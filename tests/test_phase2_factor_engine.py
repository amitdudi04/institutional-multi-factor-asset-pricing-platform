"""Phase 2 factor definitions, temporal controls, and immutable publication tests."""

import json
from datetime import UTC, date, datetime, timedelta
from pathlib import Path

import pandas as pd
import pytest
from pydantic import ValidationError

from institutional_factor_platform.data.access import VerifiedDatasetHandle
from institutional_factor_platform.data.domain import DatasetStatus
from institutional_factor_platform.data.storage import sha256_file
from institutional_factor_platform.exceptions import (
    ConfigurationError,
    DataQualityError,
    EvidenceIntegrityError,
    TemporalIntegrityError,
)
from institutional_factor_platform.factors import service as factor_service_module
from institutional_factor_platform.factors.config import FactorConfig, load_factor_config
from institutional_factor_platform.factors.contracts import MARKET_REQUIRED_UNITS
from institutional_factor_platform.factors.definitions import FACTOR_DEFINITIONS
from institutional_factor_platform.factors.portfolio import validate_factor_portfolios
from institutional_factor_platform.factors.preprocessing import normalize, winsorize
from institutional_factor_platform.factors.service import FactorResearchService
from institutional_factor_platform.factors.storage import authenticate_factor_publication
from institutional_factor_platform.factors.temporal import (
    point_in_time_panel,
    validate_fundamental_input,
    validate_market_input,
)
from institutional_factor_platform.factors.validation import validate_factor_output

FIELDS = (
    "book_equity",
    "net_income",
    "operating_cash_flow",
    "dividends",
    "shareholder_equity",
    "total_assets",
    "gross_profit",
    "operating_income",
    "revenue",
    "average_assets",
    "total_accruals",
    "total_debt",
    "interest_expense",
    "prior_total_assets",
    "capex",
    "prior_capex",
    "net_equity_issuance",
    "working_capital",
    "prior_working_capital",
)


def _config() -> FactorConfig:
    base = load_factor_config()
    return base.model_copy(
        update={
            "windows": base.windows.model_copy(
                update={
                    "short": 2,
                    "medium": 3,
                    "half_year": 4,
                    "one_year": 5,
                    "two_year": 6,
                    "minimum_observations": 2,
                }
            )
        }
    )


def _parent(tmp_path: Path, dataset_id: str) -> VerifiedDatasetHandle:
    artifact = tmp_path / f"{dataset_id}.parquet"
    artifact.write_bytes(dataset_id.encode())
    return VerifiedDatasetHandle(
        dataset_id=dataset_id,
        artifact_path=artifact,
        checksum=sha256_file(artifact),
        schema_version="1.0.0",
        unit_metadata={},
        configuration_hash="a" * 64,
        git_commit="deadbeef",
        validation_status=DatasetStatus.PASS,
        mapping_status="RESOLVED",
        mapping_evidence_id="mapping:1",
        lifecycle_state="FINALIZED",
        lineage_id=f"lineage:{dataset_id}",
        promotion_id=f"promotion:{dataset_id}",
        run_id=f"run:{dataset_id}",
        temporal_policy="1.0.0",
        limitations=(),
    )


def _inputs() -> tuple[pd.DataFrame, pd.DataFrame, dict[str, str]]:
    market_rows: list[dict[str, object]] = []
    start = date(2020, 1, 2)
    securities = ("sec_" + "1" * 32, "sec_" + "2" * 32, "sec_" + "3" * 32)
    for security_number, security_id in enumerate(securities, start=1):
        for offset in range(8):
            current = start + timedelta(days=offset)
            market_rows.append(
                {
                    "security_id": security_id,
                    "date": current,
                    "available_at": datetime.combine(current, datetime.min.time(), tzinfo=UTC),
                    "eligible": not (security_number == 3 and offset == 0),
                    "eligibility_available_at": datetime.combine(
                        current, datetime.min.time(), tzinfo=UTC
                    ),
                    "sector": f"sector-{security_number % 2}",
                    "industry": f"industry-{security_number}",
                    "classification_available_at": datetime.combine(
                        current, datetime.min.time(), tzinfo=UTC
                    ),
                    "return": ((offset % 3) - 1) * 0.005 + security_number * 0.001,
                    "price": 20.0 + 10 * security_number + offset,
                    "high": 21.0 + 10 * security_number + offset,
                    "low": 19.0 + 10 * security_number + offset,
                    "volume": float(1000 * security_number + offset),
                    "shares_outstanding": float(1_000_000 * security_number),
                    "exchange": "XNYS",
                    "market_return": ((offset % 4) - 1) * 0.003,
                    "risk_free": 0.0001,
                    "benchmark_return": ((offset % 4) - 1) * 0.0025,
                    "source_dataset_id": "market-parent",
                }
            )
    fundamental_rows: list[dict[str, object]] = []
    for security_number, security_id in enumerate(securities, start=1):
        for field_number, field_name in enumerate(FIELDS, start=1):
            fundamental_rows.append(
                {
                    "security_id": security_id,
                    "period_end": date(2019, 9, 30),
                    "available_at": datetime(2020, 1, 1, tzinfo=UTC),
                    "field": field_name,
                    "value": float(100 + field_number + security_number),
                    "unit": "USD",
                    "source_dataset_id": "fundamental-parent",
                }
            )
    fundamentals = pd.DataFrame(fundamental_rows)
    return pd.DataFrame(market_rows), fundamentals, {field: "USD" for field in FIELDS}


