import io
import json
import zipfile
from datetime import UTC, date, datetime
from pathlib import Path

import httpx
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
import pytest

from institutional_factor_platform.data.calendar import USEquityCalendar
from institutional_factor_platform.data.config import load_phase1_config
from institutional_factor_platform.data.contracts import MACRO_OBSERVATIONS
from institutional_factor_platform.data.domain import (
    DataSource,
    DateRange,
    RetrievalRequest,
    ValidationResult,
    ValidationSeverity,
)
from institutional_factor_platform.data.sources.base import HttpTransport
from institutional_factor_platform.data.sources.fred import FredAdapter
from institutional_factor_platform.data.sources.french import KennethFrenchAdapter
from institutional_factor_platform.data.sources.owner_supplied import OwnerSuppliedAdapter
from institutional_factor_platform.data.sources.sec_edgar import SecEdgarAdapter
from institutional_factor_platform.data.sources.yahoo import YahooFinanceAdapter
from institutional_factor_platform.data.validation import (
    status_from_results,
    validate_daily_market,
    validate_french_factors,
    validate_macro,
    validate_market_coverage,
    validate_sec_facts,
    validate_table,
    validate_temporal_order,
)
from institutional_factor_platform.exceptions import (
    ConfigurationError,
    PartialRetrievalError,
    RateLimitError,
    RetrievalError,
    UnsupportedDatasetError,
)

NOW = datetime(2024, 1, 3, tzinfo=UTC)


def _transport(handler: httpx.MockTransport) -> HttpTransport:
    runtime = load_phase1_config().runtime.model_copy(
        update={"max_retries": 1, "backoff_seconds": 0.0, "jitter_seconds": 0.0}
    )
    return HttpTransport(runtime, httpx.Client(transport=handler), sleeper=lambda _: None)


def test_http_transport_success_retry_rate_limit_and_bad_request() -> None:
    assert (
        _transport(httpx.MockTransport(lambda _: httpx.Response(200, content=b"ok"))).get(
            "https://x"
        )
        == b"ok"
    )
    attempts = 0

    def timeout_then_success(request: httpx.Request) -> httpx.Response:
        nonlocal attempts
        attempts += 1
        if attempts == 1:
            raise httpx.ReadTimeout("synthetic timeout", request=request)
        return httpx.Response(200, content=b"recovered")

    assert _transport(httpx.MockTransport(timeout_then_success)).get("https://x") == b"recovered"
    with pytest.raises(RateLimitError):
        _transport(httpx.MockTransport(lambda _: httpx.Response(429))).get("https://x")
    with pytest.raises(RetrievalError, match="Non-retryable"):
        _transport(httpx.MockTransport(lambda _: httpx.Response(404))).get("https://x")


def test_fred_standardizes_missing_without_interpolation() -> None:
    adapter = FredAdapter(
        _transport(httpx.MockTransport(lambda _: httpx.Response(200))), now=lambda: NOW
    )
    request = RetrievalRequest(
        DataSource.FRED, "DGS3MO", DateRange(date(2024, 1, 1), date(2024, 1, 2))
    )
    records = adapter.standardize(b"DATE,DGS3MO\n2024-01-01,5.40\n2024-01-02,.\n", request)
    assert records[0]["value"] == 5.4
    assert records[1]["value"] is None and records[1]["missing_value"] is True
    with pytest.raises(RetrievalError, match="Unapproved"):
        adapter.retrieve(RetrievalRequest(DataSource.FRED, "UNAPPROVED"))
    with pytest.raises(RetrievalError, match="expected column"):
        adapter.standardize(b"DATE,OTHER\n2024-01-01,1\n", request)
    with pytest.raises(RetrievalError, match="empty"):
        adapter.standardize(b"DATE,DGS3MO\n", request)


def _french_zip() -> bytes:
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as archive:
        archive.writestr(
            "synthetic.csv",
            "Synthetic software test fixture\n"
            ",Mkt-RF,SMB,HML,RMW,CMA,RF\n"
            "20240102,1.00,2.00,3.00,4.00,5.00,0.10\n\n",
        )
    return buffer.getvalue()


def test_french_records_unit_transformation() -> None:
    adapter = KennethFrenchAdapter(
        _transport(httpx.MockTransport(lambda _: httpx.Response(200))), now=lambda: NOW
    )
    request = RetrievalRequest(DataSource.KENNETH_FRENCH, "F-F_Research_Data_5_Factors_2x3_daily")
    records = adapter.standardize(_french_zip(), request)
    assert records[0]["factor_value"] == 0.01
    assert records[0]["source_unit"] == "percent"
    assert records[0]["standardized_unit"] == "decimal_return"
    with pytest.raises(RetrievalError, match="archive"):
        adapter.standardize(b"not zip", request)
    with pytest.raises(RetrievalError, match="Unapproved"):
        adapter.retrieve(RetrievalRequest(DataSource.KENNETH_FRENCH, "unknown"))


