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
from institutional_factor_platform.data.lineage import LineageStore, RelationshipType
from institutional_factor_platform.data.manifests import (
    DatasetManifest,
    PromotionManifest,
    SourceManifest,
)
from institutional_factor_platform.exceptions import (
    CatalogError,
    ChecksumMismatchError,
    EvidenceIntegrityError,
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
            if versions and versions != [("3.0.0",)]:
                raise CatalogError("Unsupported DuckDB catalog schema; rebuild the local catalog.")
            connection.execute("INSERT OR IGNORE INTO catalog_metadata VALUES ('3.0.0')")
            connection.execute(
                """CREATE TABLE IF NOT EXISTS dataset_registry (
                dataset_id VARCHAR PRIMARY KEY, dataset_type VARCHAR NOT NULL,
                parquet_path VARCHAR NOT NULL, output_checksum VARCHAR NOT NULL,
                manifest_path VARCHAR NOT NULL, lineage_path VARCHAR NOT NULL,
                validation_status VARCHAR NOT NULL,
                promoted BOOLEAN NOT NULL DEFAULT FALSE,
                registered_at TIMESTAMPTZ NOT NULL)"""
            )

    def register_persisted(
        self, dataset_id: str, manifest_path: Path, project_root: Path
    ) -> DatasetManifest:
        """Register only an authenticated persisted REGISTERED manifest revision."""
        manifest = authenticate_dataset_evidence(dataset_id, manifest_path, project_root)
        if manifest.catalog_registration_state != "REGISTERED":
            raise EvidenceIntegrityError("Registration requires a REGISTERED manifest revision.")
        if manifest.promotion_state != "ELIGIBLE":
            raise EvidenceIntegrityError("Registration requires an ELIGIBLE manifest revision.")
        self.initialize()
        parquet_path = _resolve_evidence_path(manifest.parquet_path, project_root)
        lineage_path = _resolve_evidence_path(manifest.lineage_path, project_root)
        values = (
            manifest.dataset_type,
            str(parquet_path),
            manifest.output_checksum,
            str(manifest_path),
            str(lineage_path),
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
        return manifest

    def promote_persisted(
        self, dataset_id: str, manifest_path: Path, project_root: Path
    ) -> DatasetManifest:
        """Promote by reloading a fully authenticated persisted PUBLISHED revision."""
        manifest = authenticate_dataset_evidence(dataset_id, manifest_path, project_root)
        if manifest.catalog_registration_state != "REGISTERED":
            raise EvidenceIntegrityError("Promotion requires registered persisted state.")
        if manifest.promotion_state != "PUBLISHED":
            raise EvidenceIntegrityError("Promotion requires a PUBLISHED manifest revision.")
        self.initialize()
        try:
            with duckdb.connect(str(self.path)) as connection:
                existing = connection.execute(
                    "SELECT dataset_type, output_checksum, promoted FROM dataset_registry "
                    "WHERE dataset_id = ?",
                    [dataset_id],
                ).fetchone()
                if (
                    existing is None
                    or str(existing[0]) != manifest.dataset_type
                    or str(existing[1]) != manifest.output_checksum
                ):
                    raise EvidenceIntegrityError(
                        "Catalog registration does not match persisted evidence."
                    )
                connection.execute("BEGIN TRANSACTION")
                connection.execute(
                    "UPDATE dataset_registry SET promoted = TRUE, "
                    "manifest_path = ?, lineage_path = ? "
                    "WHERE dataset_id = ?",
                    [
                        str(manifest_path),
                        str(_resolve_evidence_path(manifest.lineage_path, project_root)),
                        dataset_id,
                    ],
                )
                self._rebuild_view(connection, manifest.dataset_type)
                connection.execute("COMMIT")
        except duckdb.Error as exc:
            raise PromotionError(
                f"DuckDB promotion failed for {manifest.dataset_id}: {exc}"
            ) from exc
        return manifest

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

    def verify_integrity(self, project_root: Path | None = None) -> None:
        self.initialize()
        with duckdb.connect(str(self.path), read_only=True) as connection:
            rows = connection.execute(
                "SELECT parquet_path, output_checksum, manifest_path, lineage_path "
                "FROM dataset_registry WHERE promoted = TRUE"
            ).fetchall()
        root = (project_root or Path.cwd()).resolve()
        for parquet_value, checksum, manifest_value, lineage_value in rows:
            manifest_path = Path(str(manifest_value))
            if not manifest_path.is_file():
                raise EvidenceIntegrityError("Catalog references a missing dataset manifest.")
            persisted = DatasetManifest.model_validate_json(
                manifest_path.read_text(encoding="utf-8")
            )
            authenticate_dataset_evidence(persisted.dataset_id, manifest_path, root)
            if str(_resolve_evidence_path(persisted.parquet_path, root)) != str(parquet_value):
                raise EvidenceIntegrityError(
                    "Catalog Parquet path differs from persisted manifest."
                )
            if persisted.output_checksum != checksum:
                raise EvidenceIntegrityError("Catalog checksum differs from persisted manifest.")
            if str(_resolve_evidence_path(persisted.lineage_path, root)) != str(lineage_value):
                raise EvidenceIntegrityError(
                    "Catalog lineage path differs from persisted manifest."
                )
            if persisted.promotion_state != "PUBLISHED":
                raise EvidenceIntegrityError(
                    "Promoted catalog row references stale manifest state."
                )

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
            registered_path = manifest_path.with_name("dataset-registered.json")
            catalog.register_persisted(manifest.dataset_id, registered_path, project_root)
            catalog.promote_persisted(manifest.dataset_id, manifest_path, project_root)
        catalog.verify_integrity(project_root)
        return catalog


def authenticate_dataset_evidence(
    dataset_id: str, manifest_path: Path, project_root: Path
) -> DatasetManifest:
    """Load and cryptographically cross-check every persisted promotion authority."""
    try:
        manifest = DatasetManifest.model_validate_json(manifest_path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise EvidenceIntegrityError(f"Invalid persisted dataset manifest: {exc}") from exc
    if manifest.dataset_id != dataset_id:
        raise EvidenceIntegrityError("Persisted manifest dataset ID does not match request.")
    if not manifest.git_commit.strip() or manifest.git_commit == "unavailable":
        raise EvidenceIntegrityError("Persisted manifest lacks a verifiable Git commit.")
    evidence = (
        (manifest.validation_report_path, manifest.validation_report_checksum, "validation report"),
        (manifest.lineage_path, manifest.lineage_checksum, "lineage"),
        (manifest.parquet_path, manifest.output_checksum, "Parquet"),
        (
            manifest.configuration_snapshot_path,
            manifest.configuration_snapshot_checksum,
            "configuration snapshot",
        ),
        (manifest.source_manifest_path, manifest.source_manifest_checksum, "source manifest"),
    )
    resolved: dict[str, Path] = {}
    for value, expected, label in evidence:
        path = _resolve_evidence_path(value, project_root)
        if not path.is_file() or sha256_file(path) != expected:
            raise EvidenceIntegrityError(
                f"Persisted {label} is missing or has a checksum mismatch."
            )
        resolved[label] = path
    try:
        report = json.loads(resolved["validation report"].read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise EvidenceIntegrityError(f"Invalid validation report: {exc}") from exc
    if report.get("dataset_id") != dataset_id or report.get("run_id") != manifest.run_id:
        raise EvidenceIntegrityError("Validation report identity does not match manifest.")
    if report.get("final_status") != manifest.validation_status.value:
        raise EvidenceIntegrityError("Validation status differs from persisted report.")
    if any(item.get("severity") in {"ERROR", "CRITICAL"} for item in report.get("results", [])):
        raise EvidenceIntegrityError("Validation report contains blocking findings.")
    if manifest.validation_status.value not in DuckDBCatalog.ELIGIBLE:
        raise EvidenceIntegrityError("Persisted validation status is not promotion eligible.")
    lineage = LineageStore(resolved["lineage"]).load()
    if (
        lineage.schema_version != "3.0.0"
        or lineage.dataset_id != dataset_id
        or lineage.run_id != manifest.run_id
    ):
        raise EvidenceIntegrityError("Lineage identity does not match manifest.")
    required = {
        manifest.source_manifest_id,
        *manifest.parent_artifacts,
        manifest.output_artifact_id,
        dataset_id,
    }
    if not required.issubset(set(lineage.artifacts)):
        raise EvidenceIntegrityError("Lineage is incomplete for persisted publication evidence.")
    if manifest.promotion_state == "PUBLISHED":
        relationships = {edge.relationship_type for edge in lineage.edges}
        needed = {
            RelationshipType.REGISTERED_IN_CATALOG,
            RelationshipType.PROMOTED_TO_RESEARCH_READY,
        }
        if not needed.issubset(relationships):
            raise EvidenceIntegrityError("Published lineage lacks registration or promotion event.")
    parquet = resolved["Parquet"]
    if parquet.stat().st_size != manifest.output_byte_size:
        raise EvidenceIntegrityError("Parquet byte size differs from manifest.")
    try:
        fingerprint = hashlib.sha256(pq.read_schema(parquet).serialize().to_pybytes()).hexdigest()
    except (OSError, pa.ArrowException) as exc:
        raise EvidenceIntegrityError(f"Parquet schema cannot be verified: {exc}") from exc
    if fingerprint != manifest.schema_fingerprint:
        raise EvidenceIntegrityError("Parquet schema fingerprint differs from manifest.")
    try:
        source = SourceManifest.model_validate_json(
            resolved["source manifest"].read_text(encoding="utf-8")
        )
    except (OSError, ValueError) as exc:
        raise EvidenceIntegrityError(f"Invalid source manifest: {exc}") from exc
    if (
        source.source_manifest_id != manifest.source_manifest_id
        or not source.raw_artifact_path
        or not source.checksum
    ):
        raise EvidenceIntegrityError("Source manifest identity or raw evidence is incomplete.")
    raw_path = _resolve_evidence_path(source.raw_artifact_path, project_root)
    if not raw_path.is_file() or sha256_file(raw_path) != source.checksum:
        raise EvidenceIntegrityError("Parent raw artifact is missing or has changed.")
    return manifest


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
