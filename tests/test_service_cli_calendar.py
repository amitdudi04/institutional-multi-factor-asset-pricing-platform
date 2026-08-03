import hashlib
import json
from datetime import UTC, date, datetime
from pathlib import Path

import pytest

import institutional_factor_platform.cli as cli_module
from institutional_factor_platform.cli import build_parser, main
from institutional_factor_platform.data.calendar import USEquityCalendar
from institutional_factor_platform.data.config import PathSettings, Phase1Config, load_phase1_config
from institutional_factor_platform.data.contracts import DAILY_MARKET, MACRO_OBSERVATIONS, SEC_FACTS
from institutional_factor_platform.data.domain import (
    DataArtifact,
    DatasetStatus,
    DataSource,
    DateRange,
    RetrievalRequest,
    ValidationResult,
    ValidationSeverity,
)
from institutional_factor_platform.data.manifests import PromotionManifest
from institutional_factor_platform.data.services import DataIngestionService
from institutional_factor_platform.data.sources.base import SourceAdapter
from institutional_factor_platform.data.storage import DuckDBCatalog, sha256_file
from institutional_factor_platform.data.validation import ValidationReport
from institutional_factor_platform.exceptions import (
    DataQualityError,
    ManifestError,
    PartialRetrievalError,
    RetrievalError,
)


class SyntheticMacroAdapter(SourceAdapter[bytes]):
    source = DataSource.OWNER_SUPPLIED

    def retrieve(self, request: RetrievalRequest) -> bytes:
        return b"synthetic software fixture only"

    def standardize(
        self, payload: bytes, request: RetrievalRequest
    ) -> tuple[dict[str, object], ...]:
        assert payload.startswith(b"synthetic")
        return (
            {
                "series_id": "SYNTHETIC_TEST_SERIES",
                "observation_date": date(2024, 1, 2),
                "value": 1.0,
                "source_unit": "test unit",
                "frequency": "daily",
                "seasonal_adjustment": None,
                "source": "owner_supplied",
                "retrieval_timestamp": datetime(2024, 1, 3, tzinfo=UTC),
                "availability_timestamp": None,
                "missing_value": False,
                "schema_version": "1.0.0",
            },
        )


class InvalidSyntheticSecAdapter(SourceAdapter[bytes]):
    source = DataSource.SEC_EDGAR

    def retrieve(self, request: RetrievalRequest) -> bytes:
        return b"synthetic invalid SEC software fixture"

    def standardize(
        self, payload: bytes, request: RetrievalRequest
    ) -> tuple[dict[str, object], ...]:
        return (
            {
                "security_id": "sec_synthetic",
                "ticker": "SYNTH",
                "cik": "0000000001",
                "entity_name": "Synthetic Test Issuer",
                "taxonomy": "us-gaap",
                "concept": "SyntheticConcept",
                "label": None,
                "description": None,
                "unit": "USD",
                "value": 1.0,
                "fiscal_year": 2024,
                "fiscal_period": "FY",
                "period_start": date(2024, 1, 1),
                "period_end": date(2024, 12, 31),
                "filing_date": date(2024, 1, 1),
                "form": "10-K/A",
                "accession_number": "synthetic-accession",
                "frame": None,
                "source": "sec_edgar",
                "retrieval_timestamp": datetime(2025, 1, 2, tzinfo=UTC),
                "availability_timestamp": datetime(2024, 1, 1, 23, 59, tzinfo=UTC),
                "availability_quality": "INFERRED_DATE_LEVEL",
                "schema_version": "2.0.0",
            },
        )


class FailedRetrievalAdapter(SyntheticMacroAdapter):
    def retrieve(self, request: RetrievalRequest) -> bytes:
        raise RetrievalError("synthetic provider failure")


class PartialStandardizationAdapter(SyntheticMacroAdapter):
    def standardize(
        self, payload: bytes, request: RetrievalRequest
    ) -> tuple[dict[str, object], ...]:
        raise PartialRetrievalError("synthetic partial provider result")


