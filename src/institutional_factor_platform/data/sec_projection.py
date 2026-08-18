"""Fail-closed annual projection from issuer-level SEC facts to listing fundamentals."""

from collections import defaultdict
from dataclasses import dataclass
from datetime import date, datetime
from math import isfinite

from institutional_factor_platform.data.domain import IssuerId, SecurityId
from institutional_factor_platform.data.sec_concepts import (
    ACCEPTED_SEC_FORMS,
    ANNUAL_SEC_FORMS,
    SEC_XBRL_CONCEPT_REGISTRY,
    SecConceptRule,
    SecFieldMethod,
)
from institutional_factor_platform.data.security_master import IssuerListingMappingStore
from institutional_factor_platform.exceptions import DataQualityError, SecurityMappingError

_INSTANT_FIELDS = frozenset({"book_equity", "shareholder_equity", "total_assets"})
_FLOW_FIELDS = frozenset(
    {
        "net_income",
        "operating_cash_flow",
        "dividends",
        "gross_profit",
        "operating_income",
        "revenue",
        "interest_expense",
        "capex",
    }
)


@dataclass(frozen=True, slots=True)
class _Observation:
    security_id: SecurityId
    period_end: date
    available_at: datetime
    values: dict[str, float]


def project_annual_sec_fundamentals(
    records: tuple[dict[str, object], ...], mapping_store: IssuerListingMappingStore
) -> tuple[dict[str, object], ...]:
    """Project annual standard-taxonomy facts without guessing missing fields or identities."""
    grouped: dict[tuple[str, str], list[dict[str, object]]] = defaultdict(list)
    for row in records:
        if (
            str(row.get("taxonomy")) == "us-gaap"
            and str(row.get("unit")) == "USD"
            and str(row.get("form")) in ANNUAL_SEC_FORMS
        ):
            grouped[(str(row.get("issuer_id")), str(row.get("accession_number")))].append(row)

    observations: list[_Observation] = []
    for (issuer_value, accession), filing_rows in sorted(grouped.items()):
        if not issuer_value or not accession or not filing_rows:
            continue
        period_ends = {row.get("period_end") for row in filing_rows}
        valid_ends = {value for value in period_ends if isinstance(value, date)}
        if not valid_ends:
            continue
        period_end = max(valid_ends)
        current = [row for row in filing_rows if row.get("period_end") == period_end]
        filing_dates = {row.get("filing_date") for row in current}
        availability = {row.get("availability_timestamp") for row in current}
        if len(filing_dates) != 1 or len(availability) != 1:
            raise DataQualityError(f"SEC filing identity conflicts within accession {accession}.")
        filing_date = next(iter(filing_dates))
        available_at = next(iter(availability))
        if not isinstance(filing_date, date) or not isinstance(available_at, datetime):
            raise DataQualityError(f"SEC filing timing is invalid for accession {accession}.")

        values: dict[str, float] = {}
        for field in sorted(_INSTANT_FIELDS | _FLOW_FIELDS):
            rule = SEC_XBRL_CONCEPT_REGISTRY[field]
            selected = _select_direct_value(rule, current, period_end, field in _FLOW_FIELDS)
            if selected is not None:
                values[field] = selected
        _derive_same_filing(values, current, period_end)
        if not values:
            continue
        for security_id in mapping_store.resolve_all(IssuerId(issuer_value), filing_date):
            observations.append(_Observation(security_id, period_end, available_at, values))

    return _materialize_with_lags(observations)


