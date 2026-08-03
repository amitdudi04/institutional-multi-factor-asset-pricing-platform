import json
from datetime import UTC, date, datetime
from pathlib import Path

import pyarrow as pa
import pytest
from pydantic import ValidationError

from institutional_factor_platform.data.contracts import MACRO_OBSERVATIONS
from institutional_factor_platform.data.domain import DatasetStatus, DataSource, RetrievalStatus
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
from institutional_factor_platform.data.manifests import (
    DatasetManifest,
    RunManifest,
    SourceManifest,
)
from institutional_factor_platform.data.storage import (
    DuckDBCatalog,
    ParquetStorage,
    QuarantineStorage,
    RawStorage,
)
from institutional_factor_platform.exceptions import (
    ChecksumMismatchError,
    ManifestError,
    PublicationConflictError,
    RawStorageError,
)

NOW = datetime(2024, 1, 3, tzinfo=UTC)
HASH = "a" * 64


def test_manifest_hash_and_immutable_write(tmp_path: Path) -> None:
    manifest = SourceManifest(
        schema_version="2.0.0",
        source_manifest_id="source:audit",
        source="owner_supplied",
        request={"dataset": "synthetic_test"},
        retrieval_time=NOW,
        response_status=RetrievalStatus.SUCCESS,
        raw_artifact_id="raw:audit",
        raw_artifact_path="raw/audit.txt",
        checksum=HASH,
        byte_size=1,
        media_type="text/plain",
        row_count=1,
        source_terms_note="Synthetic test fixture only.",
    )
    path = tmp_path / "source.json"
    manifest.write_immutable(path)
    assert len(manifest.content_hash()) == 64
    manifest.write_immutable(path)
    path.write_text("different", encoding="utf-8")
    with pytest.raises(ManifestError, match="overwrite"):
        manifest.write_immutable(path)
    with pytest.raises(ValidationError, match="non-empty"):
        manifest.model_copy(update={"row_count": 0}).__class__.model_validate(
            {**manifest.model_dump(), "row_count": 0}
        )


def test_run_lifecycle_invariants() -> None:
    base = dict(
        schema_version="2.0.0",
        run_id="run",
        run_type="test",
        start_time=NOW,
        code_version="test",
        git_commit="commit",
        configuration_hash=HASH,
        configuration_snapshot_path="snapshot.json",
        environment_version="test",
    )
    running = RunManifest(**base, status="RUNNING")
    assert running.completion_time is None
    with pytest.raises(ValidationError, match="completion"):
        RunManifest(**base, status="SUCCESS", output_artifacts=("x",))
    with pytest.raises(ValidationError, match="output"):
        RunManifest(**base, status="SUCCESS", completion_time=NOW)
    with pytest.raises(ValidationError, match="error"):
        RunManifest(**base, status="FAILED", completion_time=NOW)


def test_raw_storage_is_deterministic_and_detects_mutation(tmp_path: Path) -> None:
    storage = RawStorage(tmp_path)
    now = datetime(2024, 1, 2, 3, 4, tzinfo=UTC)
    first = storage.persist(
        source=DataSource.OWNER_SUPPLIED,
        dataset="synthetic_contract",
        content=b"synthetic-test-only",
        extension="txt",
        media_type="text/plain",
        retrieved_at=now,
    )
    second = storage.persist(
        source=DataSource.OWNER_SUPPLIED,
        dataset="synthetic_contract",
        content=b"synthetic-test-only",
        extension="txt",
        media_type="text/plain",
        retrieved_at=now,
    )
    assert first.path == second.path
    RawStorage.verify(first)
    first.path.write_bytes(b"mutated")
    with pytest.raises(ChecksumMismatchError):
        RawStorage.verify(first)
    with pytest.raises(ChecksumMismatchError):
        storage.persist(
            source=DataSource.OWNER_SUPPLIED,
            dataset="synthetic_contract",
            content=b"synthetic-test-only",
            extension="txt",
            media_type="text/plain",
            retrieved_at=now,
        )