def test_sec_requires_contact_and_preserves_filing_metadata() -> None:
    config = load_phase1_config()
    no_contact = SecEdgarAdapter(
        config.sources.sec, _transport(httpx.MockTransport(lambda _: httpx.Response(200)))
    )
    with pytest.raises(ConfigurationError):
        no_contact.retrieve(RetrievalRequest(DataSource.SEC_EDGAR, "1"))
    settings = config.sources.sec.model_copy(update={"contact_email": "owner@example.invalid"})
    adapter = SecEdgarAdapter(
        settings, _transport(httpx.MockTransport(lambda _: httpx.Response(200))), now=lambda: NOW
    )
    payload = {
        "cik": 1,
        "entityName": "Synthetic Test Issuer",
        "facts": {
            "us-gaap": {
                "SyntheticConcept": {
                    "label": "Synthetic",
                    "description": "Software test only",
                    "units": {
                        "USD": [
                            {
                                "val": 10,
                                "start": "2023-01-01",
                                "end": "2023-12-31",
                                "filed": "2024-02-01",
                                "form": "10-K",
                                "accn": "0000000001-24-000001",
                                "fy": 2023,
                                "fp": "FY",
                            }
                        ]
                    },
                }
            }
        },
    }
    records = adapter.standardize(
        json.dumps(payload).encode(), RetrievalRequest(DataSource.SEC_EDGAR, "1")
    )
    assert records[0]["filing_date"] == date(2024, 2, 1)
    assert records[0]["availability_timestamp"] >= datetime(2024, 2, 1, tzinfo=UTC)
    assert records[0]["availability_quality"] == "INFERRED_DATE_LEVEL"
    assert records[0]["schema_version"] == "2.0.0"
    with pytest.raises(RetrievalError, match="Invalid SEC JSON"):
        adapter.standardize(b"not json", RetrievalRequest(DataSource.SEC_EDGAR, "1"))
    with pytest.raises(RetrievalError, match="entity metadata"):
        adapter.standardize(b"{}", RetrievalRequest(DataSource.SEC_EDGAR, "1"))


def test_yahoo_standardizes_and_reports_partial_failure() -> None:
    index = pd.to_datetime(["2024-01-02", "2024-01-03"])
    frame = pd.DataFrame(
        {
            "Open": [10.0, 11.0],
            "High": [11.0, 12.0],
            "Low": [9.0, 10.0],
            "Close": [10.5, 11.5],
            "Adj Close": [10.5, 11.5],
            "Volume": [100, 200],
            "Dividends": [0.0, 0.0],
            "Stock Splits": [0.0, 0.0],
        },
        index=index,
    )
    adapter = YahooFinanceAdapter(download=lambda *args, **kwargs: frame, now=lambda: NOW)
    request = RetrievalRequest(
        DataSource.YAHOO_FINANCE,
        "daily_market",
        DateRange(date(2024, 1, 1), date(2024, 1, 4)),
        ("SYNTH",),
        {"security_ids": {"SYNTH": "sec_synthetic"}, "currency": "USD"},
    )
    assert len(adapter.standardize(adapter.retrieve(request), request)) == 2
    columns = pd.MultiIndex.from_product([["SYNTH"], frame.columns])
    multi = pd.DataFrame(frame.to_numpy(), index=index, columns=columns)
    partial = request.__class__(
        request.source,
        request.dataset,
        request.date_range,
        ("SYNTH", "MISSING"),
        request.parameters,
    )
    with pytest.raises(PartialRetrievalError):
        adapter.standardize(multi, partial)
    with pytest.raises(RetrievalError, match="security ID"):
        adapter.standardize(
            frame,
            request.__class__(request.source, request.dataset, request.date_range, ("SYNTH",)),
        )
    empty_adapter = YahooFinanceAdapter(download=lambda *args, **kwargs: pd.DataFrame())
    with pytest.raises(RetrievalError, match="empty"):
        empty_adapter.retrieve(request)