def project_sec_shares_outstanding(
    records: tuple[dict[str, object], ...], mapping_store: IssuerListingMappingStore
) -> tuple[dict[str, object], ...]:
    """Project filed issuer shares only when exactly one listing can receive them."""
    eligible = [
        row
        for row in records
        if row.get("taxonomy") == "dei"
        and row.get("concept") == "EntityCommonStockSharesOutstanding"
        and row.get("unit") == "shares"
        and row.get("form") in ACCEPTED_SEC_FORMS
    ]
    grouped: dict[tuple[str, str, date, datetime], list[dict[str, object]]] = defaultdict(list)
    for row in eligible:
        issuer_value = str(row.get("issuer_id", ""))
        accession = str(row.get("accession_number", ""))
        period_end = row.get("period_end")
        available_at = row.get("availability_timestamp")
        filing_date = row.get("filing_date")
        if (
            not issuer_value
            or not accession
            or not isinstance(period_end, date)
            or not isinstance(filing_date, date)
            or not isinstance(available_at, datetime)
            or available_at.tzinfo is None
        ):
            raise DataQualityError(
                "SEC shares fact lacks complete filing and availability identity."
            )
        grouped[(issuer_value, accession, period_end, available_at)].append(row)

    output: list[dict[str, object]] = []
    for (issuer_value, accession, period_end, available_at), rows in sorted(
        grouped.items(), key=lambda item: item[0]
    ):
        filing_dates = {row.get("filing_date") for row in rows}
        if len(filing_dates) != 1:
            raise DataQualityError(
                f"SEC shares filing date conflicts within accession {accession}."
            )
        filing_date = next(iter(filing_dates))
        assert isinstance(filing_date, date)
        values = {_positive_shares(row.get("value"), accession) for row in rows}
        if len(values) != 1:
            raise DataQualityError(f"Conflicting SEC shares values within accession {accession}.")
        try:
            security_id = mapping_store.resolve(IssuerId(issuer_value), filing_date)
        except SecurityMappingError as exc:
            raise DataQualityError(
                "SEC issuer shares cannot be allocated without exactly one authenticated listing."
            ) from exc
        output.append(
            {
                "security_id": security_id.value,
                "period_end": period_end,
                "available_at": available_at,
                "shares_outstanding": next(iter(values)),
                "unit": "shares",
                "accession_number": accession,
                "form": str(rows[0]["form"]),
            }
        )
    return tuple(
        sorted(
            output,
            key=lambda row: (
                str(row["security_id"]),
                row["available_at"],
                str(row["accession_number"]),
            ),
        )
    )


def attach_point_in_time_shares(
    market_rows: tuple[dict[str, object], ...],
    share_observations: tuple[dict[str, object], ...],
) -> tuple[dict[str, object], ...]:
    """Carry forward only the latest share count available by each market-row timestamp."""
    histories: dict[str, list[tuple[datetime, float]]] = defaultdict(list)
    identities: dict[tuple[str, datetime], float] = {}
    for row in share_observations:
        security_id = str(row.get("security_id", ""))
        available_at = row.get("available_at")
        if (
            not security_id
            or not isinstance(available_at, datetime)
            or available_at.tzinfo is None
            or row.get("unit") != "shares"
        ):
            raise DataQualityError("Share observation lacks exact identity, timing, or unit.")
        shares = _positive_shares(row.get("shares_outstanding"), str(row.get("accession_number")))
        key = (security_id, available_at)
        prior = identities.get(key)
        if prior is not None and prior != shares:
            raise DataQualityError("Conflicting share observations have the same availability.")
        identities[key] = shares
    for (security_id, available_at), shares in identities.items():
        histories[security_id].append((available_at, shares))
    for history in histories.values():
        history.sort(key=lambda item: item[0])

    output: list[dict[str, object]] = []
    for row in market_rows:
        security_id = str(row.get("security_id", ""))
        available_at = row.get("available_at")
        if not security_id or not isinstance(available_at, datetime) or available_at.tzinfo is None:
            raise DataQualityError("Market row lacks exact identity or aware availability.")
        if row.get("shares_outstanding") is not None:
            raise DataQualityError("Market row already carries a non-null share count.")
        eligible = [item for item in histories.get(security_id, ()) if item[0] <= available_at]
        effective_shares = eligible[-1][1] if eligible else None
        output.append({**row, "shares_outstanding": effective_shares})
    return tuple(output)


def _select_direct_value(
    rule: SecConceptRule,
    rows: list[dict[str, object]],
    period_end: date,
    flow: bool,
) -> float | None:
    if rule.method is not SecFieldMethod.DIRECT:
        return None
    for concept in rule.primary_concepts + rule.fallback_concepts:
        candidates = [
            row
            for row in rows
            if row.get("concept") == concept
            and row.get("period_end") == period_end
            and _cadence_is_eligible(row.get("period_start"), period_end, flow)
        ]
        if not candidates:
            continue
        values = {_numeric_value(row, concept) for row in candidates}
        if len(values) != 1:
            raise DataQualityError(f"Conflicting SEC values for {rule.field}:{concept}.")
        return next(iter(values))
    return None


def _cadence_is_eligible(start: object, end: date, flow: bool) -> bool:
    if not flow:
        return start is None
    return isinstance(start, date) and 300 <= (end - start).days <= 400


