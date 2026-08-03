"""Deterministic reusable and source-specific data validation."""

import json
import math
from collections import Counter
from collections.abc import Iterable
from dataclasses import asdict, dataclass
from datetime import date, datetime
from pathlib import Path
from typing import Any

import pyarrow as pa

from institutional_factor_platform.data.contracts import TableContract
from institutional_factor_platform.data.domain import (
    DatasetStatus,
    ValidationResult,
    ValidationSeverity,
)


@dataclass(frozen=True, slots=True)
class ValidationReport:
    dataset_id: str
    source: str
    run_id: str
    schema_version: str
    row_count: int
    entity_count: int | None
    requested_start: str | None
    requested_end: str | None
    observed_start: str | None
    observed_end: str | None
    results: tuple[ValidationResult, ...]
    final_status: DatasetStatus
    quarantine_path: str | None = None

    def write(self, json_path: Path, markdown_path: Path) -> None:
        payload = asdict(self)
        json_path.parent.mkdir(parents=True, exist_ok=True)
        json_path.write_text(
            json.dumps(payload, default=str, sort_keys=True, indent=2) + "\n", encoding="utf-8"
        )
        lines = [
            f"# Data Quality Report: {self.dataset_id}",
            "",
            f"- Source: `{self.source}`",
            f"- Run: `{self.run_id}`",
            f"- Status: **{self.final_status.value}**",
            f"- Rows: {self.row_count}",
            "",
            "## Findings",
            "",
        ]
        lines.extend(
            f"- **{item.severity.value}** `{item.rule}`: {item.message}" for item in self.results
        )
        markdown_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def status_from_results(results: Iterable[ValidationResult]) -> DatasetStatus:
    severities = {result.severity for result in results}
    if ValidationSeverity.CRITICAL in severities:
        return DatasetStatus.QUARANTINED
    if ValidationSeverity.ERROR in severities:
        return DatasetStatus.FAIL
    if ValidationSeverity.WARNING in severities:
        return DatasetStatus.PASS_WITH_WARNINGS
    return DatasetStatus.PASS


def validate_table(table: pa.Table, contract: TableContract) -> tuple[ValidationResult, ...]:
    results: list[ValidationResult] = []
    try:
        contract.validate_schema(table)
    except Exception as exc:
        return (ValidationResult("schema", ValidationSeverity.CRITICAL, str(exc)),)
    if table.num_rows == 0:
        results.append(
            ValidationResult("non_empty", ValidationSeverity.CRITICAL, "Dataset is empty.")
        )
    rows = table.select(list(contract.primary_key)).to_pylist()
    keys = [tuple(row[field] for field in contract.primary_key) for row in rows]
    duplicates = [key for key, count in Counter(keys).items() if count > 1]
    if duplicates:
        results.append(
            ValidationResult(
                "primary_key_unique",
                ValidationSeverity.CRITICAL,
                f"Duplicate keys: {len(duplicates)}",
            )
        )
    for field in contract.schema:
        if not field.nullable and table[field.name].null_count:
            results.append(
                ValidationResult(
                    "required_not_null",
                    ValidationSeverity.CRITICAL,
                    f"Required field {field.name} contains {table[field.name].null_count} nulls.",
                    field.name,
                )
            )
    return tuple(results)


