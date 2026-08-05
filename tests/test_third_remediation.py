import json
import os
import socket
import subprocess
import sys
from datetime import UTC, date, datetime, timedelta
from pathlib import Path

import duckdb
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
    SymbolHistoryRecord,
)
from institutional_factor_platform.data.lineage import (
    LifecycleEvent,
    LifecycleEventStore,
    LifecycleState,
    LineageDocument,
    LineageEdge,
    LineageGraph,
    LineageStore,
    RelationshipType,
)
from institutional_factor_platform.data.security_master import (
    IssuerListingMappingStore,
    SecurityMappingStore,
    SymbolHistoryStore,
    mapping_from_listing,
)
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


def test_startup_integrity_loss_is_invalidated_before_any_read(tmp_path: Path) -> None:
    _, manifest, _ = _publish(tmp_path)
    (tmp_path / manifest.validation_report_path).unlink()  # type: ignore[attr-defined]
    restarted = DataIngestionService(_temp_config(tmp_path), root=tmp_path)
    assert restarted.research.list_authenticated() == []
    journal = LifecycleEventStore(tmp_path / manifest.lifecycle_journal_path)  # type: ignore[attr-defined]
    assert journal.load()[-1].new_state is LifecycleState.INVALIDATED


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
        "catalog_activation",
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


def test_abrupt_atomic_json_termination_never_publishes_target(tmp_path: Path) -> None:
    result = subprocess.run(
        [sys.executable, "tests/crash_worker.py", str(tmp_path), "atomic_json"],
        cwd=Path.cwd(),
        check=False,
    )
    assert result.returncode == 91
    assert not (tmp_path / "atomic-target.json").exists()


def test_abrupt_rebuild_activation_preserves_active_catalog(tmp_path: Path) -> None:
    service, manifest, _ = _publish(tmp_path)
    result = subprocess.run(
        [sys.executable, "tests/crash_worker.py", str(tmp_path), "rebuild_activation"],
        cwd=Path.cwd(),
        check=False,
    )
    assert result.returncode == 91
    assert service.research.list_authenticated()[0][0] == manifest.dataset_id  # type: ignore[attr-defined]


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
    with pytest.raises(EvidenceIntegrityError, match="not authenticated"):
        service.research.get("missing-dataset")


def test_evidence_paths_cannot_escape_project_root(tmp_path: Path) -> None:
    assert (
        evidence.resolve_project_path("data/example.json", tmp_path)
        == (tmp_path / "data/example.json").resolve()
    )
    with pytest.raises(ManifestError, match="escapes project root"):
        evidence.resolve_project_path("../outside.json", tmp_path)


def test_terminal_and_active_locks_are_reconciled_conservatively(tmp_path: Path) -> None:
    service, manifest, _ = _publish(tmp_path)
    lock_root = tmp_path / "data/metadata/publication-locks"
    lock_root.mkdir(parents=True, exist_ok=True)
    terminal = lock_root / "terminal.lock"
    terminal.write_text(
        json.dumps(
            {
                "lock_id": f"publication:{manifest.run_id}",  # type: ignore[attr-defined]
                "process_id": 2_147_483_647,
                "host": socket.gethostname(),
            }
        ),
        encoding="utf-8",
    )
    active = lock_root / "active.lock"
    active.write_text(
        json.dumps(
            {
                "lock_id": "publication:active-run",
                "process_id": os.getpid(),
                "host": socket.gethostname(),
            }
        ),
        encoding="utf-8",
    )
    outcome = service.recovery.reconcile_locks(lock_root)
    assert outcome[terminal.name] == "RECOVERED"
    assert not terminal.exists()
    assert outcome[active.name] == "ACTIVE"
    assert active.exists()


