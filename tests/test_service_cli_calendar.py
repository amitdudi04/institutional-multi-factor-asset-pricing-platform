import hashlib
import json
from datetime import UTC, date, datetime
from pathlib import Path

import pytest

import institutional_factor_platform.cli as cli_module
from institutional_factor_platform.cli import build_parser, main
from institutional_factor_platform.data.calendar import USEquityCalendar
from institutional_factor_platform.data.config import PathSettings, Phase1Config, load_phase1_config
from institutional_factor_platform.data.contracts import (
    DAILY_MARKET,
    MACRO_OBSERVATIONS,
    SEC_FACTS,
    SEC_INLINE_XBRL,
    SEC_SUBMISSIONS,
)
from institutional_factor_platform.data.domain import (
    DataArtifact,
    DatasetStatus,
    DataSource,
    DateRange,
    MappingEvidence,
    RetrievalRequest,
    SecurityId,
    ValidationResult,
    ValidationSeverity,
)
from institutional_factor_platform.data.manifests import PromotionManifest
from institutional_factor_platform.data.security_master import (
    SecurityMappingStore,
    mapping_from_listing,
)
from institutional_factor_platform.data.services import DataIngestionService
from institutional_factor_platform.data.sources.base import SourceAdapter
from institutional_factor_platform.data.sources.sec_edgar import SecEdgarAdapter
from institutional_factor_platform.data.sources.sec_inline_xbrl import SecInlineXbrlAdapter
from institutional_factor_platform.data.sources.sec_submissions import SecSubmissionsAdapter
from institutional_factor_platform.data.storage import (
    DuckDBCatalog,
    authenticate_dataset_evidence,
    sha256_file,
)
from institutional_factor_platform.data.validation import ValidationReport
from institutional_factor_platform.exceptions import (
    DataQualityError,
    EvidenceIntegrityError,
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


class ClockedSyntheticMacroAdapter(SyntheticMacroAdapter):
    def __init__(self, fallback: datetime) -> None:
        self.fallback = fallback

    def standardize(
        self, payload: bytes, request: RetrievalRequest
    ) -> tuple[dict[str, object], ...]:
        row = dict(super().standardize(payload, request)[0])
        row["retrieval_timestamp"] = self.retrieval_timestamp(lambda: self.fallback)
        return (row,)


def test_sec_raw_reprocessing_dispatches_by_contract(tmp_path: Path) -> None:
    config = _temp_config(tmp_path)
    retrieved = datetime(2026, 8, 18, 8, 5, 4, 841479, tzinfo=UTC)
    assert isinstance(
        cli_module._reprocessing_adapter(DataSource.SEC_EDGAR, SEC_FACTS.name, config, retrieved),
        SecEdgarAdapter,
    )
    assert isinstance(
        cli_module._reprocessing_adapter(
            DataSource.SEC_EDGAR, SEC_SUBMISSIONS.name, config, retrieved
        ),
        SecSubmissionsAdapter,
    )
    inline = cli_module._reprocessing_adapter(
        DataSource.SEC_EDGAR, SEC_INLINE_XBRL.name, config, retrieved
    )
    assert isinstance(inline, SecInlineXbrlAdapter)
    assert inline.now() == retrieved
    with pytest.raises(ValueError, match="does not support"):
        cli_module._reprocessing_adapter(
            DataSource.SEC_EDGAR, MACRO_OBSERVATIONS.name, config, retrieved
        )
    named = tmp_path / "20260818T080504841479Z_4b13dc8460e699d4.zip"
    named.write_bytes(b"raw")
    assert cli_module._raw_retrieval_timestamp(named) == retrieved


class InvalidSyntheticSecAdapter(SourceAdapter[bytes]):
    source = DataSource.SEC_EDGAR

    def retrieve(self, request: RetrievalRequest) -> bytes:
        return b"synthetic invalid SEC software fixture"

    def standardize(
        self, payload: bytes, request: RetrievalRequest
    ) -> tuple[dict[str, object], ...]:
        return (
            {
                "issuer_id": "issuer_synthetic",
                "security_id": None,
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
                "schema_version": "3.0.0",
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

    def __init__(self, mapping_store: SecurityMappingStore, security_id: SecurityId) -> None:
        self.mapping_store = mapping_store
        self.security_id = security_id

    def mapping_authority_path(self) -> Path:
        return self.mapping_store.path

    def retrieve(self, request: RetrievalRequest) -> bytes:
        return b"synthetic market software fixture"

    def standardize(
        self, payload: bytes, request: RetrievalRequest
    ) -> tuple[dict[str, object], ...]:
        return tuple(
            {
                "security_id": self.security_id.value,
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
    assert manifest.catalog_registration_state == "REGISTERED"
    assert manifest.promotion_state == "PUBLISHED"
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


def test_malformed_manifest_and_in_memory_pass_cannot_promote(tmp_path: Path) -> None:
    path = tmp_path / "manifest.json"
    path.write_text("{}", encoding="utf-8")
    catalog = DuckDBCatalog(tmp_path / "catalog.duckdb")
    with pytest.raises(EvidenceIntegrityError, match="Invalid persisted dataset manifest"):
        catalog.promote_persisted("forged", path, tmp_path)
    assert not hasattr(catalog, "promote")
    assert catalog.list_datasets(research_ready_only=True) == []


@pytest.mark.parametrize(
    ("evidence_name", "error"),
    [
        ("validation_report_path", "validation report"),
        ("lineage_path", "lineage"),
        ("configuration_snapshot_path", "configuration snapshot"),
        ("source_manifest_path", "source manifest"),
        ("parquet_path", "Parquet"),
    ],
)
def test_persisted_evidence_tampering_fails_after_restart(
    tmp_path: Path, evidence_name: str, error: str
) -> None:
    service = DataIngestionService(_temp_config(tmp_path), root=tmp_path)
    manifest = service.ingest(
        SyntheticMacroAdapter(),
        RetrievalRequest(DataSource.OWNER_SUPPLIED, "synthetic_macro"),
        MACRO_OBSERVATIONS,
        "txt",
        "text/plain",
    )
    manifest_path = next((tmp_path / "data/manifests").rglob("dataset.json"))
    evidence_path = tmp_path / Path(str(getattr(manifest, evidence_name)))
    evidence_path.unlink()
    restarted = DuckDBCatalog(service.catalog.path)
    with pytest.raises(EvidenceIntegrityError, match=error):
        authenticate_dataset_evidence(manifest.dataset_id, manifest_path, tmp_path)
    with pytest.raises(EvidenceIntegrityError, match=error):
        restarted.verify_integrity(tmp_path)


def test_substituted_manifest_identity_and_persisted_fail_are_blocked(tmp_path: Path) -> None:
    service = DataIngestionService(_temp_config(tmp_path), root=tmp_path)
    manifest = service.ingest(
        SyntheticMacroAdapter(),
        RetrievalRequest(DataSource.OWNER_SUPPLIED, "synthetic_macro"),
        MACRO_OBSERVATIONS,
        "txt",
        "text/plain",
    )
    original = next((tmp_path / "data/manifests").rglob("dataset.json"))
    substituted = tmp_path / "substituted.json"
    substituted.write_text(original.read_text(encoding="utf-8"), encoding="utf-8")
    with pytest.raises(EvidenceIntegrityError, match="dataset ID"):
        service.catalog.promote_persisted("different", substituted, tmp_path)
    value = json.loads(original.read_text(encoding="utf-8"))
    value["validation_status"] = "FAIL"
    failed = tmp_path / "failed.json"
    failed.write_text(json.dumps(value), encoding="utf-8")
    with pytest.raises(EvidenceIntegrityError, match="Invalid persisted dataset manifest"):
        service.catalog.promote_persisted(manifest.dataset_id, failed, tmp_path)


def test_authenticated_evidence_cross_checks_semantics(tmp_path: Path) -> None:
    service = DataIngestionService(_temp_config(tmp_path), root=tmp_path)
    manifest = service.ingest(
        SyntheticMacroAdapter(),
        RetrievalRequest(DataSource.OWNER_SUPPLIED, "synthetic_macro"),
        MACRO_OBSERVATIONS,
        "txt",
        "text/plain",
    )
    original_path = next((tmp_path / "data/manifests").rglob("dataset.json"))

    def variant(
        name: str,
        *,
        manifest_update: dict[str, object] | None = None,
        evidence_field: str | None = None,
        evidence_update: dict[str, object] | None = None,
        raw_evidence: str | None = None,
    ) -> Path:
        value = json.loads(original_path.read_text(encoding="utf-8"))
        if manifest_update:
            value.update(manifest_update)
        if evidence_field:
            evidence = tmp_path / Path(value[evidence_field])
            if raw_evidence is None:
                payload = json.loads(evidence.read_text(encoding="utf-8"))
                payload.update(evidence_update or {})
                content = json.dumps(payload, sort_keys=True, indent=2) + "\n"
            else:
                content = raw_evidence
            copy = tmp_path / f"{name}-evidence.json"
            copy.write_text(content, encoding="utf-8")
            value[evidence_field] = str(copy)
            value[evidence_field.replace("_path", "_checksum")] = sha256_file(copy)
            if evidence_field == "validation_report_path":
                value["validation_report_id"] = f"validation:{sha256_file(copy)}"
        path = tmp_path / f"{name}.json"
        path.write_text(json.dumps(value), encoding="utf-8")
        return path

    cases = [
        (variant("bad-git", manifest_update={"git_commit": "unavailable"}), "Git commit"),
        (
            variant("bad-report-json", evidence_field="validation_report_path", raw_evidence="{"),
            "Invalid validation report",
        ),
        (
            variant(
                "report-id",
                evidence_field="validation_report_path",
                evidence_update={"dataset_id": "different"},
            ),
            "identity",
        ),
        (
            variant(
                "report-status",
                evidence_field="validation_report_path",
                evidence_update={"final_status": "PASS_WITH_WARNINGS"},
            ),
            "Validation status",
        ),
        (
            variant(
                "report-critical",
                evidence_field="validation_report_path",
                evidence_update={
                    "results": [
                        {
                            "rule": "synthetic_blocker",
                            "severity": "CRITICAL",
                            "message": "synthetic blocking result",
                            "field": None,
                            "row": None,
                            "rule_version": "1.0.0",
                            "dataset_id": manifest.dataset_id,
                            "affected_count": 1,
                            "representative_keys": [],
                            "remediation": "reject synthetic blocker",
                            "source": "owner_supplied",
                            "timestamp": datetime(2024, 1, 3, tzinfo=UTC).isoformat(),
                        }
                    ]
                },
            ),
            "blocking findings",
        ),
        (
            variant(
                "lineage-id",
                evidence_field="lineage_path",
                evidence_update={"dataset_id": "different"},
            ),
            "Lineage identity",
        ),
        (
            variant(
                "lineage-artifacts",
                evidence_field="lineage_path",
                evidence_update={"artifacts": []},
            ),
            "incomplete",
        ),
        (
            variant(
                "parquet-size", manifest_update={"output_byte_size": manifest.output_byte_size + 1}
            ),
            "byte size",
        ),
        (
            variant("schema", manifest_update={"schema_fingerprint": "0" * 64}),
            "schema fingerprint",
        ),
        (
            variant("source-json", evidence_field="source_manifest_path", raw_evidence="{"),
            "Invalid source manifest",
        ),
    ]
    for path, message in cases:
        with pytest.raises(EvidenceIntegrityError, match=message):
            authenticate_dataset_evidence(manifest.dataset_id, path, tmp_path)

    registered_path = original_path.with_name("dataset-registered.json")
    with pytest.raises(EvidenceIntegrityError, match="PUBLISHED"):
        DuckDBCatalog(tmp_path / "unregistered.duckdb").promote_persisted(
            manifest.dataset_id, registered_path, tmp_path
        )
    with pytest.raises(EvidenceIntegrityError, match="Catalog registration"):
        DuckDBCatalog(tmp_path / "missing-registration.duckdb").promote_persisted(
            manifest.dataset_id, original_path, tmp_path
        )
    registered_value = json.loads(registered_path.read_text(encoding="utf-8"))
    registered_value["catalog_registration_state"] = "NOT_REGISTERED"
    not_registered = tmp_path / "not-registered.json"
    not_registered.write_text(json.dumps(registered_value), encoding="utf-8")
    with pytest.raises(EvidenceIntegrityError, match="REGISTERED"):
        DuckDBCatalog(tmp_path / "registration-state.duckdb").register_persisted(
            manifest.dataset_id, not_registered, tmp_path
        )
    registered_value["catalog_registration_state"] = "REGISTERED"
    registered_value["promotion_state"] = "NOT_ELIGIBLE"
    not_eligible = tmp_path / "not-eligible.json"
    not_eligible.write_text(json.dumps(registered_value), encoding="utf-8")
    with pytest.raises(EvidenceIntegrityError, match="ELIGIBLE"):
        DuckDBCatalog(tmp_path / "eligibility.duckdb").register_persisted(
            manifest.dataset_id, not_eligible, tmp_path
        )
    service.catalog.demote("not-present")
    existing_target = tmp_path / "existing.duckdb"
    existing_target.touch()
    rebuilt = DuckDBCatalog.rebuild_from_manifests(
        existing_target, tmp_path / "data/manifests", tmp_path
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
    assert list((tmp_path / "data/manifests").rglob("*demoted.json"))


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


def test_raw_reprocess_binds_original_retrieval_timestamp(tmp_path: Path) -> None:
    service = DataIngestionService(_temp_config(tmp_path), root=tmp_path)
    request = RetrievalRequest(DataSource.OWNER_SUPPLIED, "clocked_macro")
    first = service.ingest(
        ClockedSyntheticMacroAdapter(datetime(2030, 1, 1, tzinfo=UTC)),
        request,
        MACRO_OBSERVATIONS,
        "txt",
        "text/plain",
    )
    source = json.loads(next((tmp_path / "data/manifests").rglob("source.json")).read_text())
    raw_path = tmp_path / source["raw_artifact_path"]
    artifact = DataArtifact(
        raw_path,
        source["checksum"],
        source["byte_size"],
        source["media_type"],
        DataSource.OWNER_SUPPLIED,
        datetime.fromisoformat(source["retrieval_time"].replace("Z", "+00:00")),
    )
    second = service.reprocess(
        ClockedSyntheticMacroAdapter(datetime(2040, 1, 1, tzinfo=UTC)),
        artifact,
        request,
        MACRO_OBSERVATIONS,
    )
    assert second.dataset_id == first.dataset_id


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
    security_id = SecurityId.assign()
    mapping_store = SecurityMappingStore(tmp_path / "data/metadata/security-mappings.json")
    mapping_store.persist(
        (
            mapping_from_listing(
                source=DataSource.YAHOO_FINANCE,
                source_identifier="SYNTH",
                ticker="SYNTH",
                exchange="XNYS",
                mic="XNYS",
                valid_from=date(2020, 1, 1),
                valid_to=None,
                provenance="synthetic test mapping",
                retrieval_timestamp=datetime(2024, 1, 1, tzinfo=UTC),
                evidence=MappingEvidence.OWNER_CONFIRMED,
                security_id=security_id,
            ),
        )
    )
    manifest = service.ingest(
        SyntheticMarketAdapter(mapping_store, security_id),
        RetrievalRequest(
            DataSource.YAHOO_FINANCE,
            "daily_market",
            DateRange(date(2024, 1, 1), date(2024, 1, 3)),
            ("SYNTH",),
            {"listing_periods": {security_id.value: {"start": "2024-01-02", "end": "2024-01-03"}}},
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
    dataset_id = json.loads(manifest_path.read_text(encoding="utf-8"))["dataset_id"]
    assert main(["verify-publication", dataset_id, str(manifest_path)]) == 0
    assert "publication evidence verified" in capsys.readouterr().out
    assert main(["reconcile"]) == 0
    assert main(["rebuild-catalog"]) == 0
    assert "catalog.duckdb" in capsys.readouterr().out
    assert main(["verify-publication", "different", str(manifest_path)]) == 2


def test_hf_inventory_cli_confines_output_to_project(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    config = _temp_config(tmp_path)
    monkeypatch.setattr(cli_module, "load_phase1_config", lambda _: config)
    monkeypatch.setattr(
        cli_module, "DataIngestionService", lambda value: DataIngestionService(value, root=tmp_path)
    )
    monkeypatch.setattr(
        cli_module.HFDataLibraryAdapter,
        "inventory",
        lambda _: {"schema_version": "1.0.0", "records": []},
    )
    assert main(["inventory-hf", "--output", "outputs/hf-inventory.json"]) == 0
    assert (tmp_path / "outputs/hf-inventory.json").is_file()
    assert main(["inventory-hf", "--output", str(tmp_path.parent / "escape.json")]) == 2
