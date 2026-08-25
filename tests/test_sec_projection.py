from datetime import UTC, date, datetime
from pathlib import Path

import pytest

from institutional_factor_platform.data.domain import (
    IssuerId,
    IssuerListingMapping,
    MappingEvidence,
    MappingStatus,
    SecurityId,
)
from institutional_factor_platform.data.sec_projection import (
    attach_point_in_time_shares,
    legacy_sec_shares_facts,
    project_annual_sec_fundamentals,
    project_sec_shares_outstanding,
)
from institutional_factor_platform.data.security_master import IssuerListingMappingStore
from institutional_factor_platform.exceptions import DataQualityError


def _mapping(tmp_path: Path) -> tuple[IssuerListingMappingStore, IssuerId, tuple[SecurityId, ...]]:
    issuer = IssuerId.from_cik("1")
    securities = (SecurityId.assign(), SecurityId.assign())
    store = IssuerListingMappingStore(tmp_path / "issuer-listings.json")
    store.persist(
        tuple(
            IssuerListingMapping(
                issuer,
                security,
                date(2020, 1, 1),
                None,
                MappingStatus.RESOLVED,
                MappingEvidence.OWNER_CONFIRMED,
                "synthetic filing-cover and listing evidence",
                datetime(2024, 1, 1, tzinfo=UTC),
            )
            for security in securities
        )
    )
    return store, issuer, securities


def _fact(
    issuer: IssuerId,
    *,
    concept: str,
    value: float,
    year: int,
    instant: bool,
) -> dict[str, object]:
    return {
        "issuer_id": issuer.value,
        "taxonomy": "us-gaap",
        "concept": concept,
        "unit": "USD",
        "value": value,
        "fiscal_period": "FY",
        "period_start": None if instant else date(year, 1, 1),
        "period_end": date(year, 12, 31),
        "filing_date": date(year + 1, 2, 1),
        "form": "10-K",
        "accession_number": f"accession-{year}",
        "availability_timestamp": datetime(year + 1, 2, 1, 23, 59, tzinfo=UTC),
    }


def test_annual_projection_preserves_share_classes_and_derives_without_lookahead(
    tmp_path: Path,
) -> None:
    store, issuer, securities = _mapping(tmp_path)
    records: list[dict[str, object]] = []
    for year, scale in ((2022, 1.0), (2023, 2.0)):
        records.extend(
            [
                _fact(issuer, concept="Assets", value=100.0 * scale, year=year, instant=True),
                _fact(
                    issuer,
                    concept="StockholdersEquity",
                    value=40.0 * scale,
                    year=year,
                    instant=True,
                ),
                _fact(issuer, concept="AssetsCurrent", value=50.0 * scale, year=year, instant=True),
                _fact(
                    issuer,
                    concept="LiabilitiesCurrent",
                    value=20.0 * scale,
                    year=year,
                    instant=True,
                ),
                _fact(
                    issuer, concept="NetIncomeLoss", value=10.0 * scale, year=year, instant=False
                ),
                _fact(
                    issuer,
                    concept="NetCashProvidedByUsedInOperatingActivities",
                    value=8.0 * scale,
                    year=year,
                    instant=False,
                ),
                _fact(
                    issuer,
                    concept="PaymentsToAcquirePropertyPlantAndEquipment",
                    value=5.0 * scale,
                    year=year,
                    instant=False,
                ),
            ]
        )
    projected = project_annual_sec_fundamentals(tuple(records), store)
    assert {row["security_id"] for row in projected} == {item.value for item in securities}
    latest = [row for row in projected if row["period_end"] == date(2023, 12, 31)]
    by_security = {
        security.value: {
            row["field"]: row["value"] for row in latest if row["security_id"] == security.value
        }
        for security in securities
    }
    for values in by_security.values():
        assert values["working_capital"] == 60.0
        assert values["total_accruals"] == 4.0
        assert values["prior_total_assets"] == 100.0
        assert values["average_assets"] == 150.0
        assert values["prior_capex"] == 5.0
        assert "net_equity_issuance" not in values


def test_annual_projection_rejects_conflicting_standard_facts(tmp_path: Path) -> None:
    store, issuer, _ = _mapping(tmp_path)
    first = _fact(issuer, concept="Assets", value=100.0, year=2023, instant=True)
    second = {**first, "value": 101.0}
    with pytest.raises(DataQualityError, match="Conflicting SEC values"):
        project_annual_sec_fundamentals((first, second), store)


def test_sec_shares_projection_requires_one_listing_and_preserves_restatements(
    tmp_path: Path,
) -> None:
    issuer = IssuerId.from_cik("1")
    security = SecurityId.assign()
    store = IssuerListingMappingStore(tmp_path / "single-listing.json")
    store.persist(
        (
            IssuerListingMapping(
                issuer,
                security,
                date(2020, 1, 1),
                None,
                MappingStatus.RESOLVED,
                MappingEvidence.SEC_FILING,
                "synthetic exact filing-cover evidence",
                datetime(2024, 1, 1, tzinfo=UTC),
            ),
        )
    )
    base: dict[str, object] = {
        "issuer_id": issuer.value,
        "taxonomy": "dei",
        "concept": "EntityCommonStockSharesOutstanding",
        "dimensions_json": "{}",
        "unit": "shares",
        "value": 100.0,
        "period_end": date(2023, 1, 31),
        "filing_date": date(2023, 2, 1),
        "form": "10-K",
        "accession_number": "accession-original",
        "availability_timestamp": datetime(2023, 2, 1, 23, 59, tzinfo=UTC),
    }
    amendment = {
        **base,
        "value": 101.0,
        "filing_date": date(2023, 3, 1),
        "form": "10-K/A",
        "accession_number": "accession-amendment",
        "availability_timestamp": datetime(2023, 3, 1, 23, 59, tzinfo=UTC),
    }
    comparative = {**base, "period_end": date(2022, 1, 31), "value": 80.0}
    projected = project_sec_shares_outstanding((base, dict(base), comparative, amendment), store)
    assert [row["shares_outstanding"] for row in projected] == [100.0, 101.0]
    assert {row["security_id"] for row in projected} == {security.value}
    assert all(row["unit"] == "shares" for row in projected)

    ambiguous, _, _ = _mapping(tmp_path)
    with pytest.raises(DataQualityError, match="exactly one authenticated listing"):
        project_sec_shares_outstanding((base,), ambiguous)


