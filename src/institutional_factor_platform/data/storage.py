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
from institutional_factor_platform.data.evidence import canonical_json_bytes, resolve_project_path
from institutional_factor_platform.data.lineage import (
    LifecycleEvent,
    LifecycleEventStore,
    LifecycleState,
    LineageStore,
    RelationshipType,
)
from institutional_factor_platform.data.manifests import (
    DatasetManifest,
    PromotionManifest,
    RunManifest,
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
            # An explicit stream lifetime is required on Windows. Passing the path directly can
            # leave PyArrow's dataset reader holding the temporary file when atomic replacement
            # begins, causing a spurious sharing-violation despite successful verification.
            with temporary.open("rb") as stream:
                check = pq.read_table(stream)
            if (
                not check.schema.equals(schema, check_metadata=False)
                or check.num_rows != table.num_rows
            ):
                raise RawStorageError(f"Parquet verification failed for {path}")
            del check
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

    def __init__(self, path: Path, project_root: Path | None = None) -> None:
        self.path = path
        self.project_root = project_root.resolve() if project_root else None

    def initialize(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with duckdb.connect(str(self.path)) as connection:
            connection.execute(
                """CREATE TABLE IF NOT EXISTS catalog_metadata
                   (schema_version VARCHAR PRIMARY KEY)"""
            )
            versions = connection.execute("SELECT schema_version FROM catalog_metadata").fetchall()
            if versions and versions != [("5.0.0",)]:
                raise CatalogError("Unsupported DuckDB catalog schema; rebuild the local catalog.")
            connection.execute("INSERT OR IGNORE INTO catalog_metadata VALUES ('5.0.0')")
            connection.execute(
                """CREATE TABLE IF NOT EXISTS dataset_registry (
                dataset_id VARCHAR PRIMARY KEY, dataset_type VARCHAR NOT NULL,
                parquet_path VARCHAR NOT NULL, output_checksum VARCHAR NOT NULL,
                manifest_path VARCHAR NOT NULL, lineage_path VARCHAR NOT NULL,
                lifecycle_journal_path VARCHAR NOT NULL,
                validation_status VARCHAR NOT NULL,
                promoted BOOLEAN NOT NULL DEFAULT FALSE,
                finalized BOOLEAN NOT NULL DEFAULT FALSE,
                registered_at TIMESTAMPTZ NOT NULL)"""
            )

    def register_persisted(
        self, dataset_id: str, manifest_path: Path, project_root: Path
    ) -> DatasetManifest:
        """Register only an authenticated persisted REGISTERED manifest revision."""
        manifest = authenticate_dataset_evidence(
            dataset_id,
            manifest_path,
            project_root,
            required_state=LifecycleState.ARTIFACT_PUBLISHED,
        )
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
            str(_resolve_evidence_path(manifest.lifecycle_journal_path, project_root)),
            manifest.validation_status.value,
        )
        try:
            with duckdb.connect(str(self.path)) as connection:
                existing = connection.execute(
                    "SELECT dataset_type, parquet_path, output_checksum, validation_status "
                    "FROM dataset_registry WHERE dataset_id = ?",
                    [manifest.dataset_id],
                ).fetchone()
                immutable_values = (values[0], values[1], values[2], values[6])
                if existing is not None and tuple(existing) != immutable_values:
                    raise CatalogError(
                        f"Dataset ID already maps to different evidence: {manifest.dataset_id}"
                    )
                if existing is None:
                    connection.execute(
                        "INSERT INTO dataset_registry VALUES "
                        "(?, ?, ?, ?, ?, ?, ?, ?, FALSE, FALSE, ?)",
                        [manifest.dataset_id, *values, datetime.now(UTC)],
                    )
        except duckdb.Error as exc:
            raise CatalogError(
                f"DuckDB registration failed for {manifest.dataset_id}: {exc}"
            ) from exc
        return manifest

    def stage_promotion(
        self, dataset_id: str, manifest_path: Path, project_root: Path
    ) -> DatasetManifest:
        """Persist promotion state without exposing it to research-ready views."""
        manifest = authenticate_dataset_evidence(
            dataset_id,
            manifest_path,
            project_root,
            required_state=LifecycleState.PROMOTION_PENDING,
        )
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
                    "UPDATE dataset_registry SET promoted = TRUE, finalized = FALSE, "
                    "manifest_path = ?, lineage_path = ?, lifecycle_journal_path = ? "
                    "WHERE dataset_id = ?",
                    [
                        str(manifest_path),
                        str(_resolve_evidence_path(manifest.lineage_path, project_root)),
                        str(_resolve_evidence_path(manifest.lifecycle_journal_path, project_root)),
                        dataset_id,
                    ],
                )
                connection.execute("COMMIT")
        except duckdb.Error as exc:
            raise PromotionError(
                f"DuckDB promotion failed for {manifest.dataset_id}: {exc}"
            ) from exc
        return manifest

    def promote_persisted(
        self, dataset_id: str, manifest_path: Path, project_root: Path
    ) -> DatasetManifest:
        """Finalize only a fully authenticated current FINALIZED lifecycle."""
        try:
            candidate = DatasetManifest.model_validate_json(
                manifest_path.read_text(encoding="utf-8")
            )
        except (OSError, ValueError) as exc:
            raise EvidenceIntegrityError(f"Invalid persisted dataset manifest: {exc}") from exc
        if candidate.promotion_state != "PUBLISHED":
            raise EvidenceIntegrityError("Finalization requires a PUBLISHED manifest revision.")
        manifest = authenticate_dataset_evidence(
            dataset_id,
            manifest_path,
            project_root,
            required_state=LifecycleState.FINALIZED,
            require_terminal_run=False,
        )
        if manifest.promotion_state != "PUBLISHED":
            raise EvidenceIntegrityError("Finalization requires a PUBLISHED manifest revision.")
        self.initialize()
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
                or not bool(existing[2])
            ):
                raise EvidenceIntegrityError(
                    "Catalog registration/promotion stage is missing or inconsistent."
                )
            connection.execute("BEGIN TRANSACTION")
            connection.execute(
                "UPDATE dataset_registry SET finalized = TRUE, manifest_path = ?, "
                "lineage_path = ?, lifecycle_journal_path = ? WHERE dataset_id = ?",
                [
                    str(manifest_path),
                    str(_resolve_evidence_path(manifest.lineage_path, project_root)),
                    str(_resolve_evidence_path(manifest.lifecycle_journal_path, project_root)),
                    dataset_id,
                ],
            )
            self._rebuild_view(connection, manifest.dataset_type)
            connection.execute("COMMIT")
        return manifest

    def demote(
        self,
        dataset_id: str,
        *,
        reason: str = "authoritative catalog demotion",
        record_lifecycle: bool = True,
    ) -> None:
        self.initialize()
        with duckdb.connect(str(self.path)) as connection:
            row = connection.execute(
                "SELECT dataset_type, lifecycle_journal_path FROM dataset_registry "
                "WHERE dataset_id = ?",
                [dataset_id],
            ).fetchone()
            if row is None:
                return
            connection.execute("BEGIN TRANSACTION")
            connection.execute(
                "UPDATE dataset_registry SET promoted = FALSE, finalized = FALSE "
                "WHERE dataset_id = ?",
                [dataset_id],
            )
            self._rebuild_view(connection, str(row[0]))
            connection.execute("COMMIT")
        if record_lifecycle:
            _append_catalog_demotion(Path(str(row[1])), reason)

    def _rebuild_view(self, connection: Any, dataset_type: str) -> None:
        view = _safe_identifier(f"validated_{dataset_type}")
        rows = connection.execute(
            "SELECT parquet_path FROM dataset_registry WHERE dataset_type = ? "
            "AND promoted = TRUE AND finalized = TRUE "
            "AND validation_status IN ('PASS', 'PASS_WITH_WARNINGS') "
            "ORDER BY dataset_id",
            [dataset_type],
        ).fetchall()
        connection.execute(f'DROP VIEW IF EXISTS "{view}"')
        if rows:
            paths = ", ".join("'" + str(row[0]).replace("'", "''") + "'" for row in rows)
            connection.execute(f'CREATE VIEW "{view}" AS SELECT * FROM read_parquet([{paths}])')

    def list_datasets(self, *, research_ready_only: bool = False) -> list[tuple[str, str, str]]:
        self.initialize()
        if research_ready_only and self.project_root is not None:
            try:
                self.verify_integrity(self.project_root)
            except EvidenceIntegrityError:
                pass
        clause = " WHERE promoted = TRUE AND finalized = TRUE" if research_ready_only else ""
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
                "SELECT dataset_id, dataset_type, parquet_path, output_checksum, "
                "manifest_path, lineage_path, lifecycle_journal_path "
                "FROM dataset_registry WHERE finalized = TRUE"
            ).fetchall()
        root = (project_root or Path.cwd()).resolve()
        failures: list[str] = []
        for (
            dataset_id,
            _dataset_type,
            parquet_value,
            checksum,
            manifest_value,
            lineage_value,
            journal_value,
        ) in rows:
            try:
                manifest_path = Path(str(manifest_value))
                persisted = authenticate_dataset_evidence(
                    str(dataset_id), manifest_path, root, required_state=LifecycleState.FINALIZED
                )
                if str(_resolve_evidence_path(persisted.parquet_path, root)) != str(parquet_value):
                    raise EvidenceIntegrityError("Catalog Parquet path differs from manifest.")
                if persisted.output_checksum != checksum:
                    raise EvidenceIntegrityError("Catalog checksum differs from manifest.")
                if str(_resolve_evidence_path(persisted.lineage_path, root)) != str(lineage_value):
                    raise EvidenceIntegrityError("Catalog lineage path differs from manifest.")
            except Exception as exc:
                self.demote(str(dataset_id), record_lifecycle=False)
                _append_catalog_invalidation(Path(str(journal_value)), str(exc))
                failures.append(f"{dataset_id}: {exc}")
        if failures:
            raise EvidenceIntegrityError("; ".join(failures))

    @classmethod
    def rebuild_from_manifests(
        cls, target: Path, manifests_root: Path, project_root: Path
    ) -> "DuckDBCatalog":
        """Build a complete isolated catalog and atomically activate it on success."""
        target.parent.mkdir(parents=True, exist_ok=True)
        descriptor, temporary_name = tempfile.mkstemp(
            dir=target.parent, prefix=f".{target.name}-rebuild-", suffix=".duckdb"
        )
        os.close(descriptor)
        temporary = Path(temporary_name)
        temporary.unlink()
        try:
            catalog = cls(temporary, project_root)
            for promotion_path in sorted(manifests_root.rglob("promotion.json")):
                promotion = PromotionManifest.model_validate_json(
                    promotion_path.read_text(encoding="utf-8")
                )
                manifest_path = _resolve_evidence_path(
                    promotion.dataset_manifest_path, project_root
                )
                candidate = DatasetManifest.model_validate_json(
                    manifest_path.read_text(encoding="utf-8")
                )
                lifecycle = LifecycleEventStore(
                    _resolve_evidence_path(candidate.lifecycle_journal_path, project_root)
                ).load()
                if lifecycle and lifecycle[-1].new_state in {
                    LifecycleState.DEMOTED,
                    LifecycleState.INVALIDATED,
                    LifecycleState.SUPERSEDED,
                }:
                    continue
                manifest = authenticate_dataset_evidence(
                    promotion.dataset_id,
                    manifest_path,
                    project_root,
                    required_state=LifecycleState.FINALIZED,
                )
                if manifest.content_hash() != promotion.dataset_manifest_hash:
                    raise PromotionError("Promotion references a changed dataset manifest.")
                if promotion.lifecycle_final_event_id != _current_lifecycle_event(
                    manifest, project_root
                ):
                    raise PromotionError("Promotion references the wrong lifecycle finalization.")
                registered_path = manifest_path.with_name("dataset-registered.json")
                catalog.register_persisted(manifest.dataset_id, registered_path, project_root)
                catalog.stage_promotion(manifest.dataset_id, manifest_path, project_root)
                catalog.promote_persisted(manifest.dataset_id, manifest_path, project_root)
            catalog.verify_integrity(project_root)
            os.replace(temporary, target)
            return cls(target, project_root)
        except Exception:
            temporary.unlink(missing_ok=True)
            Path(f"{temporary}.wal").unlink(missing_ok=True)
            raise