def test_lifecycle_reconstruction_rejects_every_integrity_dimension(tmp_path: Path) -> None:
    _, manifest, _ = _publish(tmp_path)
    source_store = LifecycleEventStore(tmp_path / manifest.lifecycle_journal_path)  # type: ignore[attr-defined]
    first = source_store.load()[0]

    altered_checksum = first.model_dump(mode="json")
    altered_checksum["reason"] = "substituted"
    with pytest.raises(ValidationError, match="checksum mismatch"):
        LifecycleEvent.model_validate(altered_checksum)

    def successor(**updates: object) -> LifecycleEvent:
        values = first.model_dump(mode="python", exclude={"schema_version", "event_checksum"})
        values.update(
            {
                "sequence": 2,
                "event_id": f"lifecycle:{first.run_id}:0002:test-{len(updates)}",
                "event_type": LifecycleState.RAW_VERIFIED.value,
                "prior_event_id": first.event_id,
                "prior_state": first.new_state,
                "new_state": LifecycleState.RAW_VERIFIED,
                "event_timestamp": first.event_timestamp + timedelta(seconds=1),
            }
        )
        values.update(updates)
        return LifecycleEvent.create(**values)

    invalid_initial = first.model_dump(mode="python", exclude={"schema_version", "event_checksum"})
    invalid_initial["sequence"] = 2
    with pytest.raises(ManifestError, match="begin at sequence 1"):
        LifecycleEventStore(tmp_path / "bad-initial").persist(
            LifecycleEvent.create(**invalid_initial)
        )
    wrong_first_state = first.model_dump(
        mode="python", exclude={"schema_version", "event_checksum"}
    )
    wrong_first_state.update(
        event_type=LifecycleState.RAW_VERIFIED.value,
        new_state=LifecycleState.RAW_VERIFIED,
    )
    with pytest.raises(ManifestError, match="begin in CREATED"):
        LifecycleEventStore(tmp_path / "bad-first-state").persist(
            LifecycleEvent.create(**wrong_first_state)
        )

    idempotence_store = LifecycleEventStore(tmp_path / "idempotence")
    idempotence_store.persist(first)
    different = first.model_dump(mode="python", exclude={"schema_version", "event_checksum"})
    different["reason"] = "different immutable content"
    with pytest.raises(ManifestError, match="Refusing to overwrite"):
        idempotence_store.persist(LifecycleEvent.create(**different))

    cases = (
        (successor(sequence=3), "not contiguous"),
        (successor(prior_event_id="missing"), "predecessor"),
        (
            successor(
                event_type=LifecycleState.PROMOTED.value,
                new_state=LifecycleState.PROMOTED,
            ),
            "Invalid lifecycle transition",
        ),
        (successor(dataset_id="different"), "mixes dataset_id"),
        (successor(event_timestamp=first.event_timestamp - timedelta(seconds=1)), "out of order"),
    )
    for index, (event, message) in enumerate(cases):
        store = LifecycleEventStore(tmp_path / f"invalid-{index}")
        store.persist(first)
        with pytest.raises(ManifestError, match=message):
            store.persist(event)

    empty = LifecycleEventStore(tmp_path / "empty")
    assert empty.current_state(first.dataset_id) is None
    assert source_store.current_state(first.dataset_id) is LifecycleState.FINALIZED
    with pytest.raises(ManifestError, match="mixes dataset identities"):
        source_store.current_state("different")


def test_lineage_graph_and_store_reject_structural_corruption(tmp_path: Path) -> None:
    graph = LineageGraph()
    graph.add("raw")
    graph.add("table", ("raw",))
    graph.add("report", ("table",))
    graph.add("alternate", ("raw",))
    graph.add("diamond", ("report", "alternate"))
    assert graph.ancestors("report") == ("raw", "table")
    assert graph.ancestors("diamond") == ("alternate", "raw", "report", "table")
    with pytest.raises(ManifestError, match="own parent"):
        graph.add("self", ("self",))
    with pytest.raises(ManifestError, match="cycle"):
        graph.add("raw", ("report",))

    edge = LineageEdge(
        parent_artifact_id="raw",
        child_artifact_id="table",
        relationship_type=RelationshipType.STANDARDIZED,
        transformation_name="transform",
        transformation_version="1.0.0",
        run_id="run",
        creation_timestamp=datetime.now(UTC),
        code_commit="0" * 40,
        configuration_hash="0" * 64,
    )
    duplicate_artifacts = LineageDocument(
        schema_version="4.0.0",
        lineage_id="lineage:test",
        dataset_id="dataset",
        run_id="run",
        artifacts=("raw", "raw", "table"),
        edges=(edge,),
    )
    with pytest.raises(ManifestError, match="unique"):
        LineageStore(tmp_path / "lineage.json").persist(duplicate_artifacts)
    assert (
        LineageDocument.v3(
            lineage_id="legacy-lineage",
            dataset_id="legacy-dataset",
            run_id="legacy-run",
            artifacts=("raw", "table"),
            edges=(edge,),
        ).schema_version
        == "3.0.0"
    )
    self_edge = edge.model_copy(update={"parent_artifact_id": "table"})
    with pytest.raises(ManifestError, match="own parent"):
        LineageStore(tmp_path / "self-edge.json").persist(
            duplicate_artifacts.model_copy(update={"artifacts": ("table",), "edges": (self_edge,)})
        )
    with pytest.raises(ManifestError, match="unknown artifact"):
        LineageStore(tmp_path / "unknown-edge.json").persist(
            duplicate_artifacts.model_copy(update={"artifacts": ("raw",), "edges": (edge,)})
        )
    unknown = duplicate_artifacts.model_copy(update={"artifacts": ("raw", "table")})
    LineageStore(tmp_path / "valid-lineage.json").persist(unknown)
    with pytest.raises(ManifestError, match="missing required"):
        LineageStore(tmp_path / "valid-lineage.json").verify_complete(("absent",))