def test_configuration_is_strict_and_reproducible(tmp_path: Path) -> None:
    config = load_factor_config()
    assert config.canonical_hash() == config.canonical_hash()
    snapshot = tmp_path / "snapshot.json"
    config.write_snapshot(snapshot)
    assert snapshot.is_file()
    with pytest.raises(ValidationError):
        config.windows.model_copy(update={"short": 10, "medium": 2}).__class__.model_validate(
            {**config.windows.model_dump(), "short": 10, "medium": 2}
        )
    broken = tmp_path / "broken.yaml"
    broken.write_text("unknown: true\n", encoding="utf-8")
    with pytest.raises(ConfigurationError):
        load_factor_config(broken)


@pytest.mark.parametrize(
    "method", ["none", "winsorized", "robust_zscore", "zscore", "minmax", "rank", "percentile"]
)
def test_preprocessing_methods_preserve_missing(method: str) -> None:
    values = pd.Series([1.0, 2.0, 100.0, None])
    clipped = winsorize(values, 0.1, 0.9)
    transformed = normalize(clipped, method, 1)
    assert pd.isna(transformed.iloc[-1])
    assert clipped.iloc[2] < 100.0


def test_temporal_contract_blocks_leakage_and_bad_lineage() -> None:
    market, fundamentals, _ = _inputs()
    parents = {"market-parent", "fundamental-parent"}
    validated_market = validate_market_input(market, parents)
    validated_fundamentals = validate_fundamental_input(fundamentals, parents)
    panel = point_in_time_panel(validated_market, validated_fundamentals)
    assert (pd.to_datetime(panel["available_at"], utc=True) <= panel["computation_cutoff"]).all()

    future = market.copy()
    future.loc[0, "eligibility_available_at"] = datetime(2030, 1, 1, tzinfo=UTC)
    with pytest.raises(TemporalIntegrityError):
        validate_market_input(future, parents)
    unauthenticated = fundamentals.copy()
    unauthenticated.loc[0, "source_dataset_id"] = "forged"
    with pytest.raises(DataQualityError):
        validate_fundamental_input(unauthenticated, parents)


def test_full_catalog_publishes_authenticates_and_is_reproducible(tmp_path: Path) -> None:
    market, fundamentals, fundamental_units = _inputs()
    parents = (_parent(tmp_path, "market-parent"), _parent(tmp_path, "fundamental-parent"))
    service = FactorResearchService(_config(), tmp_path)
    first = service.compute_and_publish(
        parents,
        market,
        fundamentals,
        market_units=MARKET_REQUIRED_UNITS,
        fundamental_units=fundamental_units,
    )
    second = service.compute_and_publish(
        parents,
        market,
        fundamentals,
        market_units=MARKET_REQUIRED_UNITS,
        fundamental_units=fundamental_units,
    )
    assert first.publication_id == second.publication_id
    manifest = authenticate_factor_publication(first.publication_path, tmp_path)
    assert set(manifest.factor_ids) == {definition.factor_id for definition in FACTOR_DEFINITIONS}
    assert manifest.security_count == 3
    table = service.repository.read_table(first.publication_id)
    assert table.num_rows == first.row_count
    portfolios = service.repository.read_portfolios(first.publication_id).to_pandas()
    assert len(portfolios) == manifest.portfolio_row_count
    assert (portfolios["date"] > portfolios["formation_date"]).all()
    assert (
        portfolios["active_return"]
        == portfolios["value_weighted_return"] - portfolios["benchmark_return"]
    ).all()
    assert service.repository.list_authenticated() == (first.publication_id,)

    for relative_path in (
        manifest.configuration_snapshot_path,
        manifest.validation_report_path,
        manifest.lineage_path,
        manifest.portfolio_artifact_path,
    ):
        evidence_path = tmp_path / relative_path
        original = evidence_path.read_bytes()
        evidence_path.write_bytes(original + b"tampered")
        with pytest.raises(EvidenceIntegrityError):
            service.repository.authenticate(first.publication_id)
        evidence_path.write_bytes(original)

    publication_value = json.loads(first.publication_path.read_text(encoding="utf-8"))
    publication_value["manifest_hash"] = "0" * 64
    first.publication_path.write_text(json.dumps(publication_value), encoding="utf-8")
    with pytest.raises(EvidenceIntegrityError):
        service.repository.authenticate(first.publication_id)
    publication_value["manifest_hash"] = manifest.content_hash()
    first.publication_path.write_text(json.dumps(publication_value), encoding="utf-8")

    artifact = tmp_path / manifest.artifact_path
    artifact.write_bytes(artifact.read_bytes() + b"tampered")
    with pytest.raises(EvidenceIntegrityError):
        service.repository.read_table(first.publication_id)
    assert service.repository.list_authenticated() == ()


