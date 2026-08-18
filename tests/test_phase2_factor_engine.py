"""Phase 2 factor definitions, temporal controls, and immutable publication tests."""

import json
from dataclasses import replace
from datetime import UTC, date, datetime, timedelta
from pathlib import Path

import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
import pytest
from pydantic import ValidationError

from institutional_factor_platform.data import services as data_services_module
from institutional_factor_platform.data.access import VerifiedDatasetHandle
from institutional_factor_platform.data.contracts import CONTRACTS
from institutional_factor_platform.data.domain import (
    DatasetStatus,
    DataSource,
    RetrievalRequest,
    SecurityId,
)
from institutional_factor_platform.data.security_master import (
    SecurityMappingStore,
    mapping_from_listing,
)
from institutional_factor_platform.data.sources.owner_supplied import OwnerSuppliedAdapter
from institutional_factor_platform.data.storage import sha256_file
from institutional_factor_platform.exceptions import (
    ConfigurationError,
    DataQualityError,
    EvidenceIntegrityError,
    PublicationConflictError,
    TemporalIntegrityError,
)
from institutional_factor_platform.factors import service as factor_service_module
from institutional_factor_platform.factors import storage as factor_storage_module
from institutional_factor_platform.factors.config import FactorConfig, load_factor_config
from institutional_factor_platform.factors.contracts import MARKET_REQUIRED_UNITS, MARKET_SCHEMA
from institutional_factor_platform.factors.definitions import FACTOR_DEFINITIONS
from institutional_factor_platform.factors.diagnostics import build_factor_diagnostics
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


def _parent(
    tmp_path: Path, dataset_id: str, frame: pd.DataFrame | None = None
) -> VerifiedDatasetHandle:
    artifact = tmp_path / f"{dataset_id}.parquet"
    if frame is None:
        artifact.write_bytes(dataset_id.encode())
    else:
        frame.to_parquet(artifact, index=False)
    return VerifiedDatasetHandle(
        dataset_id=dataset_id,
        artifact_path=artifact,
        checksum=sha256_file(artifact),
        schema_version="1.0.0",
        unit_metadata=(
            dict(MARKET_REQUIRED_UNITS)
            if dataset_id == "market-parent"
            else {field: "USD" for field in FIELDS}
        ),
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
            current = start + timedelta(days=offset * 15)
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
                }
            )
    fundamentals = pd.DataFrame(fundamental_rows)
    return pd.DataFrame(market_rows), fundamentals, {field: "USD" for field in FIELDS}


def test_partial_defensible_fundamentals_preserve_unestimable_factors() -> None:
    market, fundamentals, _ = _inputs()
    partial = fundamentals.loc[fundamentals["field"].eq("book_equity")].copy()
    factor_service_module._validate_units(
        dict(MARKET_REQUIRED_UNITS), partial, {"book_equity": "USD"}
    )
    panel = point_in_time_panel(market, partial)
    characteristics = factor_service_module.compute_characteristics(panel, _config())
    assert characteristics["book_to_market"].notna().any()
    assert characteristics["earnings_yield"].isna().all()

    factors = pd.DataFrame(
        {
            "security_id": ["sec_" + "1" * 32] * 2,
            "date": [date(2020, 1, 2)] * 2,
            "factor_id": ["book_to_market", "earnings_yield"],
            "raw_value": [1.0, None],
            "winsorized_value": [1.0, None],
            "normalized_value": [0.0, None],
            "score_value": [0.0, None],
        }
    )
    diagnostics = build_factor_diagnostics(
        factors,
        pd.DataFrame(
            columns=[
                "factor_id",
                "quantile",
                "active_return",
                "value_weighted_return",
            ]
        ),
        2,
    )
    statuses = {item["factor_id"]: item["status"] for item in diagnostics["estimability"]}
    assert statuses == {
        "book_to_market": "ESTIMABLE",
        "earnings_yield": "NOT ESTIMABLE FROM DEFENSIBLE INPUTS",
    }
    with pytest.raises(DataQualityError, match="outside the approved"):
        invalid = partial.copy()
        invalid["field"] = "invented"
        factor_service_module._validate_units(
            dict(MARKET_REQUIRED_UNITS), invalid, {"invented": "USD"}
        )