def test_startup_reconciliation_handles_empty_corrupt_and_incomplete_state(tmp_path: Path) -> None:
    service, manifest, _ = _publish(tmp_path)
    empty = tmp_path / "data/manifests/empty/lifecycle"
    empty.mkdir(parents=True)
    corrupt = tmp_path / "data/manifests/corrupt/lifecycle"
    corrupt.mkdir(parents=True)
    (corrupt / "0001_bad.json").write_text("{", encoding="utf-8")
    with duckdb.connect(str(service.catalog.path)) as connection:
        connection.execute(
            "UPDATE dataset_registry SET finalized = FALSE WHERE dataset_id = ?",
            [manifest.dataset_id],  # type: ignore[attr-defined]
        )
    outcomes = service.recovery.reconcile_startup()
    assert outcomes[manifest.dataset_id] == "DEMOTED"  # type: ignore[attr-defined]
    assert "MANUAL_INTERVENTION_REQUIRED" in outcomes[str(corrupt)]
    assert service.research.list_authenticated() == []


def test_malformed_and_nonpositive_locks_fail_closed(tmp_path: Path) -> None:
    service = DataIngestionService(_temp_config(tmp_path), root=tmp_path)
    lock_root = tmp_path / "data/metadata/publication-locks"
    lock_root.mkdir(parents=True)
    malformed = lock_root / "malformed.lock"
    malformed.write_text("{", encoding="utf-8")
    nonpositive = lock_root / "nonpositive.lock"
    nonpositive.write_text(
        json.dumps(
            {
                "lock_id": "publication:missing",
                "process_id": 0,
                "host": socket.gethostname(),
            }
        ),
        encoding="utf-8",
    )
    outcomes = service.recovery.reconcile_locks(lock_root)
    assert outcomes == {
        malformed.name: "MANUAL_INTERVENTION_REQUIRED",
        nonpositive.name: "MANUAL_INTERVENTION_REQUIRED",
    }


def test_identity_stores_fail_closed_on_corruption_conflict_and_absence(tmp_path: Path) -> None:
    malformed = tmp_path / "malformed.json"
    malformed.write_text("{", encoding="utf-8")
    stores = (
        SecurityMappingStore(malformed),
        SymbolHistoryStore(malformed),
        IssuerListingMappingStore(malformed),
    )
    for store in stores:
        with pytest.raises(SecurityMappingError, match="Invalid"):
            store.load()

    mapping_store = SecurityMappingStore(tmp_path / "empty-mappings.json")
    mapping_store.persist(())
    with pytest.raises(SecurityMappingError, match="unresolved or ambiguous"):
        mapping_store.resolve("yahoo_finance", "ABSENT", date(2024, 1, 1))
    with pytest.raises(SecurityMappingError, match="must be a datetime"):
        mapping_from_listing(
            source=DataSource.YAHOO_FINANCE,
            source_identifier="SYNTH",
            ticker="SYNTH",
            exchange="XNYS",
            mic="XNYS",
            valid_from=date(2020, 1, 1),
            valid_to=None,
            provenance="synthetic evidence",
            retrieval_timestamp="not-a-datetime",
            security_id=SecurityId.assign(),
        )

    now = datetime.now(UTC)
    first_id, second_id = SecurityId.assign(), SecurityId.assign()
    symbols = (
        SymbolHistoryRecord(
            first_id,
            "SAME",
            "XNYS",
            "XNYS",
            date(2020, 1, 1),
            None,
            DataSource.OWNER_SUPPLIED,
            "one",
            now,
            "synthetic evidence",
        ),
        SymbolHistoryRecord(
            second_id,
            "SAME",
            "XNYS",
            "XNYS",
            date(2021, 1, 1),
            None,
            DataSource.OWNER_SUPPLIED,
            "two",
            now,
            "synthetic evidence",
        ),
    )
    with pytest.raises(SecurityMappingError, match="ticker conflicts"):
        SymbolHistoryStore(tmp_path / "symbol-conflict.json").persist(symbols)

    issuer = IssuerId.from_cik("1")
    issuer_mappings = tuple(
        IssuerListingMapping(
            issuer,
            security_id,
            date(2020, 1, 1),
            None,
            MappingStatus.RESOLVED,
            MappingEvidence.OWNER_CONFIRMED,
            "owner evidence",
            now,
        )
        for security_id in (first_id, second_id)
    )
    with pytest.raises(SecurityMappingError, match="Conflicting effective"):
        IssuerListingMappingStore(tmp_path / "issuer-conflict.json").persist(issuer_mappings)