def test_sec_shares_projection_rejects_conflicts_and_invalid_values(tmp_path: Path) -> None:
    store, issuer, _ = _mapping(tmp_path)
    base: dict[str, object] = {
        "issuer_id": issuer.value,
        "taxonomy": "dei",
        "concept": "EntityCommonStockSharesOutstanding",
        "unit": "shares",
        "value": 100.0,
        "period_end": date(2023, 1, 31),
        "filing_date": date(2023, 2, 1),
        "form": "10-K",
        "accession_number": "accession",
        "availability_timestamp": datetime(2023, 2, 1, 23, 59, tzinfo=UTC),
    }
    with pytest.raises(DataQualityError, match="Conflicting SEC shares"):
        project_sec_shares_outstanding((base, {**base, "value": 101.0}), store)
    with pytest.raises(DataQualityError, match="not positive"):
        project_sec_shares_outstanding(({**base, "value": 0.0},), store)
    with pytest.raises(DataQualityError, match="non-numeric"):
        project_sec_shares_outstanding(({**base, "value": "100"},), store)
    with pytest.raises(DataQualityError, match="complete filing"):
        project_sec_shares_outstanding(({**base, "accession_number": ""},), store)
    with pytest.raises(DataQualityError, match="filing date conflicts"):
        project_sec_shares_outstanding((base, {**base, "filing_date": date(2023, 2, 2)}), store)
    assert project_sec_shares_outstanding(({**base, "taxonomy": "us-gaap"},), store) == ()


def test_point_in_time_share_join_never_uses_future_observations() -> None:
    first = datetime(2023, 2, 1, 23, 59, tzinfo=UTC)
    second = datetime(2023, 3, 1, 23, 59, tzinfo=UTC)
    observations = (
        {
            "security_id": "security-1",
            "available_at": first,
            "shares_outstanding": 100.0,
            "unit": "shares",
            "accession_number": "first",
        },
        {
            "security_id": "security-1",
            "available_at": second,
            "shares_outstanding": 90.0,
            "unit": "shares",
            "accession_number": "second",
        },
    )
    market = (
        {"security_id": "security-1", "available_at": first.replace(hour=12)},
        {"security_id": "security-1", "available_at": first},
        {"security_id": "security-1", "available_at": second},
        {"security_id": "security-2", "available_at": second},
    )
    joined = attach_point_in_time_shares(market, observations)
    assert [row["shares_outstanding"] for row in joined] == [None, 100.0, 90.0, None]


def test_point_in_time_share_join_rejects_ambiguous_or_malformed_evidence() -> None:
    timestamp = datetime(2023, 2, 1, 23, 59, tzinfo=UTC)
    base = {
        "security_id": "security-1",
        "available_at": timestamp,
        "shares_outstanding": 100.0,
        "unit": "shares",
        "accession_number": "first",
    }
    with pytest.raises(DataQualityError, match="same availability"):
        attach_point_in_time_shares((), (base, {**base, "shares_outstanding": 101.0}))
    with pytest.raises(DataQualityError, match="identity, timing, or unit"):
        attach_point_in_time_shares((), ({**base, "unit": "USD"},))
    with pytest.raises(DataQualityError, match="Market row"):
        attach_point_in_time_shares(
            ({"security_id": "security-1", "available_at": timestamp.replace(tzinfo=None)},),
            (base,),
        )
    with pytest.raises(DataQualityError, match="already carries"):
        attach_point_in_time_shares(
            (
                {
                    "security_id": "security-1",
                    "available_at": timestamp,
                    "shares_outstanding": 99.0,
                },
            ),
            (base,),
        )


def test_legacy_sec_shares_translate_only_exact_positive_share_units() -> None:
    row: dict[str, object] = {
        "issuer_id": "issuer-example",
        "concept": "EntityCommonStockSharesOutstanding",
        "dimensions_json": "{}",
        "unit_measure": "xbrli:shares",
        "value": "1000000",
        "context_instant": date(2012, 10, 19),
        "filing_date": date(2012, 10, 31),
        "form": "10-K",
        "accession_number": "accession",
        "availability_timestamp": datetime(2012, 10, 31, 23, 59, tzinfo=UTC),
    }
    translated = legacy_sec_shares_facts((row, {**row, "concept": "EntityPublicFloat"}))
    assert translated[0]["value"] == 1_000_000.0
    assert translated[0]["period_end"] == date(2012, 10, 19)
    with pytest.raises(DataQualityError, match="invalid unit"):
        legacy_sec_shares_facts(({**row, "unit_measure": "iso4217:USD"},))
    with pytest.raises(DataQualityError, match="non-numeric"):
        legacy_sec_shares_facts(({**row, "value": "unknown"},))
    with pytest.raises(DataQualityError, match="positive and finite"):
        legacy_sec_shares_facts(({**row, "value": "0"},))
    assert legacy_sec_shares_facts(({**row, "dimensions_json": '{"axis":"member"}'},)) == ()
