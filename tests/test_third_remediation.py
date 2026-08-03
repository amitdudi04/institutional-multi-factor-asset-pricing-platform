import json
import socket
import subprocess
import sys
from datetime import UTC, date, datetime
from pathlib import Path

import httpx
import pytest
from pydantic import ValidationError
from test_service_cli_calendar import SyntheticMacroAdapter, _temp_config

from institutional_factor_platform.data import evidence, storage
from institutional_factor_platform.data.access import ResearchDatasetRepository
from institutional_factor_platform.data.config import load_phase1_config
from institutional_factor_platform.data.contracts import MACRO_OBSERVATIONS
from institutional_factor_platform.data.domain import (
    DataSource,
    IssuerId,
    IssuerListingMapping,
    MappingEvidence,
    MappingStatus,
    RetrievalRequest,
    SecurityId,
)
from institutional_factor_platform.data.lineage import LifecycleEventStore, LifecycleState
from institutional_factor_platform.data.security_master import IssuerListingMappingStore
from institutional_factor_platform.data.services import DataIngestionService
from institutional_factor_platform.data.sources.base import HttpTransport, SourceAdapter
from institutional_factor_platform.data.sources.sec_edgar import SecEdgarAdapter
from institutional_factor_platform.data.storage import (
    DuckDBCatalog,
    authenticate_dataset_evidence,
    sha256_file,
)
from institutional_factor_platform.exceptions import (
    DataQualityError,
    EvidenceIntegrityError,
    ManifestError,
    RetrievalError,
    SecurityMappingError,
)


def _publish(root: Path) -> tuple[DataIngestionService, object, Path]:
    service = DataIngestionService(_temp_config(root), root=root)
    manifest = service.ingest(
        SyntheticMacroAdapter(),
        RetrievalRequest(DataSource.OWNER_SUPPLIED, "synthetic_macro"),
        MACRO_OBSERVATIONS,
        "txt",
        "text/plain",
    )
    manifest_path = next((root / "data/manifests").rglob("dataset.json"))
    return service, manifest, manifest_path


def test_disconnected_lifecycle_cannot_authorize_promotion(tmp_path: Path) -> None:
    service, manifest, manifest_path = _publish(tmp_path)
    value = json.loads(manifest_path.read_text(encoding="utf-8"))
    lineage_path = tmp_path / value["lineage_path"]
    lineage = json.loads(lineage_path.read_text(encoding="utf-8"))
    lineage["edges"] = [
        edge
        for edge in lineage["edges"]
        if edge["relationship_type"] not in {"REGISTERED_IN_CATALOG", "PROMOTED_TO_RESEARCH_READY"}
    ]
    template = dict(lineage["edges"][0])
    template.update(
        {
            "parent_artifact_id": "unrelated:a",
            "child_artifact_id": "unrelated:b",
            "relationship_type": "REGISTERED_IN_CATALOG",
        }
    )
    promotion = dict(template)
    promotion.update(
        {
            "parent_artifact_id": "unrelated:b",
            "child_artifact_id": "unrelated:c",
            "relationship_type": "PROMOTED_TO_RESEARCH_READY",
        }
    )
    lineage["artifacts"].extend(["unrelated:a", "unrelated:b", "unrelated:c"])
    lineage["edges"].extend([template, promotion])
    altered_lineage = tmp_path / "disconnected-lineage.json"
    altered_lineage.write_text(json.dumps(lineage), encoding="utf-8")
    value["lineage_path"] = str(altered_lineage)
    value["lineage_checksum"] = sha256_file(altered_lineage)
    altered_manifest = tmp_path / "disconnected-manifest.json"
    altered_manifest.write_text(json.dumps(value), encoding="utf-8")
    service.catalog.demote(manifest.dataset_id)  # type: ignore[attr-defined]
    with pytest.raises(EvidenceIntegrityError, match="exact connected lifecycle"):
        service.catalog.stage_promotion(
            manifest.dataset_id,
            altered_manifest,
            tmp_path,  # type: ignore[attr-defined]
        )
    assert service.catalog.list_datasets(research_ready_only=True) == []


def test_verification_failure_revokes_reads_and_survives_restart(tmp_path: Path) -> None:
    service, manifest, _ = _publish(tmp_path)
    validation = tmp_path / manifest.validation_report_path  # type: ignore[attr-defined]
    validation.unlink()
    repository = ResearchDatasetRepository(service.catalog, tmp_path)
    assert repository.list_authenticated() == []
    assert service.catalog.list_datasets(research_ready_only=True) == []
    journal = LifecycleEventStore(tmp_path / manifest.lifecycle_journal_path)  # type: ignore[attr-defined]
    assert journal.load()[-1].new_state is LifecycleState.INVALIDATED
    restarted = DataIngestionService(_temp_config(tmp_path), root=tmp_path)
    assert restarted.research.list_authenticated() == []


