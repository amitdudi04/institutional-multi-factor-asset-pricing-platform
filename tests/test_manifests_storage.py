from datetime import UTC, datetime
from pathlib import Path

import pyarrow as pa
import pytest

from institutional_factor_platform.data.contracts import MACRO_OBSERVATIONS
from institutional_factor_platform.data.domain import DatasetStatus, DataSource, RetrievalStatus
from institutional_factor_platform.data.lineage import LineageGraph
from institutional_factor_platform.data.manifests import DatasetManifest, SourceManifest
from institutional_factor_platform.data.storage import (
    DuckDBCatalog,
    ParquetStorage,
    QuarantineStorage,
    RawStorage,
    sha256_file,
)
from institutional_factor_platform.exceptions import (
    CatalogError,
    ChecksumMismatchError,
    ManifestError,
    RawStorageError,
)


def test_manifest_hash_and_immutable_write(tmp_path: Path) -> None:
    manifest = SourceManifest(
        schema_version="1.0.0",
        source="owner_supplied",
        request={"dataset": "synthetic_test"},
        retrieval_time=datetime(2024, 1, 1, tzinfo=UTC),
        response_status=RetrievalStatus.SUCCESS,
        source_terms_note="Synthetic test fixture only.",
    )
    path = tmp_path / "source.json"
    manifest.write_immutable(path)
    assert len(manifest.content_hash()) == 64
    manifest.write_immutable(path)
    path.write_text("different", encoding="utf-8")
    with pytest.raises(ManifestError, match="overwrite"):
        manifest.write_immutable(path)


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


def _macro_table() -> pa.Table:
    return pa.Table.from_pylist(
        [
            {
                "series_id": "SYNTHETIC_TEST_SERIES",
                "observation_date": __import__("datetime").date(2024, 1, 2),
                "value": 1.25,
                "source_unit": "test units",
                "frequency": "daily",
                "seasonal_adjustment": None,
                "source": "owner_supplied",
                "retrieval_timestamp": datetime(2024, 1, 3, tzinfo=UTC),
                "availability_timestamp": None,
                "missing_value": False,
                "schema_version": "1.0.0",
            }
        ],
        schema=MACRO_OBSERVATIONS.schema,
    )


def test_parquet_and_catalog_are_verified_and_idempotent(tmp_path: Path) -> None:
    table = _macro_table()
    parquet, checksum = ParquetStorage(tmp_path / "processed").write(
        "macro_observations", "version-1", table, MACRO_OBSERVATIONS.schema
    )
    assert sha256_file(parquet) == checksum
    manifest = tmp_path / "manifest.json"
    manifest.write_text("{}", encoding="utf-8")
    catalog = DuckDBCatalog(tmp_path / "catalog.duckdb")
    catalog.register("dataset-1", "macro_observations", parquet, manifest, "PASS")
    catalog.register("dataset-1", "macro_observations", parquet, manifest, "PASS")
    assert catalog.list_datasets() == [("dataset-1", "macro_observations", "PASS")]
    with pytest.raises(CatalogError, match="different"):
        catalog.register("dataset-1", "macro_observations", parquet, tmp_path / "other", "PASS")


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
        retrieved_at=datetime(2024, 1, 1, tzinfo=UTC),
    )
    location = QuarantineStorage(tmp_path / "quarantine").quarantine(
        raw, "synthetic invalid schema", {"status": "QUARANTINED"}
    )
    assert (location / raw.path.name).read_bytes() == b"invalid synthetic"
    assert (location / "quarantine.json").is_file()
    QuarantineStorage(tmp_path / "quarantine").quarantine(
        raw, "synthetic invalid schema", {"status": "QUARANTINED"}
    )
    with pytest.raises(RawStorageError, match="collision"):
        QuarantineStorage(tmp_path / "quarantine").quarantine(
            raw, "changed reason", {"status": "FAIL"}
        )


def test_lineage_rejects_cycles_and_finds_ancestors() -> None:
    graph = LineageGraph()
    graph.add("raw")
    graph.add("standard", ("raw",))
    graph.add("dataset", ("standard",))
    assert graph.ancestors("dataset") == ("raw", "standard")
    with pytest.raises(ManifestError, match="cycle"):
        graph.add("raw", ("dataset",))


def test_dataset_manifest_validation() -> None:
    manifest = DatasetManifest(
        schema_version="1.0.0",
        dataset_id="synthetic-id",
        dataset_type="macro_observations",
        schema_name="macro_observations",
        parent_artifacts=("abc",),
        transformation_name="synthetic_standardize",
        transformation_version="1.0.0",
        row_count=1,
        column_count=11,
        primary_key=("series_id", "observation_date"),
        validation_status=DatasetStatus.PASS,
        quarantine_status=False,
        creation_time=datetime(2024, 1, 1, tzinfo=UTC),
        configuration_hash="hash",
        code_version="test",
    )
    assert manifest.row_count == 1