def test_publication_rejects_forged_parent_and_unit_contract(tmp_path: Path) -> None:
    market, fundamentals, units = _inputs()
    valid = _parent(tmp_path, "market-parent")
    forged = _parent(tmp_path, "fundamental-parent")
    forged.artifact_path.write_bytes(b"changed")
    service = FactorResearchService(_config(), tmp_path)
    with pytest.raises(EvidenceIntegrityError):
        service.compute_and_publish(
            (valid, forged),
            market,
            fundamentals,
            market_units=MARKET_REQUIRED_UNITS,
            fundamental_units=units,
        )
    with pytest.raises(DataQualityError):
        service.compute_and_publish(
            (valid, _parent(tmp_path, "fundamental-parent")),
            market,
            fundamentals,
            market_units={**MARKET_REQUIRED_UNITS, "return_basis": "price_return"},
            fundamental_units=units,
        )


def test_crash_before_activation_is_not_discoverable_and_retry_succeeds(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    market, fundamentals, units = _inputs()
    parents = (_parent(tmp_path, "market-parent"), _parent(tmp_path, "fundamental-parent"))
    service = FactorResearchService(_config(), tmp_path)

    def crash(*_args: object) -> None:
        raise RuntimeError("injected pre-activation crash")

    original = factor_service_module._activate_publication
    monkeypatch.setattr(factor_service_module, "_activate_publication", crash)
    with pytest.raises(RuntimeError, match="injected"):
        service.compute_and_publish(
            parents,
            market,
            fundamentals,
            market_units=MARKET_REQUIRED_UNITS,
            fundamental_units=units,
        )
    assert service.repository.list_authenticated() == ()
    monkeypatch.setattr(factor_service_module, "_activate_publication", original)
    result = service.compute_and_publish(
        parents,
        market,
        fundamentals,
        market_units=MARKET_REQUIRED_UNITS,
        fundamental_units=units,
    )
    assert service.repository.list_authenticated() == (result.publication_id,)


def test_factor_output_validator_rejects_invalid_values() -> None:
    frame = pd.DataFrame(
        {
            "security_id": ["sec_" + "1" * 32],
            "date": [date(2020, 1, 2)],
            "factor_id": ["market_cap"],
            "raw_value": [-1.0],
            "winsorized_value": [-1.0],
            "normalized_value": [0.0],
            "normalization_method": ["zscore"],
            "available_at": [datetime(2020, 1, 2, tzinfo=UTC)],
            "factor_version": ["1.0.0"],
        }
    )
    with pytest.raises(DataQualityError):
        validate_factor_output(frame, "factor-invalid")

    with pytest.raises(DataQualityError):
        validate_factor_output(frame.drop(columns="raw_value"), "factor-invalid")
    with pytest.raises(DataQualityError):
        validate_factor_output(frame.iloc[0:0], "factor-invalid")
    with pytest.raises(DataQualityError):
        validate_factor_output(pd.concat([frame, frame]), "factor-invalid")
    undefined = frame.copy()
    undefined["factor_id"] = "invented"
    with pytest.raises(DataQualityError):
        validate_factor_output(undefined, "factor-invalid")
    future = frame.copy()
    future["available_at"] = datetime(2030, 1, 1, tzinfo=UTC)
    with pytest.raises(TemporalIntegrityError):
        validate_factor_output(future, "factor-invalid")
    nonfinite = frame.copy()
    nonfinite["raw_value"] = float("inf")
    with pytest.raises(DataQualityError):
        validate_factor_output(nonfinite, "factor-invalid")
    fabricated = frame.copy()
    fabricated["raw_value"] = None
    with pytest.raises(DataQualityError):
        validate_factor_output(fabricated, "factor-invalid")
    indicator = frame.copy()
    indicator["factor_id"] = "size_small"
    indicator[["raw_value", "winsorized_value"]] = 2.0
    with pytest.raises(DataQualityError):
        validate_factor_output(indicator, "factor-invalid")


def test_portfolio_validator_rejects_temporal_and_numeric_defects() -> None:
    valid = pd.DataFrame(
        {
            "formation_date": [date(2020, 1, 1)],
            "date": [date(2020, 1, 2)],
            "factor_id": ["book_to_market"],
            "quantile": [1],
            "security_count": [1],
            "value_weighted_return": [0.01],
            "benchmark_return": [0.005],
            "active_return": [0.005],
            "available_at": [datetime(2020, 1, 2, tzinfo=UTC)],
            "factor_version": ["1.0.0"],
        }
    )
    validate_factor_portfolios(valid)
    with pytest.raises(DataQualityError):
        validate_factor_portfolios(valid.iloc[0:0])
    same_day = valid.copy()
    same_day["date"] = same_day["formation_date"]
    with pytest.raises(TemporalIntegrityError):
        validate_factor_portfolios(same_day)
    early = valid.copy()
    early["available_at"] = datetime(2019, 12, 31, tzinfo=UTC)
    with pytest.raises(TemporalIntegrityError):
        validate_factor_portfolios(early)
    invalid_group = valid.copy()
    invalid_group["security_count"] = 0
    with pytest.raises(DataQualityError):
        validate_factor_portfolios(invalid_group)
    invalid_number = valid.copy()
    invalid_number["active_return"] = float("inf")
    with pytest.raises(DataQualityError):
        validate_factor_portfolios(invalid_number)
    impossible = valid.copy()
    impossible["value_weighted_return"] = -1.0
    with pytest.raises(DataQualityError):
        validate_factor_portfolios(impossible)


def test_input_contract_adversarial_failures() -> None:
    market, fundamentals, _ = _inputs()
    parents = {"market-parent", "fundamental-parent"}

    with pytest.raises(DataQualityError):
        validate_market_input(market.drop(columns="price"), parents)
    with pytest.raises(DataQualityError):
        validate_market_input(market.iloc[0:0], parents)
    duplicate = pd.concat([market, market.iloc[[0]]], ignore_index=True)
    with pytest.raises(DataQualityError):
        validate_market_input(duplicate, parents)
    invalid_id = market.copy()
    invalid_id.loc[0, "security_id"] = "ticker:AAPL"
    with pytest.raises(DataQualityError):
        validate_market_input(invalid_id, parents)
    bad_return = market.copy()
    bad_return.loc[0, "return"] = -1.0
    with pytest.raises(DataQualityError):
        validate_market_input(bad_return, parents)
    negative_price = market.copy()
    negative_price.loc[0, "price"] = -1.0
    with pytest.raises(DataQualityError):
        validate_market_input(negative_price, parents)
    inverted_range = market.copy()
    inverted_range.loc[0, "high"] = inverted_range.loc[0, "low"] - 1
    with pytest.raises(DataQualityError):
        validate_market_input(inverted_range, parents)

    duplicate_fundamental = pd.concat([fundamentals, fundamentals.iloc[[0]]], ignore_index=True)
    with pytest.raises(DataQualityError):
        validate_fundamental_input(duplicate_fundamental, parents)
    future_period = fundamentals.copy()
    future_period.loc[0, "period_end"] = date(2030, 1, 1)
    with pytest.raises(TemporalIntegrityError):
        validate_fundamental_input(future_period, parents)
    nonfinite = fundamentals.copy()
    nonfinite.loc[0, "value"] = float("inf")
    with pytest.raises(DataQualityError):
        validate_fundamental_input(nonfinite, parents)
    missing_unit = fundamentals.copy()
    missing_unit.loc[0, "unit"] = None
    with pytest.raises(DataQualityError):
        validate_fundamental_input(missing_unit, parents)

    with pytest.raises(DataQualityError):
        normalize(pd.Series([1.0, 2.0]), "unsupported", 1)