def test_owner_adapter_requires_explicit_contract(tmp_path: Path) -> None:
    path = tmp_path / "header-only.csv"
    path.write_text(
        ",".join(MACRO_OBSERVATIONS.schema.names) + "\n",
        encoding="utf-8",
    )
    metadata = {
        "path": str(path),
        "schema": "macro_observations",
        "contract_version": "1.0.0",
        "source_name": "owner audit fixture",
        "source_ownership": "repository owner",
        "units": {"value": "synthetic unit"},
        "date_semantics": "ISO observation date",
        "security_identifier_semantics": "not applicable",
    }
    request = RetrievalRequest(
        DataSource.OWNER_SUPPLIED,
        "owner_test",
        parameters=metadata,
    )
    adapter = OwnerSuppliedAdapter()
    assert adapter.standardize(adapter.retrieve(request), request) == ()
    with pytest.raises(UnsupportedDatasetError):
        adapter.standardize(
            path.read_bytes(),
            request.__class__(
                request.source, request.dataset, parameters={**metadata, "schema": "unknown"}
            ),
        )
    missing = request.__class__(
        request.source,
        request.dataset,
        parameters={
            **metadata,
            "path": str(tmp_path / "none.csv"),
        },
    )
    with pytest.raises(RetrievalError, match="does not exist"):
        adapter.retrieve(missing)
    json_path = tmp_path / "records.json"
    json_path.write_text('[{"series_id":"synthetic"}]', encoding="utf-8")
    json_request = request.__class__(
        request.source,
        request.dataset,
        parameters={**metadata, "path": str(json_path)},
    )
    with pytest.raises(UnsupportedDatasetError, match="exactly match"):
        adapter.standardize(adapter.retrieve(json_request), json_request)
    with pytest.raises(UnsupportedDatasetError, match="metadata is incomplete"):
        adapter.retrieve(
            RetrievalRequest(
                DataSource.OWNER_SUPPLIED,
                "owner_test",
                parameters={"path": str(path), "schema": "macro_observations"},
            )
        )
    extra = tmp_path / "extra.csv"
    extra.write_text(
        ",".join([*MACRO_OBSERVATIONS.schema.names, "unexpected"]) + "\n",
        encoding="utf-8",
    )
    extra_request = request.__class__(
        request.source, request.dataset, parameters={**metadata, "path": str(extra)}
    )
    before = extra.read_bytes()
    with pytest.raises(UnsupportedDatasetError, match="extra"):
        adapter.standardize(adapter.retrieve(extra_request), extra_request)
    assert extra.read_bytes() == before
    parquet_path = tmp_path / "valid.parquet"
    pq.write_table(pa.Table.from_pylist([], schema=MACRO_OBSERVATIONS.schema), parquet_path)
    parquet_request = request.__class__(
        request.source, request.dataset, parameters={**metadata, "path": str(parquet_path)}
    )
    assert adapter.standardize(adapter.retrieve(parquet_request), parquet_request) == ()
    corrupt = tmp_path / "corrupt.parquet"
    corrupt.write_bytes(b"not parquet")
    corrupt_request = request.__class__(
        request.source, request.dataset, parameters={**metadata, "path": str(corrupt)}
    )
    with pytest.raises(RetrievalError, match="cannot be parsed"):
        adapter.standardize(adapter.retrieve(corrupt_request), corrupt_request)
    wrong_version = request.__class__(
        request.source,
        request.dataset,
        parameters={**metadata, "contract_version": "9.0.0"},
    )
    with pytest.raises(UnsupportedDatasetError, match="unsupported"):
        adapter.retrieve(wrong_version)
    missing_units = request.__class__(
        request.source, request.dataset, parameters={**metadata, "units": {}}
    )
    with pytest.raises(UnsupportedDatasetError, match="units"):
        adapter.retrieve(missing_units)


def test_common_market_and_temporal_validation() -> None:
    records = [
        {
            "security_id": "sec",
            "ticker": "SYNTH",
            "trading_date": date(2024, 1, 2),
            "open": 11,
            "high": 10,
            "low": 9,
            "close": 12,
            "volume": -1,
        },
        {
            "security_id": "sec",
            "ticker": "SYNTH",
            "trading_date": date(2024, 1, 2),
            "open": 11,
            "high": 10,
            "low": 9,
            "close": 12,
            "volume": 1,
        },
    ]
    findings = validate_daily_market(records)
    assert {item.rule for item in findings} >= {"unique_date", "volume", "ohlc_consistency"}
    temporal = validate_temporal_order(date(2024, 2, 1), date(2024, 1, 1), NOW)
    assert status_from_results(temporal).value == "QUARANTINED"
    empty = pa.Table.from_pylist([], schema=MACRO_OBSERVATIONS.schema)
    assert status_from_results(validate_table(empty, MACRO_OBSERVATIONS)).value == "QUARANTINED"
    assert (
        status_from_results(
            (ValidationResult("warn", ValidationSeverity.WARNING, "synthetic"),)
        ).value
        == "PASS_WITH_WARNINGS"
    )


