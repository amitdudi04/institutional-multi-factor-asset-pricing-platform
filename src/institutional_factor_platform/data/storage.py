"""Immutable raw, atomic Parquet, quarantine, and DuckDB storage."""

import hashlib
import json
import os
import shutil
import tempfile
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import duckdb
import pyarrow as pa
import pyarrow.parquet as pq

from institutional_factor_platform.data.domain import DataArtifact, DataSource
from institutional_factor_platform.exceptions import (
    CatalogError,
    ChecksumMismatchError,
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
        path = (
            directory
            / f"{stamp.strftime('%Y%m%dT%H%M%S%fZ')}_{checksum[:16]}.{extension.lstrip('.')}"
        )
        if path.exists():
            if sha256_file(path) != checksum:
                raise ChecksumMismatchError(f"Existing raw artifact checksum mismatch: {path}")
        else:
            self._atomic_bytes(path, content)
        return DataArtifact(path, checksum, len(content), media_type, source, retrieved_at)

    @staticmethod
    def verify(artifact: DataArtifact) -> None:
        if not artifact.path.is_file() or sha256_file(artifact.path) != artifact.checksum:
            raise ChecksumMismatchError(f"Raw artifact failed checksum validation: {artifact.path}")

    @staticmethod
    def _atomic_bytes(path: Path, content: bytes) -> None:
        descriptor, temporary = tempfile.mkstemp(dir=path.parent, prefix=".raw-", suffix=".tmp")
        try:
            with os.fdopen(descriptor, "wb") as handle:
                handle.write(content)
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temporary, path)
        finally:
            Path(temporary).unlink(missing_ok=True)


class ParquetStorage:
    def __init__(self, root: Path, compression: str = "zstd") -> None:
        self.root = root
        self.compression = compression

    def write(
        self, dataset: str, version: str, table: pa.Table, schema: pa.Schema
    ) -> tuple[Path, str]:
        if not table.schema.equals(schema, check_metadata=False):
            try:
                table = table.cast(schema)
            except (ValueError, pa.ArrowInvalid, pa.ArrowNotImplementedError) as exc:
                raise RawStorageError(f"Table does not match schema for {dataset}: {exc}") from exc
        path = self.root / dataset / version / "data.parquet"
        path.parent.mkdir(parents=True, exist_ok=True)
        temporary = path.with_name(f".{path.name}.tmp")
        pq.write_table(table, temporary, compression=self.compression)
        check = pq.read_table(temporary)
        if check.num_rows != table.num_rows or check.column_names != table.column_names:
            temporary.unlink(missing_ok=True)
            raise RawStorageError(f"Parquet verification failed for {path}")
        os.replace(temporary, path)
        return path, sha256_file(path)


class QuarantineStorage:
    def __init__(self, root: Path) -> None:
        self.root = root

    def quarantine(self, artifact: DataArtifact, reason: str, report: dict[str, Any]) -> Path:
        destination = self.root / artifact.source.value / artifact.checksum
        destination.mkdir(parents=True, exist_ok=True)
        raw_copy = destination / artifact.path.name
        if not raw_copy.exists():
            shutil.copy2(artifact.path, raw_copy)
        payload = {"reason": reason, "artifact_checksum": artifact.checksum, "report": report}
        report_path = destination / "quarantine.json"
        content = json.dumps(payload, sort_keys=True, indent=2) + "\n"
        if report_path.exists() and report_path.read_text(encoding="utf-8") != content:
            raise RawStorageError(f"Quarantine report collision: {report_path}")
        report_path.write_text(content, encoding="utf-8")
        return destination


class DuckDBCatalog:
    def __init__(self, path: Path) -> None:
        self.path = path

    def initialize(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with duckdb.connect(str(self.path)) as connection:
            connection.execute(
                """CREATE TABLE IF NOT EXISTS dataset_registry (
                dataset_id VARCHAR PRIMARY KEY, dataset_type VARCHAR NOT NULL,
                parquet_path VARCHAR NOT NULL, manifest_path VARCHAR NOT NULL,
                validation_status VARCHAR NOT NULL, registered_at TIMESTAMPTZ NOT NULL)"""
            )

    def register(
        self,
        dataset_id: str,
        dataset_type: str,
        parquet_path: Path,
        manifest_path: Path,
        validation_status: str,
    ) -> None:
        self.initialize()
        try:
            with duckdb.connect(str(self.path)) as connection:
                connection.execute("BEGIN TRANSACTION")
                existing = connection.execute(
                    "SELECT parquet_path, manifest_path FROM dataset_registry WHERE dataset_id = ?",
                    [dataset_id],
                ).fetchone()
                values = (str(parquet_path), str(manifest_path))
                if existing is not None and tuple(existing) != values:
                    raise CatalogError(
                        f"Dataset ID already maps to different artifacts: {dataset_id}"
                    )
                if existing is None:
                    connection.execute(
                        "INSERT INTO dataset_registry VALUES (?, ?, ?, ?, ?, ?)",
                        [dataset_id, dataset_type, *values, validation_status, datetime.now(UTC)],
                    )
                    view = _safe_identifier(f"validated_{dataset_type}")
                    parquet_sql = str(parquet_path).replace("'", "''")
                    connection.execute(
                        f'CREATE OR REPLACE VIEW "{view}" '
                        f"AS SELECT * FROM read_parquet('{parquet_sql}')"
                    )
                connection.execute("COMMIT")
        except duckdb.Error as exc:
            raise CatalogError(f"DuckDB registration failed for {dataset_id}: {exc}") from exc

    def list_datasets(self) -> list[tuple[str, str, str]]:
        self.initialize()
        with duckdb.connect(str(self.path), read_only=True) as connection:
            rows = connection.execute(
                "SELECT dataset_id, dataset_type, validation_status "
                "FROM dataset_registry ORDER BY dataset_id"
            ).fetchall()
            return [(str(row[0]), str(row[1]), str(row[2])) for row in rows]


def _safe_identifier(value: str) -> str:
    safe = "".join(ch if ch.isalnum() or ch == "_" else "_" for ch in value)
    if not safe:
        raise CatalogError("DuckDB identifier is empty after normalization.")
    return safe