def validate_daily_market(
    records: list[dict[str, Any]],
    *,
    stale_sessions: int = 5,
    extreme_return_threshold: float = 0.5,
) -> tuple[ValidationResult, ...]:
    results: list[ValidationResult] = []
    seen: set[tuple[str, date]] = set()
    previous: dict[str, tuple[date, float]] = {}
    stale_counts: Counter[str] = Counter()
    for index, row in enumerate(records):
        trading_date = row.get("trading_date")
        if not isinstance(trading_date, date):
            results.append(
                ValidationResult(
                    "trading_date", ValidationSeverity.CRITICAL, "Invalid trading date.", row=index
                )
            )
            continue
        key = (str(row.get("security_id")), trading_date)
        if key in seen:
            results.append(
                ValidationResult(
                    "unique_date", ValidationSeverity.CRITICAL, f"Duplicate {key}", row=index
                )
            )
        seen.add(key)
        values = [row.get(name) for name in ("open", "high", "low", "close")]
        numeric = [float(value) for value in values if value is not None]
        if numeric and any(not math.isfinite(value) or value <= 0 for value in numeric):
            results.append(
                ValidationResult(
                    "positive_prices", ValidationSeverity.CRITICAL, "Invalid price.", row=index
                )
            )
        high, low, open_, close = row.get("high"), row.get("low"), row.get("open"), row.get("close")
        if high is not None and low is not None and float(high) < float(low):
            results.append(
                ValidationResult(
                    "high_low", ValidationSeverity.CRITICAL, "High is below low.", row=index
                )
            )
        complete_ohlc = all(value is not None for value in (high, low, open_, close))
        if complete_ohlc:
            high_value, low_value = _required_float(high), _required_float(low)
            open_value, close_value = _required_float(open_), _required_float(close)
        if complete_ohlc and not (
            low_value <= open_value <= high_value and low_value <= close_value <= high_value
        ):
            results.append(
                ValidationResult(
                    "ohlc_consistency",
                    ValidationSeverity.ERROR,
                    "Open/close outside range.",
                    row=index,
                )
            )
        if row.get("volume") is not None and int(row["volume"]) < 0:
            results.append(
                ValidationResult(
                    "volume", ValidationSeverity.CRITICAL, "Negative volume.", row=index
                )
            )
        ticker = str(row.get("ticker"))
        current = (trading_date, float(close)) if close is not None else None
        if current and ticker in previous:
            prior_date, prior_close = previous[ticker]
            if current[0] < prior_date:
                results.append(
                    ValidationResult(
                        "sorted_dates", ValidationSeverity.ERROR, "Dates not sorted.", row=index
                    )
                )
            if current[1] == prior_close:
                stale_counts[ticker] += 1
            simple_return = current[1] / prior_close - 1 if prior_close else math.inf
            if abs(simple_return) > extreme_return_threshold:
                results.append(
                    ValidationResult(
                        "extreme_return",
                        ValidationSeverity.WARNING,
                        f"Unadjusted close return {simple_return:.2%} requires review.",
                        row=index,
                    )
                )
        if current:
            previous[ticker] = current
    if any(count >= stale_sessions for count in stale_counts.values()):
        results.append(
            ValidationResult(
                "stale_price", ValidationSeverity.WARNING, "Repeated closes require review."
            )
        )
    return tuple(results)


def validate_macro(records: list[dict[str, Any]]) -> tuple[ValidationResult, ...]:
    results: list[ValidationResult] = []
    for index, row in enumerate(records):
        missing = bool(row.get("missing_value"))
        value = row.get("value")
        if missing == (value is not None):
            results.append(
                ValidationResult(
                    "explicit_missingness",
                    ValidationSeverity.CRITICAL,
                    "is_missing must be true exactly when value is null.",
                    row=index,
                )
            )
    return tuple(results)


def validate_french_factors(records: list[dict[str, Any]]) -> tuple[ValidationResult, ...]:
    results: list[ValidationResult] = []
    for index, row in enumerate(records):
        value = row.get("factor_value")
        if value is not None and not math.isfinite(float(value)):
            results.append(
                ValidationResult(
                    "finite_factor_value",
                    ValidationSeverity.CRITICAL,
                    "Factor value is not finite.",
                    row=index,
                )
            )
    return tuple(results)


def validate_sec_facts(records: list[dict[str, Any]]) -> tuple[ValidationResult, ...]:
    results: list[ValidationResult] = []
    for index, row in enumerate(records):
        period_end = row.get("period_end")
        filing_date = row.get("filing_date")
        availability = row.get("availability_timestamp")
        if (
            not isinstance(period_end, date)
            or not isinstance(filing_date, date)
            or not isinstance(availability, datetime)
        ):
            results.append(
                ValidationResult(
                    "sec_temporal_types",
                    ValidationSeverity.CRITICAL,
                    "SEC temporal fields are invalid.",
                    row=index,
                )
            )
            continue
        results.extend(validate_temporal_order(period_end, filing_date, availability))
    return tuple(results)


def _required_float(value: Any) -> float:
    if value is None:
        raise ValueError("Required numeric value is missing.")
    return float(value)


def validate_temporal_order(
    period_end: date, filing_date: date, availability: datetime
) -> tuple[ValidationResult, ...]:
    results: list[ValidationResult] = []
    if filing_date < period_end:
        results.append(
            ValidationResult(
                "filing_after_period", ValidationSeverity.CRITICAL, "Filing precedes period end."
            )
        )
    if availability.date() < filing_date:
        results.append(
            ValidationResult(
                "availability_after_filing",
                ValidationSeverity.CRITICAL,
                "Availability precedes filing.",
            )
        )
    return tuple(results)