def authenticate_dataset_evidence(
    dataset_id: str,
    manifest_path: Path,
    project_root: Path,
    *,
    required_state: LifecycleState | None = None,
    require_terminal_run: bool = True,
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
    expected_report_fields = {
        "dataset_id",
        "source",
        "run_id",
        "schema_version",
        "row_count",
        "entity_count",
        "requested_start",
        "requested_end",
        "observed_start",
        "observed_end",
        "results",
        "final_status",
        "quarantine_path",
    }
    if not isinstance(report, dict) or set(report) != expected_report_fields:
        raise EvidenceIntegrityError("Validation report does not match the complete schema.")
    if not isinstance(report["results"], list) or not isinstance(report["row_count"], int):
        raise EvidenceIntegrityError("Validation report contains invalid typed evidence.")
    expected_result_fields = {
        "rule",
        "severity",
        "message",
        "field",
        "row",
        "rule_version",
        "dataset_id",
        "affected_count",
        "representative_keys",
        "remediation",
        "source",
        "timestamp",
    }
    if any(
        not isinstance(item, dict)
        or set(item) != expected_result_fields
        or item.get("severity") not in {"INFO", "WARNING", "ERROR", "CRITICAL"}
        or not isinstance(item.get("affected_count"), int)
        or item["affected_count"] < 0
        for item in report["results"]
    ):
        raise EvidenceIntegrityError("Validation result does not match the complete schema.")
    if report.get("dataset_id") != dataset_id or report.get("run_id") != manifest.run_id:
        raise EvidenceIntegrityError("Validation report identity does not match manifest.")
    expected_report_id = f"validation:{manifest.validation_report_checksum}"
    if manifest.validation_report_id != expected_report_id:
        raise EvidenceIntegrityError("Validation report ID is not content-bound.")
    if report.get("final_status") != manifest.validation_status.value:
        raise EvidenceIntegrityError("Validation status differs from persisted report.")
    if report["row_count"] != manifest.row_count:
        raise EvidenceIntegrityError("Validation report row count differs from manifest.")
    if any(item["severity"] in {"ERROR", "CRITICAL"} for item in report["results"]):
        raise EvidenceIntegrityError("Validation report contains blocking findings.")
    if manifest.validation_status.value not in DuckDBCatalog.ELIGIBLE:
        raise EvidenceIntegrityError("Persisted validation status is not promotion eligible.")
    lineage = LineageStore(resolved["lineage"]).load()
    if (
        lineage.schema_version != "4.0.0"
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
        registration_id = manifest.catalog_registration_id
        promotion_id = manifest.promotion_event_id
        exact_edges = {
            (edge.parent_artifact_id, edge.child_artifact_id, edge.relationship_type)
            for edge in lineage.edges
        }
        needed = {
            (manifest.output_artifact_id, dataset_id, RelationshipType.MANIFESTED),
            (dataset_id, registration_id, RelationshipType.REGISTERED_IN_CATALOG),
            (registration_id, promotion_id, RelationshipType.PROMOTED_TO_RESEARCH_READY),
        }
        if not needed.issubset(exact_edges):
            raise EvidenceIntegrityError("Published lineage lacks the exact connected lifecycle.")
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
    try:
        snapshot_value = json.loads(resolved["configuration snapshot"].read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise EvidenceIntegrityError(f"Invalid configuration snapshot: {exc}") from exc
    if not isinstance(snapshot_value, dict) or not snapshot_value:
        raise EvidenceIntegrityError("Configuration snapshot must be a non-empty object.")
    computed_config_hash = hashlib.sha256(canonical_json_bytes(snapshot_value)).hexdigest()
    if (
        computed_config_hash != manifest.configuration_hash
        or manifest.configuration_snapshot_id != f"config:{computed_config_hash}"
    ):
        raise EvidenceIntegrityError("Configuration snapshot identity does not match manifest.")
    if manifest.mapping_status == "RESOLVED":
        if not (
            manifest.mapping_evidence_path
            and manifest.mapping_evidence_checksum
            and manifest.mapping_evidence_id
        ):
            raise EvidenceIntegrityError("Resolved mapping evidence is incomplete.")
        mapping_path = _resolve_evidence_path(manifest.mapping_evidence_path, project_root)
        if (
            not mapping_path.is_file()
            or sha256_file(mapping_path) != manifest.mapping_evidence_checksum
            or manifest.mapping_evidence_id != f"mapping:{manifest.mapping_evidence_checksum}"
        ):
            raise EvidenceIntegrityError("Mapping authority is missing or has changed.")
    journal = LifecycleEventStore(
        _resolve_evidence_path(manifest.lifecycle_journal_path, project_root)
    )
    events = journal.load()
    if not events or events[-1].dataset_id != dataset_id:
        raise EvidenceIntegrityError("Lifecycle journal is missing or has the wrong dataset.")
    if manifest.lifecycle_head_event_id not in {event.event_id for event in events}:
        raise EvidenceIntegrityError("Manifest lifecycle head is absent from the journal.")
    final = events[-1]
    invariant_pairs = {
        "artifact_id": manifest.output_artifact_id,
        "run_id": manifest.run_id,
        "registration_id": manifest.catalog_registration_id,
        "validation_report_id": manifest.validation_report_id,
        "lineage_document_id": manifest.lineage_id,
        "configuration_snapshot_id": manifest.configuration_snapshot_id,
        "code_commit": manifest.git_commit,
        "configuration_hash": manifest.configuration_hash,
    }
    if required_state is LifecycleState.FINALIZED:
        invariant_pairs["manifest_revision_id"] = manifest.manifest_revision_id
    if any(getattr(final, key) != value for key, value in invariant_pairs.items()):
        raise EvidenceIntegrityError("Dataset manifest identities differ from lifecycle authority.")
    if required_state is not None:
        states = {event.new_state for event in events}
        if required_state not in states:
            raise EvidenceIntegrityError(f"Lifecycle has not reached {required_state.value}.")
        if (
            required_state is LifecycleState.FINALIZED
            and events[-1].new_state is not required_state
        ):
            raise EvidenceIntegrityError("Current lifecycle state is not FINALIZED.")
    if required_state is LifecycleState.FINALIZED:
        promotion_path = manifest_path.with_name("promotion.json")
        try:
            promotion = PromotionManifest.model_validate_json(
                promotion_path.read_text(encoding="utf-8")
            )
        except (OSError, ValueError) as exc:
            raise EvidenceIntegrityError(f"Final promotion evidence is invalid: {exc}") from exc
        if (
            promotion.dataset_id != dataset_id
            or promotion.run_id != manifest.run_id
            or promotion.promotion_manifest_id != manifest.promotion_event_id
            or _resolve_evidence_path(promotion.dataset_manifest_path, project_root)
            != manifest_path.resolve()
            or promotion.dataset_manifest_hash != manifest.content_hash()
            or promotion.output_checksum != manifest.output_checksum
            or _resolve_evidence_path(promotion.lineage_path, project_root) != resolved["lineage"]
            or promotion.validation_status is not manifest.validation_status
            or promotion.git_commit != manifest.git_commit
            or promotion.configuration_hash != manifest.configuration_hash
            or promotion.lifecycle_final_event_id != final.event_id
        ):
            raise EvidenceIntegrityError(
                "Final promotion envelope does not bind the authenticated dataset evidence."
            )
        if (
            f"promotion-envelope:{promotion.content_hash()}" not in final.supporting_evidence_ids
            or f"run-terminal:{manifest.run_id}" not in final.supporting_evidence_ids
        ):
            raise EvidenceIntegrityError(
                "Final lifecycle event does not authenticate the promotion envelope."
            )
        if require_terminal_run:
            run_path = _resolve_evidence_path(promotion.run_manifest_path, project_root)
            try:
                run = RunManifest.model_validate_json(run_path.read_text(encoding="utf-8"))
                started = RunManifest.model_validate_json(
                    run_path.with_name("run-started.json").read_text(encoding="utf-8")
                )
            except (OSError, ValueError) as exc:
                raise EvidenceIntegrityError(f"Terminal run evidence is invalid: {exc}") from exc
            if (
                run.run_id != manifest.run_id
                or run.status != "SUCCESS"
                or run.git_commit != manifest.git_commit
                or run.configuration_hash != manifest.configuration_hash
                or set(run.output_artifacts) != {dataset_id, promotion.promotion_manifest_id}
                or started.status != "RUNNING"
                or started.run_id != run.run_id
                or started.start_time != run.start_time
                or started.git_commit != run.git_commit
                or started.configuration_hash != run.configuration_hash
                or started.configuration_snapshot_path != run.configuration_snapshot_path
                or started.requested_sources != run.requested_sources
                or started.requested_datasets != run.requested_datasets
            ):
                raise EvidenceIntegrityError(
                    "Terminal run evidence does not authorize publication."
                )
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
    try:
        return resolve_project_path(value, project_root)
    except Exception as exc:
        raise EvidenceIntegrityError(str(exc)) from exc


def _current_lifecycle_event(manifest: DatasetManifest, project_root: Path) -> str:
    events = LifecycleEventStore(
        _resolve_evidence_path(manifest.lifecycle_journal_path, project_root)
    ).load()
    if not events or events[-1].new_state is not LifecycleState.FINALIZED:
        raise EvidenceIntegrityError("Lifecycle is not finalized.")
    return events[-1].event_id


def _append_catalog_invalidation(journal_path: Path, reason: str) -> None:
    try:
        store = LifecycleEventStore(journal_path)
        events = store.load()
        if not events or events[-1].new_state is not LifecycleState.FINALIZED:
            return
        previous = events[-1]
        values = previous.model_dump(mode="python", exclude={"event_checksum"})
        values.update(
            {
                "sequence": previous.sequence + 1,
                "event_id": f"lifecycle:{previous.run_id}:{previous.sequence + 1:04d}:invalidated",
                "event_type": LifecycleState.INVALIDATED.value,
                "prior_event_id": previous.event_id,
                "prior_state": previous.new_state,
                "new_state": LifecycleState.INVALIDATED,
                "event_timestamp": datetime.now(UTC),
                "reason": reason,
            }
        )
        store.persist(LifecycleEvent.create(**values))
    except Exception:
        # Visibility has already been removed; a corrupt journal requires manual recovery.
        return


def _append_catalog_demotion(journal_path: Path, reason: str) -> None:
    """Make an exposed catalog demotion durable in the authoritative lifecycle."""
    store = LifecycleEventStore(journal_path)
    events = store.load()
    if not events or events[-1].new_state in {
        LifecycleState.DEMOTED,
        LifecycleState.INVALIDATED,
        LifecycleState.SUPERSEDED,
    }:
        return
    previous = events[-1]
    if previous.new_state is LifecycleState.FINALIZED:
        previous = _append_transition(store, previous, LifecycleState.DEMOTION_PENDING, reason)
    elif previous.new_state in {
        LifecycleState.ARTIFACT_PUBLISHED,
        LifecycleState.REGISTERED,
        LifecycleState.PROMOTION_PENDING,
        LifecycleState.PROMOTED,
    }:
        previous = _append_transition(store, previous, LifecycleState.RECOVERY_REQUIRED, reason)
    else:
        raise EvidenceIntegrityError(
            f"Cannot durably demote lifecycle from {previous.new_state.value}."
        )
    _append_transition(store, previous, LifecycleState.DEMOTED, reason)


def _append_transition(
    store: LifecycleEventStore,
    previous: LifecycleEvent,
    state: LifecycleState,
    reason: str,
) -> LifecycleEvent:
    values = previous.model_dump(mode="python", exclude={"event_checksum"})
    event_id = f"lifecycle:{previous.run_id}:{previous.sequence + 1:04d}:{state.value.lower()}"
    values.update(
        {
            "sequence": previous.sequence + 1,
            "event_id": event_id,
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