@pytest.mark.parametrize(
    "boundary",
    [
        "artifact_publication",
        "catalog_registration",
        "final_manifest_persistence",
        "catalog_promotion",
        "promotion_event_persistence",
        "run_completion",
        "journal_finalization",
    ],
)
def test_abrupt_subprocess_termination_never_exposes_incomplete_data(
    tmp_path: Path, boundary: str
) -> None:
    result = subprocess.run(
        [sys.executable, "tests/crash_worker.py", str(tmp_path), boundary],
        cwd=Path.cwd(),
        check=False,
    )
    assert result.returncode == 91
    restarted = DataIngestionService(_temp_config(tmp_path), root=tmp_path)
    assert restarted.research.list_authenticated() == []


def test_demotion_is_authoritative_over_historical_manifest(tmp_path: Path) -> None:
    def fail(name: str) -> None:
        if name == "promotion_manifest_persistence":
            raise RuntimeError("injected finalization failure")

    service = DataIngestionService(_temp_config(tmp_path), root=tmp_path, failure_hook=fail)
    with pytest.raises(RuntimeError, match="finalization"):
        service.ingest(
            SyntheticMacroAdapter(),
            RetrievalRequest(DataSource.OWNER_SUPPLIED, "synthetic_macro"),
            MACRO_OBSERVATIONS,
            "txt",
            "text/plain",
        )
    published = json.loads(next((tmp_path / "data/manifests").rglob("dataset.json")).read_text())
    assert published["promotion_state"] == "PUBLISHED"
    journal = LifecycleEventStore(next((tmp_path / "data/manifests").rglob("lifecycle")))
    assert journal.load()[-1].new_state is LifecycleState.DEMOTED
    assert service.research.list_authenticated() == []
    restarted = DataIngestionService(_temp_config(tmp_path), root=tmp_path)
    assert restarted.research.list_authenticated() == []


def test_configuration_and_report_identities_are_content_bound(tmp_path: Path) -> None:
    _, manifest, manifest_path = _publish(tmp_path)
    value = json.loads(manifest_path.read_text())
    snapshot = tmp_path / value["configuration_snapshot_path"]
    original_snapshot = snapshot.read_bytes()
    snapshot.write_text("{}\n", encoding="utf-8")
    value["configuration_snapshot_checksum"] = sha256_file(snapshot)
    altered = tmp_path / "altered-config.json"
    altered.write_text(json.dumps(value), encoding="utf-8")
    with pytest.raises(EvidenceIntegrityError, match="non-empty"):
        authenticate_dataset_evidence(manifest.dataset_id, altered, tmp_path)  # type: ignore[attr-defined]
    snapshot.write_bytes(original_snapshot)
    value = json.loads(manifest_path.read_text())
    value["validation_report_id"] = "validation:arbitrary"
    altered.write_text(json.dumps(value), encoding="utf-8")
    with pytest.raises(EvidenceIntegrityError, match="content-bound"):
        authenticate_dataset_evidence(manifest.dataset_id, altered, tmp_path)  # type: ignore[attr-defined]


def test_identity_ambiguity_and_sec_caller_id_are_blocked(tmp_path: Path) -> None:
    issuer = IssuerId.from_cik("1")
    listing = SecurityId.assign()
    now = datetime.now(UTC)
    store = IssuerListingMappingStore(tmp_path / "issuer-map.json")
    store.persist(
        (
            IssuerListingMapping(
                issuer,
                listing,
                date(2020, 1, 1),
                None,
                MappingStatus.RESOLVED,
                MappingEvidence.OWNER_CONFIRMED,
                "owner evidence",
                now,
            ),
            IssuerListingMapping(
                issuer,
                None,
                date(2020, 1, 1),
                None,
                MappingStatus.AMBIGUOUS,
                MappingEvidence.REGISTRANT_ONLY,
                "ambiguous evidence",
                now,
            ),
        )
    )
    with pytest.raises(SecurityMappingError, match="unresolved or ambiguous"):
        store.resolve(issuer, date(2024, 1, 1))

    config = load_phase1_config()
    transport = HttpTransport(
        config.runtime,
        httpx.Client(transport=httpx.MockTransport(lambda _: httpx.Response(200))),
    )
    adapter = SecEdgarAdapter(config.sources.sec, transport)
    payload = json.dumps(
        {
            "cik": 1,
            "entityName": "Synthetic Issuer",
            "facts": {
                "us-gaap": {
                    "Assets": {
                        "units": {
                            "USD": [
                                {
                                    "val": 1,
                                    "end": "2023-12-31",
                                    "filed": "2024-01-31",
                                    "form": "10-K",
                                    "accn": "synthetic",
                                }
                            ]
                        }
                    }
                }
            },
        }
    ).encode()
    with pytest.raises(RetrievalError, match="caller-supplied"):
        adapter.standardize(
            payload,
            RetrievalRequest(
                DataSource.SEC_EDGAR, "1", parameters={"security_id": "caller-forged"}
            ),
        )
    assert not hasattr(SecurityId, "create")