def test_raw_storage_rejects_bad_dataset_and_naive_time(tmp_path: Path) -> None:
    storage = RawStorage(tmp_path)
    with pytest.raises(RawStorageError, match="timezone"):
        storage.persist(
            source=DataSource.OWNER_SUPPLIED,
            dataset="test",
            content=b"x",
            extension="txt",
            media_type="text/plain",
            retrieved_at=datetime.now(),
        )
    with pytest.raises(RawStorageError, match="safe path"):
        storage.persist(
            source=DataSource.OWNER_SUPPLIED,
            dataset="...",
            content=b"x",
            extension="txt",
            media_type="text/plain",
            retrieved_at=datetime.now(UTC),
        )


def _macro_table(value: float = 1.25) -> pa.Table:
    return pa.Table.from_pylist(
        [
            {
                "series_id": "SYNTHETIC_TEST_SERIES",
                "observation_date": date(2024, 1, 2),
                "value": value,
                "source_unit": "test units",
                "frequency": "daily",
                "seasonal_adjustment": None,
                "source": "owner_supplied",
                "retrieval_timestamp": NOW,
                "availability_timestamp": None,
                "missing_value": False,
                "schema_version": "1.0.0",
            }
        ],
        schema=MACRO_OBSERVATIONS.schema,
    )


def _lineage(path: Path, dataset_id: str, raw_id: str = "raw:audit") -> LineageStore:
    edge = LineageEdge(
        parent_artifact_id=raw_id,
        child_artifact_id=dataset_id,
        relationship_type=RelationshipType.MANIFESTED,
        transformation_name="synthetic",
        transformation_version="2.0.0",
        run_id="run",
        creation_timestamp=NOW,
        code_commit="commit",
        configuration_hash=HASH,
    )
    store = LineageStore(path)
    store.persist(
        LineageDocument(
            schema_version="2.0.0",
            artifacts=("source:audit", raw_id, dataset_id),
            edges=(edge,),
        )
    )
    return store


def _dataset_manifest(
    parquet: Path,
    checksum: str,
    lineage: Path,
    *,
    dataset_id: str = "dataset-audit",
    status: DatasetStatus = DatasetStatus.PASS,
    complete: bool = True,
) -> DatasetManifest:
    return DatasetManifest(
        schema_version="3.0.0",
        run_id="run",
        dataset_id=dataset_id,
        dataset_type="macro_observations",
        schema_name="macro_observations",
        schema_fingerprint=HASH,
        parent_artifacts=("raw:audit",),
        source_manifest_id="source:audit",
        source_manifest_path="source.json",
        source_manifest_checksum=HASH,
        transformation_name="synthetic_standardize",
        transformation_version="2.0.0",
        row_count=1,
        column_count=11,
        primary_key=("series_id", "observation_date"),
        validation_report_id="validation:audit",
        validation_report_path="validation.json",
        validation_report_checksum=HASH,
        validation_status=status,
        lineage_path=str(lineage),
        lineage_id="lineage:audit",
        lineage_checksum=HASH,
        lineage_complete=complete,
        quarantine_status=status is DatasetStatus.QUARANTINED,
        parquet_path=str(parquet),
        output_artifact_id=f"parquet:{checksum}",
        output_checksum=checksum,
        output_byte_size=parquet.stat().st_size,
        catalog_registration_state="NOT_REGISTERED",
        promotion_state=(
            "ELIGIBLE"
            if complete and status in {DatasetStatus.PASS, DatasetStatus.PASS_WITH_WARNINGS}
            else "NOT_ELIGIBLE"
        ),
        creation_time=NOW,
        configuration_hash=HASH,
        configuration_snapshot_path="configuration.json",
        configuration_snapshot_checksum=HASH,
        code_version="test",
        git_commit="commit",
        temporal_policy_version="2.0.0",
    )


def test_parquet_immutable_idempotent_and_conflict(tmp_path: Path) -> None:
    storage = ParquetStorage(tmp_path / "processed")
    first = storage.publish(
        "macro_observations", "immutable-id", _macro_table(), MACRO_OBSERVATIONS.schema
    )
    second = storage.publish(
        "macro_observations", "immutable-id", _macro_table(), MACRO_OBSERVATIONS.schema
    )
    assert second.reused and second.checksum == first.checksum
    original = first.path.read_bytes()
    with pytest.raises(PublicationConflictError):
        storage.publish(
            "macro_observations", "immutable-id", _macro_table(9.0), MACRO_OBSERVATIONS.schema
        )
    assert first.path.read_bytes() == original
    assert not list(first.path.parent.glob(".parquet-*.tmp"))