class SyntheticMarketAdapter(SourceAdapter[bytes]):
    source = DataSource.YAHOO_FINANCE

    def retrieve(self, request: RetrievalRequest) -> bytes:
        return b"synthetic market software fixture"

    def standardize(
        self, payload: bytes, request: RetrievalRequest
    ) -> tuple[dict[str, object], ...]:
        return tuple(
            {
                "security_id": "sec_synthetic",
                "ticker": "SYNTH",
                "trading_date": value,
                "open": 10.0,
                "high": 11.0,
                "low": 9.0,
                "close": 10.0,
                "adjusted_close": 10.0,
                "volume": 100,
                "dividend": 0.0,
                "split_factor": 0.0,
                "currency": "USD",
                "source": "yahoo_finance",
                "retrieval_timestamp": datetime(2024, 1, 4, tzinfo=UTC),
                "schema_version": "1.0.0",
            }
            for value in (date(2024, 1, 2), date(2024, 1, 3))
        )


def _temp_config(tmp_path: Path) -> Phase1Config:
    config = load_phase1_config()
    paths = PathSettings(
        raw=Path("data/raw"),
        interim=Path("data/interim"),
        processed=Path("data/processed"),
        manifests=Path("data/manifests"),
        quarantine=Path("data/quarantine"),
        data_quality=Path("outputs/data_quality"),
        metadata=Path("outputs/metadata"),
        logs=Path("logs"),
        duckdb=Path("data/processed/catalog.duckdb"),
    )
    return config.model_copy(update={"paths": paths})


def test_end_to_end_offline_ingestion(tmp_path: Path) -> None:
    service = DataIngestionService(_temp_config(tmp_path), root=tmp_path)
    manifest = service.ingest(
        SyntheticMacroAdapter(),
        RetrievalRequest(DataSource.OWNER_SUPPLIED, "synthetic_macro"),
        MACRO_OBSERVATIONS,
        "txt",
        "text/plain",
    )
    assert manifest.validation_status is DatasetStatus.PASS
    assert manifest.promotion_state == "ELIGIBLE"
    assert service.catalog.list_datasets(research_ready_only=True)[0][0] == manifest.dataset_id
    assert len(service.catalog.list_datasets()) == 1
    assert list((tmp_path / "data/raw").rglob("*.txt"))
    assert list((tmp_path / "data/processed").rglob("*.parquet"))
    assert list((tmp_path / "data/manifests").rglob("run.json"))
    assert list((tmp_path / "outputs/data_quality").rglob("validation.md"))
    assert list((tmp_path / "data/manifests").rglob("lineage.json"))
    assert list((tmp_path / "data/manifests").rglob("promotion.json"))
    assert list((tmp_path / "data/manifests").rglob("run-started.json"))
    rebuilt = DuckDBCatalog.rebuild_from_manifests(
        tmp_path / "rebuilt.duckdb", tmp_path / "data/manifests", tmp_path
    )
    assert rebuilt.list_datasets(research_ready_only=True)[0][0] == manifest.dataset_id


def test_invalid_sec_temporal_data_is_quarantined_and_not_visible(tmp_path: Path) -> None:
    service = DataIngestionService(_temp_config(tmp_path), root=tmp_path)
    with pytest.raises(DataQualityError, match="quarantined"):
        service.ingest(
            InvalidSyntheticSecAdapter(),
            RetrievalRequest(DataSource.SEC_EDGAR, "1"),
            SEC_FACTS,
            "json",
            "application/json",
        )
    assert service.catalog.list_datasets(research_ready_only=True) == []
    assert list((tmp_path / "data/raw").rglob("*.json"))
    assert list((tmp_path / "data/quarantine").rglob("quarantine.json"))
    run = json.loads(next((tmp_path / "data/manifests").rglob("run.json")).read_text())
    assert run["status"] == "FAILED" and run["errors"]