def test_atomic_rebuild_preserves_active_catalog_on_failure(tmp_path: Path) -> None:
    service, manifest, _ = _publish(tmp_path)
    promotion = next((tmp_path / "data/manifests").rglob("promotion.json"))
    invalid = json.loads(promotion.read_text())
    invalid["schema_version"] = "1.0.0"
    bad = tmp_path / "data/manifests/z-invalid/promotion.json"
    bad.parent.mkdir(parents=True)
    bad.write_text(json.dumps(invalid), encoding="utf-8")
    with pytest.raises(ValidationError):
        DuckDBCatalog.rebuild_from_manifests(
            service.catalog.path, tmp_path / "data/manifests", tmp_path
        )
    assert service.research.list_authenticated()[0][0] == manifest.dataset_id  # type: ignore[attr-defined]


def test_atomic_rebuild_preserves_active_catalog_on_activation_crash(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    service, manifest, _ = _publish(tmp_path)

    def fail_replace(source: Path, destination: Path) -> None:
        raise OSError(f"injected activation crash: {source} -> {destination}")

    monkeypatch.setattr(storage.os, "replace", fail_replace)
    with pytest.raises(OSError, match="activation crash"):
        DuckDBCatalog.rebuild_from_manifests(
            service.catalog.path, tmp_path / "data/manifests", tmp_path
        )
    assert service.research.list_authenticated()[0][0] == manifest.dataset_id  # type: ignore[attr-defined]


def test_atomic_evidence_failure_leaves_no_partial_target(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    target = tmp_path / "evidence.json"

    def fail_replace(source: Path, destination: Path) -> None:
        raise OSError(f"injected publication crash: {source} -> {destination}")

    monkeypatch.setattr(evidence.os, "replace", fail_replace)
    with pytest.raises(OSError, match="publication crash"):
        evidence.atomic_write_json(target, {"authoritative": True})
    assert not target.exists()
    assert not list(tmp_path.glob(".evidence.json-*"))


def test_lifecycle_journal_rejects_duplicate_or_reordered_events(tmp_path: Path) -> None:
    _, manifest, _ = _publish(tmp_path)
    journal_root = tmp_path / manifest.lifecycle_journal_path  # type: ignore[attr-defined]
    first = sorted(journal_root.glob("*.json"))[0]
    (journal_root / "9999_duplicate.json").write_bytes(first.read_bytes())
    with pytest.raises(ManifestError, match=r"Duplicate|sequence"):
        LifecycleEventStore(journal_root).load()


def test_ambiguous_stale_lock_requires_manual_intervention(tmp_path: Path) -> None:
    service = DataIngestionService(_temp_config(tmp_path), root=tmp_path)
    lock_root = tmp_path / "data/metadata/publication-locks"
    lock_root.mkdir(parents=True)
    lock = lock_root / "unknown.lock"
    lock.write_text(
        json.dumps(
            {
                "lock_id": "publication:unknown-run",
                "process_id": 2_147_483_647,
                "host": socket.gethostname(),
                "created_at": datetime.now(UTC).isoformat(),
                "operation": "publish",
                "dataset": "unknown",
            }
        ),
        encoding="utf-8",
    )
    outcome = service.recovery.reconcile_locks(lock_root)
    assert outcome[lock.name] == "MANUAL_INTERVENTION_REQUIRED"
    assert lock.exists()


def test_unit_reconciliation_rejects_request_row_contradiction(tmp_path: Path) -> None:
    class SharesMacro(SourceAdapter[bytes]):
        source = DataSource.OWNER_SUPPLIED

        def retrieve(self, request: RetrievalRequest) -> bytes:
            return b"synthetic unit fixture"

        def standardize(
            self, payload: bytes, request: RetrievalRequest
        ) -> tuple[dict[str, object], ...]:
            return (
                {
                    "series_id": "DGS3MO",
                    "observation_date": date(2024, 1, 2),
                    "value": 5.0,
                    "source_unit": "shares",
                    "frequency": "daily",
                    "seasonal_adjustment": None,
                    "source": "owner_supplied",
                    "retrieval_timestamp": datetime(2024, 1, 3, tzinfo=UTC),
                    "availability_timestamp": None,
                    "missing_value": False,
                    "schema_version": "1.0.0",
                },
            )

    service = DataIngestionService(_temp_config(tmp_path), root=tmp_path)
    request = RetrievalRequest(
        DataSource.OWNER_SUPPLIED,
        "owner_macro",
        parameters={"units": {"value": "percent_per_annum"}},
    )
    with pytest.raises(DataQualityError, match="contradicts"):
        service.ingest(SharesMacro(), request, MACRO_OBSERVATIONS, "txt", "text/plain")
    assert service.catalog.list_datasets(research_ready_only=True) == []


def test_authenticated_repository_returns_verified_handle(tmp_path: Path) -> None:
    service, manifest, _ = _publish(tmp_path)
    handle = service.research.get(manifest.dataset_id)  # type: ignore[attr-defined]
    assert handle.checksum == manifest.output_checksum  # type: ignore[attr-defined]
    assert handle.configuration_hash == manifest.configuration_hash  # type: ignore[attr-defined]
    assert service.research.read_table(manifest.dataset_id).num_rows == 1  # type: ignore[attr-defined]
