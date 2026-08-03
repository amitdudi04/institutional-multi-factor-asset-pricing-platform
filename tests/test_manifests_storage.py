import json
from datetime import UTC, date, datetime
from pathlib import Path

import duckdb
import pyarrow as pa
import pytest
from pydantic import ValidationError

from institutional_factor_platform.data.contracts import MACRO_OBSERVATIONS
from institutional_factor_platform.data.domain import DatasetStatus, DataSource, RetrievalStatus
from institutional_factor_platform.data.lineage import (
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
    PromotionError,
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
        schema_version="2.0.0",
        dataset_id=dataset_id,
        dataset_type="macro_observations",
        schema_name="macro_observations",
        schema_fingerprint=HASH,
        parent_artifacts=("raw:audit",),
        source_manifest_id="source:audit",
        transformation_name="synthetic_standardize",
        transformation_version="2.0.0",
        row_count=1,
        column_count=11,
        primary_key=("series_id", "observation_date"),
        validation_report_id="validation:audit",
        validation_report_path="validation.json",
        validation_status=status,
        lineage_path=str(lineage),
        lineage_complete=complete,
        quarantine_status=status is DatasetStatus.QUARANTINED,
        parquet_path=str(parquet),
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


def test_catalog_validated_only_promotion_and_demotion(tmp_path: Path) -> None:
    artifact = ParquetStorage(tmp_path / "processed").publish(
        "macro_observations", "dataset-audit", _macro_table(), MACRO_OBSERVATIONS.schema
    )
    lineage_path = tmp_path / "lineage.json"
    _lineage(lineage_path, "dataset-audit")
    manifest = _dataset_manifest(artifact.path, artifact.checksum, lineage_path)
    manifest_path = tmp_path / "manifest.json"
    manifest.write_immutable(manifest_path)
    catalog = DuckDBCatalog(tmp_path / "catalog.duckdb")
    catalog.promote(manifest, manifest_path, lineage_path, artifact.path)
    catalog.promote(manifest, manifest_path, lineage_path, artifact.path)
    assert catalog.list_datasets(research_ready_only=True) == [
        ("dataset-audit", "macro_observations", "PASS")
    ]
    catalog.verify_integrity()
    catalog.demote("dataset-audit")
    assert catalog.list_datasets(research_ready_only=True) == []
    with duckdb.connect(str(catalog.path), read_only=True) as connection:
        assert connection.execute(
            "select count(*) from information_schema.views "
            "where table_name='validated_macro_observations'"
        ).fetchone() == (0,)


@pytest.mark.parametrize("status", [DatasetStatus.FAIL, DatasetStatus.QUARANTINED])
def test_failed_and_quarantined_cannot_promote(tmp_path: Path, status: DatasetStatus) -> None:
    artifact = ParquetStorage(tmp_path / "processed").publish(
        "macro_observations", "blocked", _macro_table(), MACRO_OBSERVATIONS.schema
    )
    lineage_path = tmp_path / "lineage.json"
    _lineage(lineage_path, "blocked")
    manifest = _dataset_manifest(
        artifact.path, artifact.checksum, lineage_path, dataset_id="blocked", status=status
    )
    path = tmp_path / "manifest.json"
    manifest.write_immutable(path)
    catalog = DuckDBCatalog(tmp_path / "catalog.duckdb")
    catalog.register(manifest, path)
    with pytest.raises(PromotionError, match="not research-ready"):
        catalog.promote(manifest, path, lineage_path, artifact.path)
    assert catalog.list_datasets(research_ready_only=True) == []


def test_missing_checksum_or_lineage_blocks_promotion(tmp_path: Path) -> None:
    artifact = ParquetStorage(tmp_path / "processed").publish(
        "macro_observations", "dataset-audit", _macro_table(), MACRO_OBSERVATIONS.schema
    )
    lineage_path = tmp_path / "lineage.json"
    _lineage(lineage_path, "dataset-audit")
    manifest = _dataset_manifest(artifact.path, "b" * 64, lineage_path)
    path = tmp_path / "manifest.json"
    manifest.write_immutable(path)
    catalog = DuckDBCatalog(tmp_path / "catalog.duckdb")
    with pytest.raises(PromotionError, match="checksum"):
        catalog.promote(manifest, path, lineage_path, artifact.path)
    incomplete = _dataset_manifest(artifact.path, artifact.checksum, lineage_path, complete=False)
    incomplete_path = tmp_path / "incomplete.json"
    incomplete.write_immutable(incomplete_path)
    with pytest.raises(PromotionError, match="complete lineage"):
        catalog.promote(incomplete, incomplete_path, lineage_path, artifact.path)


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