def test_additional_validation_status_and_schema_paths() -> None:
    assert status_from_results(()).value == "PASS"
    assert (
        status_from_results(
            (ValidationResult("error", ValidationSeverity.ERROR, "synthetic"),)
        ).value
        == "FAIL"
    )
    assert validate_table(pa.table({"wrong": [1]}), MACRO_OBSERVATIONS)[0].rule == "schema"
    bad_date_records = [
        {
            "security_id": "sec",
            "ticker": "SYNTH",
            "trading_date": "not-a-date",
            "open": 1,
            "high": 1,
            "low": 1,
            "close": 1,
            "volume": 1,
        }
    ]
    assert validate_daily_market(bad_date_records)[0].rule == "trading_date"
    availability_before = validate_temporal_order(
        date(2024, 1, 1), date(2024, 1, 2), datetime(2024, 1, 1, tzinfo=UTC)
    )
    assert any(item.rule == "availability_after_filing" for item in availability_before)


def test_source_specific_validation_paths() -> None:
    macro = validate_macro(
        [
            {"value": None, "missing_value": False},
            {"value": 1.0, "missing_value": True},
        ]
    )
    assert len(macro) == 2
    french = validate_french_factors([{"factor_value": float("inf")}])
    assert french[0].rule == "finite_factor_value"
    sec = validate_sec_facts(
        [
            {
                "period_end": date(2024, 2, 1),
                "filing_date": date(2024, 1, 1),
                "availability_timestamp": NOW,
                "retrieval_timestamp": NOW,
                "availability_quality": "INFERRED_DATE_LEVEL",
            },
            {"period_end": "invalid"},
        ]
    )
    assert {finding.rule for finding in sec} == {"filing_after_period", "sec_temporal_types"}


def test_market_stale_extreme_and_invalid_values() -> None:
    records = [
        {
            "security_id": "sec",
            "ticker": "SYNTH",
            "trading_date": date(2024, 1, 2 + index),
            "open": close,
            "high": close,
            "low": close,
            "close": close,
            "volume": 1,
        }
        for index, close in enumerate((1.0, 1.0, 1.0, 3.0))
    ]
    findings = validate_daily_market(records, stale_sessions=2, extreme_return_threshold=0.5)
    assert {finding.rule for finding in findings} >= {"stale_price", "extreme_return"}
    invalid = validate_daily_market(
        [
            {
                "security_id": "sec",
                "ticker": "SYNTH",
                "trading_date": date(2024, 1, 2),
                "open": -1,
                "high": 1,
                "low": 2,
                "close": 1,
                "volume": 1,
            }
        ]
    )
    assert {finding.rule for finding in invalid} >= {"positive_prices", "high_low"}


def test_market_calendar_coverage_and_listing_boundaries() -> None:
    records = [
        {"security_id": "sec", "trading_date": date(2024, 1, 2)},
        {"security_id": "sec", "trading_date": date(2024, 1, 4)},
    ]
    findings = validate_market_coverage(
        records,
        calendar=USEquityCalendar(),
        start=date(2024, 1, 1),
        end=date(2024, 1, 5),
        warning_ratio=0.9,
        critical_ratio=0.5,
        listing_periods={"sec": (date(2024, 1, 2), date(2024, 1, 4))},
    )
    coverage = next(item for item in findings if item.rule == "market_calendar_coverage")
    assert coverage.affected_count == 1
    assert coverage.representative_keys == ("2024-01-03",)
    out_of_range = validate_market_coverage(
        [{"security_id": "sec", "trading_date": date(2024, 1, 8)}],
        calendar=USEquityCalendar(),
        start=date(2024, 1, 1),
        end=date(2024, 1, 5),
        warning_ratio=0.9,
        critical_ratio=0.5,
    )
    assert any(item.rule == "market_out_of_range" for item in out_of_range)


def test_sec_temporal_availability_and_duration_rules() -> None:
    base = {
        "period_start": date(2023, 1, 1),
        "period_end": date(2023, 12, 31),
        "filing_date": date(2024, 2, 1),
        "availability_timestamp": datetime(2024, 2, 1, 23, 59, tzinfo=UTC),
        "retrieval_timestamp": datetime(2024, 2, 2, tzinfo=UTC),
        "availability_quality": "INFERRED_DATE_LEVEL",
    }
    assert validate_sec_facts([base]) == ()
    assert validate_sec_facts([{**base, "period_start": None, "form": "10-Q"}]) == ()
    availability_before = validate_sec_facts(
        [{**base, "availability_timestamp": datetime(2024, 1, 1, tzinfo=UTC)}]
    )
    assert any(item.rule == "availability_after_filing" for item in availability_before)
    retrieval_before = validate_sec_facts(
        [{**base, "retrieval_timestamp": datetime(2024, 1, 1, tzinfo=UTC)}]
    )
    assert any(item.rule == "retrieval_after_availability" for item in retrieval_before)
    reversed_period = validate_sec_facts(
        [{**base, "period_start": date(2024, 1, 1), "period_end": date(2023, 1, 1)}]
    )
    assert any(item.rule == "sec_period_order" for item in reversed_period)
