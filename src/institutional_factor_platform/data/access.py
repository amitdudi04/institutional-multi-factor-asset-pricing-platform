"""Research-data read and recovery boundary."""

import json
import os
import socket
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

import duckdb
import pyarrow as pa
import pyarrow.parquet as pq

from institutional_factor_platform.data.domain import DatasetStatus
from institutional_factor_platform.data.lineage import (
    LifecycleEvent,
    LifecycleEventStore,
    LifecycleState,
)
from institutional_factor_platform.data.storage import (
    DuckDBCatalog,
    authenticate_dataset_evidence,
    sha256_file,
)
from institutional_factor_platform.exceptions import EvidenceIntegrityError


@dataclass(frozen=True, slots=True)
class VerifiedDatasetHandle:
    dataset_id: str
    artifact_path: Path
    checksum: str
    schema_version: str
    unit_metadata: dict[str, str]
    configuration_hash: str
    git_commit: str
    validation_status: DatasetStatus
    mapping_status: str
    mapping_evidence_id: str | None
    lifecycle_state: str
    lineage_id: str
    promotion_id: str
    run_id: str
    temporal_policy: str
    limitations: tuple[str, ...]


class ResearchDatasetRepository:
    """Only supported research-ready read boundary; raw DuckDB access is operational only."""

    def __init__(self, catalog: DuckDBCatalog, project_root: Path) -> None:
        self.catalog = catalog
        self.project_root = project_root.resolve()

    def list_authenticated(self) -> list[tuple[str, str, str]]:
        try:
            self.catalog.verify_integrity(self.project_root)
        except EvidenceIntegrityError:
            pass
        return self.catalog.list_datasets(research_ready_only=True)

    def get(self, dataset_id: str) -> VerifiedDatasetHandle:
        self.catalog.verify_integrity(self.project_root)
        with duckdb.connect(str(self.catalog.path), read_only=True) as connection:
            row = connection.execute(
                "SELECT manifest_path FROM dataset_registry "
                "WHERE dataset_id = ? AND promoted = TRUE AND finalized = TRUE",
                [dataset_id],
            ).fetchone()
        if row is None:
            raise EvidenceIntegrityError(
                f"Dataset is not authenticated research-ready: {dataset_id}"
            )
        manifest_path = Path(str(row[0]))
        manifest = authenticate_dataset_evidence(
            dataset_id,
            manifest_path,
            self.project_root,
            required_state=LifecycleState.FINALIZED,
        )
        artifact = (self.project_root / manifest.parquet_path).resolve()
        if sha256_file(artifact) != manifest.output_checksum:
            self.catalog.demote(dataset_id)
            raise EvidenceIntegrityError("Dataset artifact changed during authenticated read.")
        return VerifiedDatasetHandle(
            dataset_id=dataset_id,
            artifact_path=artifact,
            checksum=manifest.output_checksum,
            schema_version=manifest.schema_version,
            unit_metadata=manifest.unit_metadata,
            configuration_hash=manifest.configuration_hash,
            git_commit=manifest.git_commit,
            validation_status=manifest.validation_status,
            mapping_status=manifest.mapping_status,
            mapping_evidence_id=manifest.mapping_evidence_id,
            lifecycle_state=LifecycleState.FINALIZED.value,
            lineage_id=manifest.lineage_id,
            promotion_id=str(manifest.promotion_event_id),
            run_id=manifest.run_id,
            temporal_policy=manifest.temporal_policy_version,
            limitations=("LIVE INTEGRATION VALIDATION PENDING",),
        )

    def read_table(self, dataset_id: str) -> pa.Table:
        handle = self.get(dataset_id)
        return pq.read_table(handle.artifact_path)


