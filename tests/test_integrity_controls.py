import json
import subprocess
import sys
from datetime import UTC, date, datetime
from pathlib import Path

import pytest
from test_service_cli_calendar import SyntheticMarketAdapter, _temp_config
from test_recovery_and_lineage import _publish

from institutional_factor_platform.data.contracts import DAILY_MARKET, SEC_FACTS
from institutional_factor_platform.data.domain import (
    DataSource,
    DateRange,
    IssuerId,
    IssuerListingMapping,
    MappingEvidence,
    MappingStatus,
    RetrievalRequest,
    SecurityId,
)
from institutional_factor_platform.data.lineage import LifecycleEventStore, LifecycleState
from institutional_factor_platform.data.manifests import DatasetManifest, PromotionManifest
from institutional_factor_platform.data.security_master import (
    IssuerListingMappingStore,
    SecurityMappingStore,
    mapping_from_listing,
)
from institutional_factor_platform.data.services import DataIngestionService
from institutional_factor_platform.data.sources.base import SourceAdapter, completed_result
from institutional_factor_platform.data.storage import authenticate_dataset_evidence, sha256_file
from institutional_factor_platform.exceptions import DataQualityError, EvidenceIntegrityError


def _market_publication(root: Path) -> tuple[DataIngestionService, object, Path]:
    security_id = SecurityId.assign()
    mapping = SecurityMappingStore(root / "data/metadata/security-mappings.json")
    mapping.persist(
        (
            mapping_from_listing(
                source=DataSource.YAHOO_FINANCE,
                source_identifier="SYNTH",
                ticker="SYNTH",
                exchange="XNYS",
                mic="XNYS",
                valid_from=date(2020, 1, 1),
                valid_to=None,
                provenance="synthetic assurance mapping",
                retrieval_timestamp=datetime(2024, 1, 1, tzinfo=UTC),
                evidence=MappingEvidence.OWNER_CONFIRMED,
                security_id=security_id,
            ),
        )
    )
    service = DataIngestionService(_temp_config(root), root=root)
    manifest = service.ingest(
        SyntheticMarketAdapter(mapping, security_id),
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
    return service, manifest, mapping.path


@pytest.mark.parametrize("evidence_name", ["promotion.json", "run.json"])
def test_terminal_evidence_is_mandatory_for_supported_reads(
    tmp_path: Path, evidence_name: str
) -> None:
    service, manifest, manifest_path = _publish(tmp_path)
    manifest_path.with_name(evidence_name).unlink()
    with pytest.raises(EvidenceIntegrityError):
        service.research.get(manifest.dataset_id)  # type: ignore[attr-defined]
    assert service.catalog.list_datasets(research_ready_only=True) == []


def test_promoted_manifest_is_immutable_read_authority(tmp_path: Path) -> None:
    service, manifest, manifest_path = _publish(tmp_path)
    value = json.loads(manifest_path.read_text(encoding="utf-8"))
    value["unit_metadata"]["standardized.value"] = "shares"
    manifest_path.write_text(json.dumps(value), encoding="utf-8")
    with pytest.raises(EvidenceIntegrityError, match="promotion envelope"):
        service.research.get(manifest.dataset_id)  # type: ignore[attr-defined]


def test_manifest_mapping_evidence_contract_is_strict(tmp_path: Path) -> None:
    _, _, manifest_path = _publish(tmp_path)
    value = json.loads(manifest_path.read_text(encoding="utf-8"))
    value["mapping_status"] = "RESOLVED"
    with pytest.raises(ValueError, match="complete mapping evidence"):
        DatasetManifest.model_validate(value)
    value["mapping_status"] = "NOT_APPLICABLE"
    value["mapping_evidence_path"] = "data/metadata/unexpected.json"
    value["mapping_evidence_checksum"] = "0" * 64
    value["mapping_evidence_id"] = "mapping:unexpected"
    with pytest.raises(ValueError, match="only valid for resolved"):
        DatasetManifest.model_validate(value)
    marker = object()
    assert completed_result(marker) is marker  # type: ignore[arg-type]


def test_rewritten_manifest_and_promotion_cannot_replace_final_authority(tmp_path: Path) -> None:
    service, manifest, manifest_path = _publish(tmp_path)
    value = json.loads(manifest_path.read_text(encoding="utf-8"))
    value["unit_metadata"]["standardized.value"] = "shares"
    manifest_path.write_text(json.dumps(value), encoding="utf-8")
    changed = DatasetManifest.model_validate(value)
    promotion_path = manifest_path.with_name("promotion.json")
    promotion = PromotionManifest.model_validate_json(promotion_path.read_text())
    rewritten = promotion.model_copy(update={"dataset_manifest_hash": changed.content_hash()})
    promotion_path.write_text(rewritten.canonical_json(), encoding="utf-8")
    with pytest.raises(EvidenceIntegrityError, match="lifecycle event"):
        service.research.get(manifest.dataset_id)  # type: ignore[attr-defined]


def test_forged_validation_and_disconnected_lineage_cannot_authenticate(tmp_path: Path) -> None:
    service, manifest, manifest_path = _publish(tmp_path)
    value = json.loads(manifest_path.read_text(encoding="utf-8"))
    report = tmp_path / value["validation_report_path"]
    report.write_text(
        json.dumps(
            {
                "dataset_id": manifest.dataset_id,  # type: ignore[attr-defined]
                "run_id": manifest.run_id,  # type: ignore[attr-defined]
                "final_status": "PASS",
                "results": [],
            }
        ),
        encoding="utf-8",
    )
    value["validation_report_checksum"] = sha256_file(report)
    value["validation_report_id"] = f"validation:{sha256_file(report)}"
    manifest_path.write_text(json.dumps(value), encoding="utf-8")
    with pytest.raises(EvidenceIntegrityError, match="complete schema"):
        service.research.get(manifest.dataset_id)  # type: ignore[attr-defined]


def test_validation_result_requires_complete_typed_schema(tmp_path: Path) -> None:
    _, manifest, manifest_path = _publish(tmp_path)
    value = json.loads(manifest_path.read_text(encoding="utf-8"))
    report = tmp_path / value["validation_report_path"]
    report_value = json.loads(report.read_text(encoding="utf-8"))
    report_value["results"] = [{"severity": "INFO"}]
    report.write_text(json.dumps(report_value), encoding="utf-8")
    value["validation_report_checksum"] = sha256_file(report)
    value["validation_report_id"] = f"validation:{sha256_file(report)}"
    manifest_path.write_text(json.dumps(value), encoding="utf-8")
    with pytest.raises(EvidenceIntegrityError, match="Validation result"):
        authenticate_dataset_evidence(manifest.dataset_id, manifest_path, tmp_path)  # type: ignore[attr-defined]


def test_configuration_substitution_cannot_authenticate(tmp_path: Path) -> None:
    service, manifest, manifest_path = _publish(tmp_path)
    value = json.loads(manifest_path.read_text(encoding="utf-8"))
    snapshot = tmp_path / value["configuration_snapshot_path"]
    snapshot.write_text('{"attacker":true}\n', encoding="utf-8")
    checksum = sha256_file(snapshot)
    value["configuration_snapshot_checksum"] = checksum
    value["configuration_hash"] = checksum
    value["configuration_snapshot_id"] = f"config:{checksum}"
    manifest_path.write_text(json.dumps(value), encoding="utf-8")
    with pytest.raises(EvidenceIntegrityError):
        service.research.get(manifest.dataset_id)  # type: ignore[attr-defined]


def test_mapping_evidence_removal_revokes_market_access(tmp_path: Path) -> None:
    service, manifest, mapping_path = _market_publication(tmp_path)
    handle = service.research.get(manifest.dataset_id)  # type: ignore[attr-defined]
    assert handle.mapping_status == "RESOLVED"
    assert handle.mapping_evidence_id == f"mapping:{sha256_file(mapping_path)}"
    mapping_path.unlink()
    with pytest.raises(EvidenceIntegrityError, match="Mapping authority"):
        service.research.get(manifest.dataset_id)  # type: ignore[attr-defined]


def test_mapping_authority_must_be_inside_project_and_complete(tmp_path: Path) -> None:
    security_id = SecurityId.assign()
    external = SecurityMappingStore(tmp_path.parent / f"{tmp_path.name}-external-mapping.json")
    external.persist(
        (
            mapping_from_listing(
                source=DataSource.YAHOO_FINANCE,
                source_identifier="SYNTH",
                ticker="SYNTH",
                exchange="XNYS",
                mic="XNYS",
                valid_from=date(2020, 1, 1),
                valid_to=None,
                provenance="synthetic external mapping",
                retrieval_timestamp=datetime(2024, 1, 1, tzinfo=UTC),
                evidence=MappingEvidence.OWNER_CONFIRMED,
                security_id=security_id,
            ),
        )
    )
    service = DataIngestionService(_temp_config(tmp_path), root=tmp_path)
    request = RetrievalRequest(
        DataSource.YAHOO_FINANCE,
        "daily_market",
        DateRange(date(2024, 1, 1), date(2024, 1, 3)),
        ("SYNTH",),
    )
    with pytest.raises(DataQualityError, match="inside the project"):
        service.ingest(
            SyntheticMarketAdapter(external, security_id),
            request,
            DAILY_MARKET,
            "txt",
            "text/plain",
        )

    internal = SecurityMappingStore(tmp_path / "data/metadata/internal-mapping.json")
    internal.persist(external.load())
    external.path.unlink()

    class PartiallyMapped(SyntheticMarketAdapter):
        def standardize(
            self, payload: bytes, request: RetrievalRequest
        ) -> tuple[dict[str, object], ...]:
            rows = [dict(row) for row in super().standardize(payload, request)]
            rows[-1]["security_id"] = None
            return tuple(rows)

    with pytest.raises(DataQualityError, match="mix mapped and unmapped"):
        service.ingest(
            PartiallyMapped(internal, security_id),
            request,
            DAILY_MARKET,
            "txt",
            "text/plain",
        )


def test_lower_level_adapter_cannot_inject_security_identity(tmp_path: Path) -> None:
    class InjectedAdapter(SourceAdapter[bytes]):
        source = DataSource.YAHOO_FINANCE

        def retrieve(self, request: RetrievalRequest) -> bytes:
            return b"synthetic injected identity fixture"

        def standardize(
            self, payload: bytes, request: RetrievalRequest
        ) -> tuple[dict[str, object], ...]:
            return (
                {
                    "security_id": SecurityId.assign().value,
                    "ticker": "SYNTH",
                    "trading_date": date(2024, 1, 2),
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
                    "retrieval_timestamp": datetime(2024, 1, 3, tzinfo=UTC),
                    "schema_version": "1.0.0",
                },
            )

    service = DataIngestionService(_temp_config(tmp_path), root=tmp_path)
    with pytest.raises(DataQualityError, match="mapping authority"):
        service.ingest(
            InjectedAdapter(),
            RetrievalRequest(
                DataSource.YAHOO_FINANCE,
                "daily_market",
                DateRange(date(2024, 1, 2), date(2024, 1, 2)),
                ("SYNTH",),
            ),
            DAILY_MARKET,
            "txt",
            "text/plain",
        )


def test_missing_or_unsupported_mapping_authority_fails_closed(tmp_path: Path) -> None:
    security_id = SecurityId.assign()
    internal = SecurityMappingStore(tmp_path / "data/metadata/mapping.json")
    internal.persist(
        (
            mapping_from_listing(
                source=DataSource.YAHOO_FINANCE,
                source_identifier="SYNTH",
                ticker="SYNTH",
                exchange="XNYS",
                mic="XNYS",
                valid_from=date(2020, 1, 1),
                valid_to=None,
                provenance="synthetic mapping",
                retrieval_timestamp=datetime(2024, 1, 1, tzinfo=UTC),
                evidence=MappingEvidence.OWNER_CONFIRMED,
                security_id=security_id,
            ),
        )
    )

    class OwnerIdentityAdapter(SyntheticMarketAdapter):
        source = DataSource.OWNER_SUPPLIED

    service = DataIngestionService(_temp_config(tmp_path), root=tmp_path)
    request = RetrievalRequest(
        DataSource.OWNER_SUPPLIED,
        "daily_market",
        DateRange(date(2024, 1, 1), date(2024, 1, 3)),
        ("SYNTH",),
    )
    with pytest.raises(DataQualityError, match="not defined"):
        service.ingest(
            OwnerIdentityAdapter(internal, security_id),
            request,
            DAILY_MARKET,
            "txt",
            "text/plain",
        )
    internal.path.unlink()
    with pytest.raises(DataQualityError, match="missing"):
        service.ingest(
            SyntheticMarketAdapter(internal, security_id),
            RetrievalRequest(
                DataSource.YAHOO_FINANCE,
                "daily_market",
                DateRange(date(2024, 1, 1), date(2024, 1, 3)),
                ("SYNTH",),
            ),
            DAILY_MARKET,
            "txt",
            "text/plain",
        )


def test_sec_mapping_authority_is_enforced_centrally(tmp_path: Path) -> None:
    issuer_id = IssuerId.from_cik("1")
    security_id = SecurityId.assign()
    mapping = IssuerListingMappingStore(tmp_path / "data/metadata/issuer-listing.json")
    mapping.persist(
        (
            IssuerListingMapping(
                issuer_id=issuer_id,
                security_id=security_id,
                valid_from=date(2020, 1, 1),
                valid_to=None,
                status=MappingStatus.RESOLVED,
                evidence=MappingEvidence.OWNER_CONFIRMED,
                provenance="synthetic assurance mapping",
                retrieval_timestamp=datetime(2024, 1, 1, tzinfo=UTC),
            ),
        )
    )

    class MappedSecAdapter(SourceAdapter[bytes]):
        source = DataSource.SEC_EDGAR

        def __init__(self, observed: SecurityId) -> None:
            self.observed = observed

        def mapping_authority_path(self) -> Path:
            return mapping.path

        def retrieve(self, request: RetrievalRequest) -> bytes:
            return b"synthetic mapped SEC fixture"

        def standardize(
            self, payload: bytes, request: RetrievalRequest
        ) -> tuple[dict[str, object], ...]:
            return (
                {
                    "issuer_id": issuer_id.value,
                    "security_id": self.observed.value,
                    "ticker": "SYNTH",
                    "cik": "0000000001",
                    "entity_name": "Synthetic Issuer",
                    "taxonomy": "us-gaap",
                    "concept": "SyntheticConcept",
                    "label": None,
                    "description": None,
                    "unit": "USD",
                    "value": 1.0,
                    "fiscal_year": 2023,
                    "fiscal_period": "FY",
                    "period_start": date(2023, 1, 1),
                    "period_end": date(2023, 12, 31),
                    "filing_date": date(2024, 2, 1),
                    "form": "10-K",
                    "accession_number": "synthetic-accession",
                    "frame": None,
                    "source": "sec_edgar",
                    "retrieval_timestamp": datetime(2024, 2, 2, tzinfo=UTC),
                    "availability_timestamp": datetime(2024, 2, 1, 23, 59, tzinfo=UTC),
                    "availability_quality": "INFERRED_DATE_LEVEL",
                    "schema_version": "3.0.0",
                },
            )

    service = DataIngestionService(_temp_config(tmp_path), root=tmp_path)
    manifest = service.ingest(
        MappedSecAdapter(security_id),
        RetrievalRequest(DataSource.SEC_EDGAR, "1"),
        SEC_FACTS,
        "txt",
        "text/plain",
    )
    assert service.research.get(manifest.dataset_id).mapping_status == "RESOLVED"

    with pytest.raises(DataQualityError, match="differs from mapping authority"):
        service.ingest(
            MappedSecAdapter(SecurityId.assign()),
            RetrievalRequest(DataSource.SEC_EDGAR, "1"),
            SEC_FACTS,
            "txt",
            "text/plain",
        )


def test_abrupt_run_completion_never_leaves_false_success(tmp_path: Path) -> None:
    result = subprocess.run(
        [sys.executable, "tests/crash_worker.py", str(tmp_path), "run_completion"],
        cwd=Path.cwd(),
        check=False,
    )
    assert result.returncode == 91
    terminal = list((tmp_path / "data/manifests").rglob("run.json"))
    assert not terminal or all(
        json.loads(path.read_text())["status"] != "SUCCESS" for path in terminal
    )
    restarted = DataIngestionService(_temp_config(tmp_path), root=tmp_path)
    assert restarted.research.list_authenticated() == []


@pytest.mark.parametrize("terminal_file", ["run.json", "run-started.json"])
def test_run_transition_evidence_is_required(tmp_path: Path, terminal_file: str) -> None:
    service, manifest, manifest_path = _publish(tmp_path)
    manifest_path.with_name(terminal_file).unlink()
    with pytest.raises(EvidenceIntegrityError, match="run evidence"):
        service.research.get(manifest.dataset_id)  # type: ignore[attr-defined]


def test_direct_demotion_is_authoritative_across_rebuild(tmp_path: Path) -> None:
    service, manifest, _ = _publish(tmp_path)
    service.catalog.demote(manifest.dataset_id)  # type: ignore[attr-defined]
    journal = LifecycleEventStore(tmp_path / manifest.lifecycle_journal_path)  # type: ignore[attr-defined]
    assert journal.load()[-1].new_state is LifecycleState.DEMOTED
    service.recovery.rebuild_catalog()
    assert service.research.list_authenticated() == []


def test_deleting_latest_lifecycle_event_is_detected_as_rollback(tmp_path: Path) -> None:
    service, manifest, _ = _publish(tmp_path)
    journal = LifecycleEventStore(tmp_path / manifest.lifecycle_journal_path)  # type: ignore[attr-defined]
    sorted(journal.root.glob("*.json"))[-1].unlink()
    with pytest.raises(EvidenceIntegrityError):
        service.research.get(manifest.dataset_id)  # type: ignore[attr-defined]
    assert service.catalog.list_datasets(research_ready_only=True) == []


def test_verified_handle_exposes_authenticated_provenance(tmp_path: Path) -> None:
    service, manifest, _ = _publish(tmp_path)
    handle = service.research.get(manifest.dataset_id)  # type: ignore[attr-defined]
    assert handle.lifecycle_state == "FINALIZED"
    assert handle.lineage_id == manifest.lineage_id  # type: ignore[attr-defined]
    assert handle.promotion_id == manifest.promotion_event_id  # type: ignore[attr-defined]
    assert handle.run_id == manifest.run_id  # type: ignore[attr-defined]
    assert handle.mapping_status == "NOT_APPLICABLE"
    assert handle.limitations == ("LIVE INTEGRATION VALIDATION PENDING",)