def _derive_same_filing(
    values: dict[str, float], rows: list[dict[str, object]], period_end: date
) -> None:
    if {"net_income", "operating_cash_flow"} <= values.keys():
        values["total_accruals"] = values["net_income"] - values["operating_cash_flow"]
    current_assets = _component_value(rows, "AssetsCurrent", period_end)
    current_liabilities = _component_value(rows, "LiabilitiesCurrent", period_end)
    if current_assets is not None and current_liabilities is not None:
        values["working_capital"] = current_assets - current_liabilities
    for current_concept, noncurrent_concept in (
        ("LongTermDebtCurrent", "LongTermDebtNoncurrent"),
        (
            "LongTermDebtAndFinanceLeaseObligationsCurrent",
            "LongTermDebtAndFinanceLeaseObligationsNoncurrent",
        ),
    ):
        current_debt = _component_value(rows, current_concept, period_end)
        noncurrent_debt = _component_value(rows, noncurrent_concept, period_end)
        if current_debt is not None and noncurrent_debt is not None:
            values["total_debt"] = current_debt + noncurrent_debt
            break


def _component_value(rows: list[dict[str, object]], concept: str, period_end: date) -> float | None:
    values = {
        _numeric_value(row, concept)
        for row in rows
        if row.get("concept") == concept
        and row.get("period_end") == period_end
        and row.get("period_start") is None
    }
    if len(values) > 1:
        raise DataQualityError(f"Conflicting SEC component values for {concept}.")
    return next(iter(values)) if values else None


def _numeric_value(row: dict[str, object], concept: str) -> float:
    value = row.get("value")
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise DataQualityError(f"SEC value is non-numeric for {concept}.")
    return float(value)


def _positive_shares(value: object, accession: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise DataQualityError(f"SEC shares value is non-numeric for accession {accession}.")
    shares = float(value)
    if not isfinite(shares) or shares <= 0:
        raise DataQualityError(f"SEC shares value is not positive for accession {accession}.")
    return shares


def _materialize_with_lags(
    observations: list[_Observation],
) -> tuple[dict[str, object], ...]:
    history: dict[SecurityId, dict[str, dict[date, list[tuple[datetime, float]]]]] = defaultdict(
        lambda: defaultdict(lambda: defaultdict(list))
    )
    output: list[dict[str, object]] = []
    seen: set[tuple[str, datetime, str]] = set()
    for observation in sorted(
        observations,
        key=lambda item: (item.available_at, item.period_end, item.security_id.value),
    ):
        values = dict(observation.values)
        for current_field, prior_field in (
            ("total_assets", "prior_total_assets"),
            ("capex", "prior_capex"),
            ("working_capital", "prior_working_capital"),
        ):
            prior = _latest_prior(
                history[observation.security_id][current_field],
                observation.period_end,
                observation.available_at,
            )
            if prior is not None:
                values[prior_field] = prior
        if "total_assets" in values and "prior_total_assets" in values:
            values["average_assets"] = (values["total_assets"] + values["prior_total_assets"]) / 2.0

        for field, value in sorted(values.items()):
            key = (observation.security_id.value, observation.available_at, field)
            if key in seen:
                raise DataQualityError(
                    "SEC projection collides at listing/availability/field identity."
                )
            seen.add(key)
            output.append(
                {
                    "security_id": observation.security_id.value,
                    "period_end": observation.period_end,
                    "available_at": observation.available_at,
                    "field": field,
                    "value": value,
                    "unit": "USD",
                }
            )
        for field in ("total_assets", "capex", "working_capital"):
            if field in observation.values:
                history[observation.security_id][field][observation.period_end].append(
                    (observation.available_at, observation.values[field])
                )
    return tuple(
        sorted(
            output,
            key=lambda row: (
                str(row["security_id"]),
                row["available_at"],
                str(row["field"]),
            ),
        )
    )


def _latest_prior(
    history: dict[date, list[tuple[datetime, float]]],
    period_end: date,
    available_at: datetime,
) -> float | None:
    prior_ends = [value for value in history if value < period_end]
    if not prior_ends:
        return None
    prior_end = max(prior_ends)
    eligible = [item for item in history[prior_end] if item[0] <= available_at]
    return max(eligible, key=lambda item: item[0])[1] if eligible else None