def test_failure_after_catalog_promotion_is_compensated(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    service = DataIngestionService(_temp_config(tmp_path), root=tmp_path)
    original = PromotionManifest.write_immutable

    def fail_promotion_manifest(self: PromotionManifest, path: Path) -> None:
        if path.name == "promotion.json":
            raise ManifestError("synthetic post-promotion failure")
        original(self, path)

    monkeypatch.setattr(PromotionManifest, "write_immutable", fail_promotion_manifest)
    with pytest.raises(ManifestError, match="post-promotion"):
        service.ingest(
            SyntheticMacroAdapter(),
            RetrievalRequest(DataSource.OWNER_SUPPLIED, "synthetic_macro"),
            MACRO_OBSERVATIONS,
            "txt",
            "text/plain",
        )
    assert service.catalog.list_datasets(research_ready_only=True) == []
    assert list((tmp_path / "data/raw").rglob("*.txt"))


def test_existing_raw_artifact_reprocesses_idempotently_without_retrieval(tmp_path: Path) -> None:
    service = DataIngestionService(_temp_config(tmp_path), root=tmp_path)
    request = RetrievalRequest(DataSource.OWNER_SUPPLIED, "synthetic_macro")
    first = service.ingest(
        SyntheticMacroAdapter(), request, MACRO_OBSERVATIONS, "txt", "text/plain"
    )
    raw_path = next((tmp_path / "data/raw").rglob("*.txt"))
    artifact = DataArtifact(
        raw_path,
        sha256_file(raw_path),
        raw_path.stat().st_size,
        "text/plain",
        DataSource.OWNER_SUPPLIED,
        datetime(2024, 1, 3, tzinfo=UTC),
    )

    class NoRetrieveAdapter(SyntheticMacroAdapter):
        def retrieve(self, request: RetrievalRequest) -> bytes:
            raise AssertionError("reprocessing must not retrieve")

    second = service.reprocess(NoRetrieveAdapter(), artifact, request, MACRO_OBSERVATIONS)
    assert second.dataset_id == first.dataset_id
    assert len(service.catalog.list_datasets(research_ready_only=True)) == 1
    wrong_source = artifact.__class__(
        artifact.path,
        artifact.checksum,
        artifact.byte_size,
        artifact.media_type,
        DataSource.FRED,
        artifact.retrieval_timestamp,
    )
    with pytest.raises(DataQualityError, match="source"):
        service.reprocess(NoRetrieveAdapter(), wrong_source, request, MACRO_OBSERVATIONS)


@pytest.mark.parametrize(
    ("adapter", "expected_status"),
    [(FailedRetrievalAdapter(), "FAILED"), (PartialStandardizationAdapter(), "PARTIAL")],
)
def test_failed_and_partial_sources_remain_manifested(
    tmp_path: Path, adapter: SourceAdapter[bytes], expected_status: str
) -> None:
    service = DataIngestionService(_temp_config(tmp_path), root=tmp_path)
    with pytest.raises((RetrievalError, PartialRetrievalError)):
        service.ingest(
            adapter,
            RetrievalRequest(DataSource.OWNER_SUPPLIED, "synthetic_macro"),
            MACRO_OBSERVATIONS,
            "txt",
            "text/plain",
        )
    source = json.loads(next((tmp_path / "data/manifests").rglob("source.json")).read_text())
    assert source["response_status"] == expected_status
    assert source["partial_failures"]
    run = json.loads(next((tmp_path / "data/manifests").rglob("run.json")).read_text())
    assert run["status"] == "FAILED"


def test_market_ingestion_applies_exchange_calendar_coverage(tmp_path: Path) -> None:
    service = DataIngestionService(_temp_config(tmp_path), root=tmp_path)
    manifest = service.ingest(
        SyntheticMarketAdapter(),
        RetrievalRequest(
            DataSource.YAHOO_FINANCE,
            "daily_market",
            DateRange(date(2024, 1, 1), date(2024, 1, 3)),
            ("SYNTH",),
            {"listing_periods": {"sec_synthetic": {"start": "2024-01-02", "end": "2024-01-03"}}},
        ),
        DAILY_MARKET,
        "csv",
        "text/csv",
    )
    assert manifest.validation_status is DatasetStatus.PASS
    assert manifest.unit_metadata["currency"] == "USD"
    assert manifest.date_start == "2024-01-02"


def test_calendar_uses_sessions_not_weekdays() -> None:
    calendar = USEquityCalendar()
    sessions = calendar.sessions(date(2024, 1, 1), date(2024, 1, 3))
    assert date(2024, 1, 1) not in sessions
    assert sessions == (date(2024, 1, 2), date(2024, 1, 3))
    assert calendar.missing_sessions({date(2024, 1, 2)}, date(2024, 1, 1), date(2024, 1, 3)) == (
        date(2024, 1, 3),
    )


def test_quality_report_writes_json_and_markdown(tmp_path: Path) -> None:
    report = ValidationReport(
        "synthetic",
        "owner_supplied",
        "run",
        "1.0.0",
        1,
        None,
        None,
        None,
        "2024-01-01",
        "2024-01-01",
        (ValidationResult("test", ValidationSeverity.WARNING, "Synthetic warning"),),
        DatasetStatus.PASS_WITH_WARNINGS,
    )
    json_path, md_path = tmp_path / "report.json", tmp_path / "report.md"
    report.write(json_path, md_path)
    assert json.loads(json_path.read_text(encoding="utf-8"))["final_status"] == "PASS_WITH_WARNINGS"
    assert "Synthetic warning" in md_path.read_text(encoding="utf-8")


def test_cli_validate_config_and_errors(
    tmp_path: Path, capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    config = _temp_config(tmp_path)
    monkeypatch.setattr(cli_module, "load_phase1_config", lambda _: config)
    monkeypatch.setattr(
        cli_module, "DataIngestionService", lambda value: DataIngestionService(value, root=tmp_path)
    )
    assert main(["validate-config"]) == 0
    assert len(capsys.readouterr().out.strip()) == 64
    assert main(["inspect-manifest", "missing.json"]) == 2
    assert "error:" in capsys.readouterr().err
    assert main(["init-storage"]) == 0
    assert (tmp_path / "data/processed/catalog.duckdb").is_file()
    assert main(["list-datasets"]) == 0
    assert main(["list-datasets", "--research-ready"]) == 0
    assert main(["validate-catalog"]) == 0
    assert "catalog integrity verified" in capsys.readouterr().out
    raw = tmp_path / "raw.txt"
    raw.write_bytes(b"synthetic raw")
    checksum = hashlib.sha256(raw.read_bytes()).hexdigest()
    assert main(["verify-raw", str(raw), checksum]) == 0
    assert "checksum verified" in capsys.readouterr().out
    assert main(["verify-standardized", str(raw), checksum]) == 0
    assert "standardized checksum verified" in capsys.readouterr().out
    assert main(["verify-standardized", str(raw), "0" * 64]) == 2
    assert "error:" in capsys.readouterr().err
    assert "inspect-lineage" in build_parser().format_help()
    invalid = tmp_path / "invalid.json"
    invalid.write_text("{}", encoding="utf-8")
    assert main(["inspect-lineage", str(invalid)]) == 2
    assert main(["inspect-dataset-manifest", str(invalid)]) == 2
    capsys.readouterr()
    fred_raw = tmp_path / "fred-audit.csv"
    fred_raw.write_bytes(b"DATE,DGS3MO\n2024-01-02,5.40\n")
    fred_hash = sha256_file(fred_raw)
    assert (
        main(
            [
                "reprocess-raw",
                "fred",
                "DGS3MO",
                "macro_observations",
                str(fred_raw),
                fred_hash,
                "--media-type",
                "text/csv",
            ]
        )
        == 0
    )
    assert "macro_observations-" in capsys.readouterr().out
    lineage_path = next((tmp_path / "data/manifests").rglob("lineage.json"))
    manifest_path = next((tmp_path / "data/manifests").rglob("dataset.json"))
    assert main(["inspect-lineage", str(lineage_path)]) == 0
    assert main(["inspect-dataset-manifest", str(manifest_path)]) == 0