def test_missing_nyse_reference_marks_size_breakpoints_unestimable() -> None:
    market, fundamentals, _ = _inputs()
    market["exchange"] = "XNAS"
    panel = point_in_time_panel(market, fundamentals)

    characteristics = factor_service_module.compute_characteristics(panel, _config())

    assert characteristics[["size_small", "size_mid", "size_large"]].isna().all().all()


def test_service_rejects_insufficient_authenticated_cross_section(tmp_path: Path) -> None:
    market, fundamentals, _ = _inputs()
    market = market.loc[market["security_id"].isin(("sec_" + "1" * 32, "sec_" + "2" * 32))]
    parents = (
        _parent(tmp_path, "market-parent", market),
        _parent(tmp_path, "fundamental-parent", fundamentals),
    )

    with pytest.raises(DataQualityError, match="maximum authenticated breadth is 2"):
        FactorResearchService(_config(), tmp_path).compute_and_publish(
            parents,
            market_dataset_id="market-parent",
            fundamental_dataset_id="fundamental-parent",
        )


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
    with pytest.raises(ValidationError):
        config.publication.__class__(output_root="../escape", manifest_root="data/manifests")


def test_owner_factor_input_uses_registered_exact_contract(tmp_path: Path) -> None:
    market, _, _ = _inputs()
    source = tmp_path / "market.parquet"
    pq.write_table(pa.Table.from_pandas(market, schema=MARKET_SCHEMA, preserve_index=False), source)
    mapping_path = tmp_path / "mapping.json"
    SecurityMappingStore(mapping_path).persist(
        tuple(
            mapping_from_listing(
                source=DataSource.OWNER_SUPPLIED,
                source_identifier=f"fixture-{index}",
                ticker=f"F{index}",
                exchange="XNYS",
                mic="XNYS",
                valid_from=date(2019, 1, 1),
                valid_to=None,
                provenance="isolated software fixture",
                retrieval_timestamp=datetime(2020, 1, 1, tzinfo=UTC),
                security_id=SecurityId(security_id),
            )
            for index, security_id in enumerate(sorted(set(market["security_id"])), start=1)
        )
    )
    parameters = {
        "path": str(source),
        "schema": "factor_market_input",
        "contract_version": "1.0.0",
        "source_name": "isolated software fixture",
        "source_ownership": "test only",
        "units": MARKET_REQUIRED_UNITS,
        "date_semantics": "fixture point-in-time dates",
        "security_identifier_semantics": "fixture canonical mappings",
        "mapping_authority_path": str(mapping_path),
    }
    request = RetrievalRequest(
        DataSource.OWNER_SUPPLIED, "factor-market-fixture", parameters=parameters
    )
    adapter = OwnerSuppliedAdapter()
    rows = adapter.standardize(source.read_bytes(), request)
    assert len(rows) == len(market)
    mapping = data_services_module._authenticate_mapping_authority(
        adapter,
        rows,
        request,
        CONTRACTS["factor_market_input"],
        tmp_path,
    )
    assert mapping[0] == "RESOLVED"


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
    validated_market = validate_market_input(market, _config().plausibility)
    validated_fundamentals = validate_fundamental_input(fundamentals)
    panel = point_in_time_panel(validated_market, validated_fundamentals)
    assert (pd.to_datetime(panel["available_at"], utc=True) <= panel["computation_cutoff"]).all()

    future = market.copy()
    future.loc[0, "eligibility_available_at"] = datetime(2030, 1, 1, tzinfo=UTC)
    with pytest.raises(TemporalIntegrityError):
        validate_market_input(future, _config().plausibility)


