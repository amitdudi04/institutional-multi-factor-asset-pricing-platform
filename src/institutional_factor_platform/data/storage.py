"""Immutable raw/Parquet storage, quarantine, and validated-only DuckDB catalog."""

import hashlib
import json
import os
import shutil
import tempfile
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, ClassVar

import duckdb
import pyarrow as pa
import pyarrow.parquet as pq

from institutional_factor_platform.data.domain import DataArtifact, DatasetStatus, DataSource
from institutional_factor_platform.data.lineage import LineageStore
from institutional_factor_platform.data.manifests import DatasetManifest, PromotionManifest
from institutional_factor_platform.exceptions import (
    CatalogError,
    ChecksumMismatchError,
    PromotionError,
    PublicationConflictError,
    RawStorageError,
)


def sha256_bytes(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


@dataclass(frozen=True, slots=True)
class PublishedArtifact:
    artifact_id: str
    path: Path
    checksum: str
    byte_size: int
    reused: bool


class RawStorage:
    def __init__(self, root: Path) -> None:
        self.root = root

    def persist(
        self,
        *,
        source: DataSource,
        dataset: str,
        content: bytes,
        extension: str,
        media_type: str,
        retrieved_at: datetime,
    ) -> DataArtifact:
        if retrieved_at.tzinfo is None:
            raise RawStorageError("Raw retrieval timestamp must be timezone-aware.")
        checksum = sha256_bytes(content)
        safe_dataset = "".join(ch for ch in dataset if ch.isalnum() or ch in "-_")
        if not safe_dataset:
            raise RawStorageError("Dataset name has no safe path characters.")
        stamp = retrieved_at.astimezone(UTC)
        directory = self.root / source.value / safe_dataset / stamp.strftime("%Y/%m/%d")
        directory.mkdir(parents=True, exist_ok=True)
        path = directory / (
            f"{stamp.strftime('%Y%m%dT%H%M%S%fZ')}_{checksum[:16]}.{extension.lstrip('.')}"
        )
        if path.exists():
            if sha256_file(path) != checksum:
                raise ChecksumMismatchError(f"Existing raw artifact checksum mismatch: {path}")
        else:
            _atomic_bytes(path, content, ".raw-")
        return DataArtifact(path, checksum, len(content), media_type, source, retrieved_at)

    @staticmethod
    def verify(artifact: DataArtifact) -> None:
        if not artifact.path.is_file() or sha256_file(artifact.path) != artifact.checksum:
            raise ChecksumMismatchError(f"Raw artifact failed checksum validation: {artifact.path}")


class ParquetStorage:
    def __init__(self, root: Path, compression: str = "zstd") -> None:
        self.root = root
        self.compression = compression

    def publish(
        self,
        dataset: str,
        artifact_id: str,
        table: pa.Table,
        schema: pa.Schema,
    ) -> PublishedArtifact:
        if not table.schema.equals(schema, check_metadata=False):
            raise RawStorageError(f"Table does not exactly match schema for {dataset}.")
        safe_id = "".join(ch for ch in artifact_id if ch.isalnum() or ch in "-_")
        if not safe_id or safe_id != artifact_id:
            raise RawStorageError("Standardized artifact ID contains unsafe characters.")
        path = self.root / dataset / artifact_id / "data.parquet"
        path.parent.mkdir(parents=True, exist_ok=True)
        descriptor, temporary_name = tempfile.mkstemp(
            dir=path.parent, prefix=".parquet-", suffix=".tmp"
        )
        os.close(descriptor)
        temporary = Path(temporary_name)
        try:
            pq.write_table(table, temporary, compression=self.compression)
            # Best effort: Windows/filesystem combinations may not support fsync on this handle.
            try:
                descriptor = os.open(temporary, os.O_RDONLY)
                try:
                    os.fsync(descriptor)
                finally:
                    os.close(descriptor)
            except OSError:
                pass
            check = pq.read_table(temporary)
            if (
                not check.schema.equals(schema, check_metadata=False)
                or check.num_rows != table.num_rows
            ):
                raise RawStorageError(f"Parquet verification failed for {path}")
            checksum = sha256_file(temporary)
            size = temporary.stat().st_size
            if path.exists():
                existing = sha256_file(path)
                if existing != checksum:
                    raise PublicationConflictError(
                        f"Immutable Parquet identity already has different content: {artifact_id}"
                    )
                return PublishedArtifact(artifact_id, path, checksum, size, True)
            os.replace(temporary, path)
            return PublishedArtifact(artifact_id, path, checksum, size, False)
        finally:
            temporary.unlink(missing_ok=True)

    @staticmethod
    def verify(artifact: PublishedArtifact) -> None:
        if not artifact.path.is_file() or sha256_file(artifact.path) != artifact.checksum:
            raise ChecksumMismatchError(
                f"Standardized artifact failed checksum verification: {artifact.path}"
            )

    # Compatibility wrapper: still immutable, but callers should use publish with a full identity.
    def write(
        self, dataset: str, version: str, table: pa.Table, schema: pa.Schema
    ) -> tuple[Path, str]:
        artifact = self.publish(dataset, version, table, schema)
        return artifact.path, artifact.checksum


class QuarantineStorage:
    def __init__(self, root: Path) -> None:
        self.root = root

    def quarantine(self, artifact: DataArtifact, reason: str, report: dict[str, Any]) -> Path:
        RawStorage.verify(artifact)
        destination = self.root / artifact.source.value / artifact.checksum
        destination.mkdir(parents=True, exist_ok=True)
        raw_copy = destination / artifact.path.name
        if raw_copy.exists() and sha256_file(raw_copy) != artifact.checksum:
            raise ChecksumMismatchError(f"Quarantine artifact collision: {raw_copy}")
        if not raw_copy.exists():
            shutil.copy2(artifact.path, raw_copy)
        payload = {"reason": reason, "artifact_checksum": artifact.checksum, "report": report}
        report_path = destination / "quarantine.json"
        content = json.dumps(payload, sort_keys=True, indent=2) + "\n"
        if report_path.exists() and report_path.read_text(encoding="utf-8") != content:
            raise RawStorageError(f"Quarantine report collision: {report_path}")
        if not report_path.exists():
            _atomic_bytes(report_path, content.encode(), ".quarantine-")
        return destination


class DuckDBCatalog:
    ELIGIBLE: ClassVar[set[str]] = {
        DatasetStatus.PASS.value,
        DatasetStatus.PASS_WITH_WARNINGS.value,
    }

    def __init__(self, path: Path) -> None:
        self.path = path

    def initialize(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with duckdb.connect(str(self.path)) as connection:
            connection.execute(
                """CREATE TABLE IF NOT EXISTS catalog_metadata
                   (schema_version VARCHAR PRIMARY KEY)"""
            )
            versions = connection.execute("SELECT schema_version FROM catalog_metadata").fetchall()
            if versions and versions != [("2.0.0",)]:
                raise CatalogError("Unsupported DuckDB catalog schema; rebuild the local catalog.")
            connection.execute("INSERT OR IGNORE INTO catalog_metadata VALUES ('2.0.0')")
            connection.execute(
                """CREATE TABLE IF NOT EXISTS dataset_registry (
                dataset_id VARCHAR PRIMARY KEY, dataset_type VARCHAR NOT NULL,
                parquet_path VARCHAR NOT NULL, output_checksum VARCHAR NOT NULL,
                manifest_path VARCHAR NOT NULL, lineage_path VARCHAR NOT NULL,
                validation_status VARCHAR NOT NULL,
                promoted BOOLEAN NOT NULL DEFAULT FALSE,
                registered_at TIMESTAMPTZ NOT NULL)"""
            )

    def register(self, manifest: DatasetManifest, manifest_path: Path) -> None:
        """Register lifecycle metadata without creating research-ready visibility."""
        self.initialize()
        values = (
            manifest.dataset_type,
            manifest.parquet_path,
            manifest.output_checksum,
            str(manifest_path),
            manifest.lineage_path,
            manifest.validation_status.value,
        )
        try:
            with duckdb.connect(str(self.path)) as connection:
                existing = connection.execute(
                    "SELECT dataset_type, parquet_path, output_checksum, validation_status "
                    "FROM dataset_registry WHERE dataset_id = ?",
                    [manifest.dataset_id],
                ).fetchone()
                immutable_values = (values[0], values[1], values[2], values[5])
                if existing is not None and tuple(existing) != immutable_values:
                    raise CatalogError(
                        f"Dataset ID already maps to different evidence: {manifest.dataset_id}"
                    )
                if existing is None:
                    connection.execute(
                        "INSERT INTO dataset_registry VALUES (?, ?, ?, ?, ?, ?, ?, FALSE, ?)",
                        [manifest.dataset_id, *values, datetime.now(UTC)],
                    )
        except duckdb.Error as exc:
            raise CatalogError(
                f"DuckDB registration failed for {manifest.dataset_id}: {exc}"
            ) from exc

    def promote(
        self,
        manifest: DatasetManifest,
        manifest_path: Path,
        lineage_path: Path,
        parquet_path: Path,
    ) -> None:
        """Promote only complete, checksum-verified, eligible evidence transactionally."""
        if manifest.validation_status.value not in self.ELIGIBLE:
            raise PromotionError(
                f"Status is not research-ready: {manifest.validation_status.value}"
            )
        if not manifest.lineage_complete or manifest.promotion_state != "ELIGIBLE":
            raise PromotionError("Promotion requires complete lineage and ELIGIBLE manifest state.")
        if not manifest_path.is_file() or not lineage_path.is_file() or not parquet_path.is_file():
            raise PromotionError("Promotion evidence file is missing.")
        if sha256_file(parquet_path) != manifest.output_checksum:
            raise PromotionError("Parquet checksum does not match dataset manifest.")
        LineageStore(lineage_path).verify_complete(
            (manifest.source_manifest_id, *manifest.parent_artifacts, manifest.dataset_id)
        )
        runtime_manifest = manifest.model_copy(
            update={"parquet_path": str(parquet_path), "lineage_path": str(lineage_path)}
        )
        self.register(runtime_manifest, manifest_path)
        try:
            with duckdb.connect(str(self.path)) as connection:
                connection.execute("BEGIN TRANSACTION")
                connection.execute(
                    "UPDATE dataset_registry SET promoted = TRUE WHERE dataset_id = ?",
                    [manifest.dataset_id],
                )
                self._rebuild_view(connection, manifest.dataset_type)
                connection.execute("COMMIT")
        except duckdb.Error as exc:
            raise PromotionError(
                f"DuckDB promotion failed for {manifest.dataset_id}: {exc}"
            ) from exc

    def demote(self, dataset_id: str) -> None:
        self.initialize()
        with duckdb.connect(str(self.path)) as connection:
            row = connection.execute(
                "SELECT dataset_type FROM dataset_registry WHERE dataset_id = ?", [dataset_id]
            ).fetchone()
            if row is None:
                return
            connection.execute("BEGIN TRANSACTION")
            connection.execute(
                "UPDATE dataset_registry SET promoted = FALSE WHERE dataset_id = ?", [dataset_id]
            )
            self._rebuild_view(connection, str(row[0]))
            connection.execute("COMMIT")

    def _rebuild_view(self, connection: Any, dataset_type: str) -> None:
        view = _safe_identifier(f"validated_{dataset_type}")
        rows = connection.execute(
            "SELECT parquet_path FROM dataset_registry WHERE dataset_type = ? "
            "AND promoted = TRUE AND validation_status IN ('PASS', 'PASS_WITH_WARNINGS') "
            "ORDER BY dataset_id",
            [dataset_type],
        ).fetchall()
        connection.execute(f'DROP VIEW IF EXISTS "{view}"')
        if rows:
            paths = ", ".join("'" + str(row[0]).replace("'", "''") + "'" for row in rows)
            connection.execute(f'CREATE VIEW "{view}" AS SELECT * FROM read_parquet([{paths}])')

    def list_datasets(self, *, research_ready_only: bool = False) -> list[tuple[str, str, str]]:
        self.initialize()
        clause = " WHERE promoted = TRUE" if research_ready_only else ""
        with duckdb.connect(str(self.path), read_only=True) as connection:
            rows = connection.execute(
                "SELECT dataset_id, dataset_type, validation_status FROM dataset_registry"
                + clause
                + " ORDER BY dataset_id"
            ).fetchall()
            return [(str(row[0]), str(row[1]), str(row[2])) for row in rows]

    def verify_integrity(self) -> None:
        self.initialize()
        with duckdb.connect(str(self.path), read_only=True) as connection:
            rows = connection.execute(
                "SELECT parquet_path, output_checksum, manifest_path, lineage_path "
                "FROM dataset_registry WHERE promoted = TRUE"
            ).fetchall()
        for parquet_value, checksum, manifest_value, lineage_value in rows:
            parquet_path = Path(str(parquet_value))
            if (
                not parquet_path.is_file()
                or sha256_file(parquet_path) != checksum
                or not Path(str(manifest_value)).is_file()
                or not Path(str(lineage_value)).is_file()
            ):
                raise PromotionError("Catalog contains broken promoted evidence.")

    @classmethod
    def rebuild_from_manifests(
        cls, target: Path, manifests_root: Path, project_root: Path
    ) -> "DuckDBCatalog":
        """Explicitly rebuild a new disposable catalog from v2 promotion evidence."""
        if target.exists():
            raise CatalogError(f"Catalog rebuild target already exists: {target}")
        catalog = cls(target)
        for promotion_path in sorted(manifests_root.rglob("promotion.json")):
            promotion = PromotionManifest.model_validate_json(
                promotion_path.read_text(encoding="utf-8")
            )
            manifest_path = _resolve_evidence_path(promotion.dataset_manifest_path, project_root)
            manifest = DatasetManifest.model_validate_json(
                manifest_path.read_text(encoding="utf-8")
            )
            if manifest.content_hash() != promotion.dataset_manifest_hash:
                raise PromotionError("Promotion references a changed dataset manifest.")
            lineage_path = _resolve_evidence_path(manifest.lineage_path, project_root)
            parquet_path = _resolve_evidence_path(manifest.parquet_path, project_root)
            catalog.promote(manifest, manifest_path, lineage_path, parquet_path)
        catalog.verify_integrity()
        return catalog


def _atomic_bytes(path: Path, content: bytes, prefix: str) -> None:
    descriptor, temporary = tempfile.mkstemp(dir=path.parent, prefix=prefix, suffix=".tmp")
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        Path(temporary).unlink(missing_ok=True)


def _safe_identifier(value: str) -> str:
    safe = "".join(ch if ch.isalnum() or ch == "_" else "_" for ch in value)
    if not safe:
        raise CatalogError("DuckDB identifier is empty after normalization.")
    return safe


def _resolve_evidence_path(value: str, project_root: Path) -> Path:
    path = Path(value)
    return path.resolve() if path.is_absolute() else (project_root / path).resolve()