def test_catalog_has_no_in_memory_promotion_interface(tmp_path: Path) -> None:
    catalog = DuckDBCatalog(tmp_path / "catalog.duckdb")
    assert not hasattr(catalog, "promote")
    assert not hasattr(catalog, "register")


def test_parquet_rejects_incompatible_schema(tmp_path: Path) -> None:
    with pytest.raises(RawStorageError, match="schema"):
        ParquetStorage(tmp_path).write(
            "macro", "v1", pa.table({"wrong": ["value"]}), MACRO_OBSERVATIONS.schema
        )


def test_quarantine_preserves_raw_and_report(tmp_path: Path) -> None:
    raw = RawStorage(tmp_path / "raw").persist(
        source=DataSource.OWNER_SUPPLIED,
        dataset="synthetic",
        content=b"invalid synthetic",
        extension="txt",
        media_type="text/plain",
        retrieved_at=NOW,
    )
    storage = QuarantineStorage(tmp_path / "quarantine")
    location = storage.quarantine(raw, "synthetic invalid schema", {"status": "QUARANTINED"})
    assert (location / raw.path.name).read_bytes() == b"invalid synthetic"
    assert (
        json.loads((location / "quarantine.json").read_text())["artifact_checksum"] == raw.checksum
    )
    storage.quarantine(raw, "synthetic invalid schema", {"status": "QUARANTINED"})
    with pytest.raises(RawStorageError, match="collision"):
        storage.quarantine(raw, "changed reason", {"status": "FAIL"})


def test_persisted_lineage_restart_missing_duplicate_and_cycle(tmp_path: Path) -> None:
    store = _lineage(tmp_path / "lineage.json", "dataset")
    assert store.load().artifacts[-1] == "dataset"
    LineageStore(store.path).verify_complete(("source:audit", "raw:audit", "dataset"))
    with pytest.raises(ManifestError, match="missing"):
        store.verify_complete(("not-present",))
    edge = store.load().edges[0]
    duplicate = store.load().model_copy(update={"edges": (edge, edge)})
    with pytest.raises(ManifestError, match="Duplicate"):
        LineageStore._validate(duplicate)
    cycle_edge = edge.model_copy(
        update={"parent_artifact_id": "dataset", "child_artifact_id": "raw:audit"}
    )
    cyclic = store.load().model_copy(update={"edges": (edge, cycle_edge)})
    with pytest.raises(ManifestError, match="cycle"):
        LineageStore._validate(cyclic)
    graph = LineageGraph()
    graph.add("raw")
    graph.add("dataset", ("raw",))
    assert graph.ancestors("dataset") == ("raw",)


def test_dataset_manifest_requires_complete_evidence() -> None:
    with pytest.raises(ValidationError):
        DatasetManifest.model_validate(
            {
                "schema_version": "2.0.0",
                "dataset_id": "incomplete",
                "dataset_type": "macro_observations",
            }
        )


def test_lifecycle_event_journal_is_restart_safe_and_immutable(tmp_path: Path) -> None:
    event = LifecycleEvent.create(
        sequence=1,
        event_id="lifecycle:run:0001:created",
        event_type="CREATED",
        dataset_id="dataset",
        artifact_id="parquet:artifact",
        prior_event_id=None,
        prior_state=None,
        new_state=LifecycleState.CREATED,
        registration_id="catalog:dataset",
        manifest_revision_id="manifest:dataset",
        validation_report_id="validation:report",
        lineage_document_id="lineage:dataset",
        configuration_snapshot_id="config:snapshot",
        catalog_identity="catalog.duckdb",
        run_id="run",
        event_timestamp=NOW,
        code_commit="commit",
        configuration_hash=HASH,
        reason="synthetic failure boundary",
        supporting_evidence_ids=("dataset",),
    )
    store = LifecycleEventStore(tmp_path / "events")
    path = store.persist(event)
    assert LifecycleEventStore(store.root).load() == (event,)
    store.persist(event)
    path.write_text("{}", encoding="utf-8")
    with pytest.raises(ManifestError, match="Invalid lifecycle journal"):
        store.persist(event)
    with pytest.raises(ManifestError, match="Invalid lifecycle journal"):
        store.load()