def test_full_catalog_publishes_authenticates_and_is_reproducible(tmp_path: Path) -> None:
    market, fundamentals, _ = _inputs()
    parents = (
        _parent(tmp_path, "market-parent", market),
        _parent(tmp_path, "fundamental-parent", fundamentals),
    )
    service = FactorResearchService(_config(), tmp_path)
    first = service.compute_and_publish(
        parents,
        market_dataset_id="market-parent",
        fundamental_dataset_id="fundamental-parent",
    )
    second = service.compute_and_publish(
        parents,
        market_dataset_id="market-parent",
        fundamental_dataset_id="fundamental-parent",
    )
    assert first.publication_id == second.publication_id
    manifest = authenticate_factor_publication(first.publication_path, tmp_path)
    assert set(manifest.factor_ids) == {definition.factor_id for definition in FACTOR_DEFINITIONS}
    assert len(manifest.factor_ids) == 48
    assert manifest.security_count == 3
    table = service.repository.read_table(first.publication_id)
    assert table.num_rows == first.row_count
    factor_frame = table.to_pandas()
    size_score = factor_frame.loc[
        factor_frame["factor_id"].eq("market_cap") & factor_frame["normalized_value"].notna()
    ]
    assert (size_score["score_value"] == -size_score["normalized_value"]).all()
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
    market, fundamentals, _ = _inputs()
    valid = _parent(tmp_path, "market-parent", market)
    forged = _parent(tmp_path, "fundamental-parent", fundamentals)
    forged.artifact_path.write_bytes(b"changed")
    service = FactorResearchService(_config(), tmp_path)
    with pytest.raises(EvidenceIntegrityError):
        service.compute_and_publish(
            (valid, forged),
            market_dataset_id="market-parent",
            fundamental_dataset_id="fundamental-parent",
        )
    invalid_unit_parent = replace(
        _parent(tmp_path, "market-parent", market),
        unit_metadata={**MARKET_REQUIRED_UNITS, "return_basis": "price_return"},
    )
    with pytest.raises(DataQualityError):
        service.compute_and_publish(
            (invalid_unit_parent, _parent(tmp_path, "fundamental-parent", fundamentals)),
            market_dataset_id="market-parent",
            fundamental_dataset_id="fundamental-parent",
        )
    ineligible = market.copy()
    ineligible["eligible"] = False
    with pytest.raises(DataQualityError, match="No securities"):
        service.compute_and_publish(
            (
                _parent(tmp_path, "market-parent", ineligible),
                _parent(tmp_path, "fundamental-parent", fundamentals),
            ),
            market_dataset_id="market-parent",
            fundamental_dataset_id="fundamental-parent",
        )