class RecoveryService:
    """Deterministic local startup reconciliation and atomic catalog rebuild."""

    def __init__(self, catalog: DuckDBCatalog, project_root: Path, manifests_root: Path) -> None:
        self.catalog = catalog
        self.project_root = project_root.resolve()
        self.manifests_root = manifests_root

    def reconcile_startup(self) -> dict[str, str]:
        outcomes: dict[str, str] = {}
        for journal_path in sorted(self.manifests_root.rglob("lifecycle")):
            store = LifecycleEventStore(journal_path)
            try:
                events = store.load()
                if not events:
                    continue
                last = events[-1]
                if last.new_state in {
                    LifecycleState.ARTIFACT_PUBLISHED,
                    LifecycleState.REGISTERED,
                    LifecycleState.PROMOTION_PENDING,
                    LifecycleState.PROMOTED,
                }:
                    recovery = _continue_lifecycle(
                        store, last, LifecycleState.RECOVERY_REQUIRED, "startup reconciliation"
                    )
                    _continue_lifecycle(
                        store, recovery, LifecycleState.DEMOTED, "startup reconciliation"
                    )
                    outcomes[last.dataset_id] = "DEMOTED"
                    if self.catalog.path.exists():
                        self.catalog.demote(last.dataset_id, record_lifecycle=False)
            except Exception as exc:
                outcomes[str(journal_path)] = f"MANUAL_INTERVENTION_REQUIRED: {exc}"
        if self.catalog.path.exists():
            self.catalog.initialize()
            with duckdb.connect(str(self.catalog.path), read_only=True) as connection:
                incomplete_rows = connection.execute(
                    "SELECT dataset_id, lifecycle_journal_path FROM dataset_registry "
                    "WHERE finalized = FALSE"
                ).fetchall()
            for dataset_id, journal_value in incomplete_rows:
                store = LifecycleEventStore(Path(str(journal_value)))
                try:
                    events = store.load()
                    if events and events[-1].new_state is LifecycleState.FINALIZED:
                        pending = _continue_lifecycle(
                            store,
                            events[-1],
                            LifecycleState.DEMOTION_PENDING,
                            "incomplete catalog activation",
                        )
                        _continue_lifecycle(
                            store,
                            pending,
                            LifecycleState.DEMOTED,
                            "incomplete catalog activation",
                        )
                        outcomes[str(dataset_id)] = "DEMOTED"
                    self.catalog.demote(str(dataset_id), record_lifecycle=False)
                except Exception as exc:
                    outcomes[str(dataset_id)] = f"MANUAL_INTERVENTION_REQUIRED: {exc}"
            try:
                self.catalog.verify_integrity(self.project_root)
            except EvidenceIntegrityError as exc:
                outcomes["integrity"] = f"INVALID: {exc}"
        return outcomes

    def rebuild_catalog(self) -> DuckDBCatalog:
        return DuckDBCatalog.rebuild_from_manifests(
            self.catalog.path, self.manifests_root, self.project_root
        )

    def reconcile_locks(self, lock_root: Path) -> dict[str, str]:
        outcomes: dict[str, str] = {}
        for lock in sorted(lock_root.glob("*.lock")):
            try:
                value = json.loads(lock.read_text(encoding="utf-8"))
                process_id = int(value["process_id"])
                run_id = str(value["lock_id"]).removeprefix("publication:")
                if str(value.get("host")) == socket.gethostname() and _process_alive(process_id):
                    outcomes[lock.name] = "ACTIVE"
                    continue
                journal = LifecycleEventStore(self.manifests_root / run_id / "lifecycle")
                events = journal.load()
                if events and events[-1].new_state in {
                    LifecycleState.FINALIZED,
                    LifecycleState.DEMOTED,
                    LifecycleState.INVALIDATED,
                    LifecycleState.SUPERSEDED,
                }:
                    lock.unlink()
                    outcomes[lock.name] = "RECOVERED"
                else:
                    outcomes[lock.name] = "MANUAL_INTERVENTION_REQUIRED"
            except Exception:
                outcomes[lock.name] = "MANUAL_INTERVENTION_REQUIRED"
        return outcomes


def _continue_lifecycle(
    store: LifecycleEventStore,
    previous: LifecycleEvent,
    state: LifecycleState,
    reason: str,
) -> LifecycleEvent:
    values = previous.model_dump(mode="python", exclude={"event_checksum"})
    values.update(
        {
            "sequence": previous.sequence + 1,
            "event_id": (
                f"lifecycle:{previous.run_id}:{previous.sequence + 1:04d}:{state.value.lower()}"
            ),
            "event_type": state.value,
            "prior_event_id": previous.event_id,
            "prior_state": previous.new_state,
            "new_state": state,
            "event_timestamp": datetime.now(UTC),
            "reason": reason,
        }
    )
    event = LifecycleEvent.create(**values)
    store.persist(event)
    return event


def _process_alive(process_id: int) -> bool:
    if process_id <= 0:
        return False
    if os.name == "nt":
        import ctypes

        process_query_limited_information = 0x1000
        kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)  # type: ignore[attr-defined, unused-ignore]
        handle = kernel32.OpenProcess(process_query_limited_information, False, process_id)
        if handle:
            kernel32.CloseHandle(handle)
            return True
        return bool(ctypes.get_last_error() == 5)  # type: ignore[attr-defined, unused-ignore]
    try:
        os.kill(process_id, 0)
    except OSError:
        return False
    return True
