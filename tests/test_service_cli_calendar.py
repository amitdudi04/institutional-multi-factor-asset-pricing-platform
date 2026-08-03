import hashlib
import json
from datetime import UTC, date, datetime
from pathlib import Path

import pytest

import institutional_factor_platform.cli as cli_module
from institutional_factor_platform.cli import main
from institutional_factor_platform.data.calendar import USEquityCalendar
from institutional_factor_platform.data.config import PathSettings, Phase1Config, load_phase1_config
from institutional_factor_platform.data.contracts import MACRO_OBSERVATIONS
from institutional_factor_platform.data.domain import (
    DatasetStatus,
    DataSource,
    RetrievalRequest,
    ValidationResult,
    ValidationSeverity,
)
from institutional_factor_platform.data.services import DataIngestionService
from institutional_factor_platform.data.sources.base import SourceAdapter
from institutional_factor_platform.data.validation import ValidationReport


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
    assert manifest.duckdb_registered
    assert len(service.catalog.list_datasets()) == 1
    assert list((tmp_path / "data/raw").rglob("*.txt"))
    assert list((tmp_path / "data/processed").rglob("*.parquet"))
    assert list((tmp_path / "data/manifests").rglob("run.json"))
    assert list((tmp_path / "outputs/data_quality").rglob("validation.md"))


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
    raw = tmp_path / "raw.txt"
    raw.write_bytes(b"synthetic raw")
    checksum = hashlib.sha256(raw.read_bytes()).hexdigest()
    assert main(["verify-raw", str(raw), checksum]) == 0
    assert "checksum verified" in capsys.readouterr().out