def test_crash_before_activation_is_not_discoverable_and_retry_succeeds(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    market, fundamentals, _ = _inputs()
    parents = (
        _parent(tmp_path, "market-parent", market),
        _parent(tmp_path, "fundamental-parent", fundamentals),
    )
    service = FactorResearchService(_config(), tmp_path)

    def crash(*_args: object) -> None:
        raise RuntimeError("injected pre-activation crash")

    original = factor_service_module._activate_publication
    monkeypatch.setattr(factor_service_module, "_activate_publication", crash)
    with pytest.raises(RuntimeError, match="injected"):
        service.compute_and_publish(
            parents,
            market_dataset_id="market-parent",
            fundamental_dataset_id="fundamental-parent",
        )
    assert service.repository.list_authenticated() == ()
    monkeypatch.setattr(factor_service_module, "_activate_publication", original)
    result = service.compute_and_publish(
        parents,
        market_dataset_id="market-parent",
        fundamental_dataset_id="fundamental-parent",
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
            "score_value": [0.0],
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
    with pytest.raises(DataQualityError):
        validate_market_input(market.drop(columns="price"), _config().plausibility)
    with pytest.raises(DataQualityError):
        validate_market_input(market.iloc[0:0], _config().plausibility)
    duplicate = pd.concat([market, market.iloc[[0]]], ignore_index=True)
    with pytest.raises(DataQualityError):
        validate_market_input(duplicate, _config().plausibility)
    invalid_id = market.copy()
    invalid_id.loc[0, "security_id"] = "ticker:AAPL"
    with pytest.raises(DataQualityError):
        validate_market_input(invalid_id, _config().plausibility)
    bad_return = market.copy()
    bad_return.loc[0, "return"] = -1.0
    with pytest.raises(DataQualityError):
        validate_market_input(bad_return, _config().plausibility)
    implausible_rf = market.copy()
    implausible_rf.loc[0, "risk_free"] = 0.1
    with pytest.raises(DataQualityError):
        validate_market_input(implausible_rf, _config().plausibility)
    negative_price = market.copy()
    negative_price.loc[0, "price"] = -1.0
    with pytest.raises(DataQualityError):
        validate_market_input(negative_price, _config().plausibility)
    inverted_range = market.copy()
    inverted_range.loc[0, "high"] = inverted_range.loc[0, "low"] - 1
    with pytest.raises(DataQualityError):
        validate_market_input(inverted_range, _config().plausibility)

    duplicate_fundamental = pd.concat([fundamentals, fundamentals.iloc[[0]]], ignore_index=True)
    with pytest.raises(DataQualityError):
        validate_fundamental_input(duplicate_fundamental)
    future_period = fundamentals.copy()
    future_period.loc[0, "period_end"] = date(2030, 1, 1)
    with pytest.raises(TemporalIntegrityError):
        validate_fundamental_input(future_period)
    nonfinite = fundamentals.copy()
    nonfinite.loc[0, "value"] = float("inf")
    with pytest.raises(DataQualityError):
        validate_fundamental_input(nonfinite)
    missing_unit = fundamentals.copy()
    missing_unit.loc[0, "unit"] = None
    with pytest.raises(DataQualityError):
        validate_fundamental_input(missing_unit)

    with pytest.raises(DataQualityError):
        normalize(pd.Series([1.0, 2.0]), "unsupported", 1)


def test_additional_fail_closed_boundaries(tmp_path: Path) -> None:
    market, fundamentals, _ = _inputs()
    config = _config()

    for column in ("security_id", "available_at", "eligible", "sector"):
        broken = market.copy()
        if column == "eligible":
            broken[column] = broken[column].astype("object")
        broken.loc[0, column] = None
        with pytest.raises(DataQualityError):
            validate_market_input(broken, config.plausibility)
    zero = market.copy()
    zero.loc[0, "shares_outstanding"] = 0.0
    with pytest.raises(DataQualityError):
        validate_market_input(zero, config.plausibility)
    missing_period = fundamentals.copy()
    missing_period.loc[0, "period_end"] = None
    with pytest.raises(DataQualityError):
        validate_fundamental_input(missing_period)

    assert factor_service_module._authenticate_parents
    with pytest.raises(EvidenceIntegrityError):
        factor_service_module._authenticate_parents(())
    market_parent = _parent(tmp_path, "market-parent", market)
    with pytest.raises(EvidenceIntegrityError):
        factor_service_module._authenticate_parents((market_parent, market_parent))
    missing_parent = replace(market_parent, artifact_path=tmp_path / "missing.parquet")
    with pytest.raises(EvidenceIntegrityError, match="cannot be read"):
        factor_service_module._read_parent_table(missing_parent)
    with pytest.raises(EvidenceIntegrityError):
        factor_service_module._relative(tmp_path.parent / "escape", tmp_path)

    service = FactorResearchService(config, tmp_path)
    fundamental_parent = _parent(tmp_path, "fundamental-parent", fundamentals)
    with pytest.raises(EvidenceIntegrityError):
        service.compute_and_publish(
            (market_parent, fundamental_parent),
            market_dataset_id="missing-role",
            fundamental_dataset_id="fundamental-parent",
        )
    unreadable = _parent(tmp_path, "market-parent")
    with pytest.raises(EvidenceIntegrityError, match="readable Parquet"):
        service.compute_and_publish(
            (unreadable, fundamental_parent),
            market_dataset_id="market-parent",
            fundamental_dataset_id="fundamental-parent",
        )
    no_units = replace(fundamental_parent, unit_metadata={})
    with pytest.raises(DataQualityError):
        service.compute_and_publish(
            (_parent(tmp_path, "market-parent", market), no_units),
            market_dataset_id="market-parent",
            fundamental_dataset_id="fundamental-parent",
        )
    non_usd = replace(
        fundamental_parent,
        unit_metadata={field: ("EUR" if field == "book_equity" else "USD") for field in FIELDS},
    )
    with pytest.raises(DataQualityError):
        service.compute_and_publish(
            (_parent(tmp_path, "market-parent", market), non_usd),
            market_dataset_id="market-parent",
            fundamental_dataset_id="fundamental-parent",
        )
    with pytest.raises(EvidenceIntegrityError):
        service.repository.authenticate("factor-does-not-exist")
    invalid_publication = tmp_path / "invalid-publication.json"
    invalid_publication.write_text("{}", encoding="utf-8")
    with pytest.raises(EvidenceIntegrityError):
        authenticate_factor_publication(invalid_publication, tmp_path)
    with pytest.raises(EvidenceIntegrityError, match="unavailable"):
        factor_storage_module._read_manifest_parquet("missing.parquet", "0" * 64, tmp_path)
    changed = tmp_path / "changed.parquet"
    changed.write_bytes(b"not-the-bound-content")
    with pytest.raises(EvidenceIntegrityError, match="changed"):
        factor_storage_module._read_manifest_parquet("changed.parquet", "0" * 64, tmp_path)
    with pytest.raises(PublicationConflictError, match="factor table"):
        factor_storage_module.publish_factor_parquet(
            tmp_path / "wrong.parquet", pa.table({"wrong": [1]})
        )
