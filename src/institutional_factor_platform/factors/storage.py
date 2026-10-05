"""Immutable factor publication and access."""

import hashlib
import json
import os
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Literal

import pyarrow as pa
import pyarrow.parquet as pq
from pydantic import BaseModel, ConfigDict, Field

from institutional_factor_platform.data.evidence import resolve_project_path
from institutional_factor_platform.data.storage import sha256_file
from institutional_factor_platform.exceptions import (
    EvidenceIntegrityError,
    PublicationConflictError,
)
from institutional_factor_platform.factors.contracts import FACTOR_SCHEMA


class ImmutableModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    def canonical_json(self) -> str:
        return json.dumps(self.model_dump(mode="json"), sort_keys=True, separators=(",", ":"))

    def content_hash(self) -> str:
        return hashlib.sha256(self.canonical_json().encode()).hexdigest()


class ParentDatasetEvidence(ImmutableModel):
    dataset_id: str
    artifact_checksum: str = Field(pattern=r"^[a-f0-9]{64}$")
    lineage_id: str
    promotion_id: str
    run_id: str
    validation_status: str
    schema_version: str
    unit_metadata: dict[str, str]
    configuration_hash: str = Field(pattern=r"^[a-f0-9]{64}$")
    git_commit: str
    mapping_status: str
    mapping_evidence_id: str | None
    temporal_policy: str


class FactorMetadata(ImmutableModel):
    factor_id: str
    definition: str
    formula: str
    economic_rationale: str
    required_inputs: tuple[str, ...]
    unit: str
    direction: Literal[-1, 1]
    transformation_chain: tuple[str, ...]
    dependencies: tuple[str, ...]
    version: str
    research_notes: str


class FactorManifest(ImmutableModel):
    schema_version: Literal["1.0.0"]
    publication_id: str
    created_at: datetime
    factor_version: str
    artifact_path: str
    artifact_checksum: str = Field(pattern=r"^[a-f0-9]{64}$")
    artifact_byte_size: int = Field(gt=0)
    schema_fingerprint: str = Field(pattern=r"^[a-f0-9]{64}$")
    portfolio_artifact_path: str
    portfolio_artifact_checksum: str = Field(pattern=r"^[a-f0-9]{64}$")
    portfolio_artifact_byte_size: int = Field(gt=0)
    portfolio_schema_fingerprint: str = Field(pattern=r"^[a-f0-9]{64}$")
    portfolio_row_count: int = Field(gt=0)
    row_count: int = Field(gt=0)
    security_count: int = Field(gt=0)
    date_start: str
    date_end: str
    factor_ids: tuple[str, ...]
    parents: tuple[ParentDatasetEvidence, ...]
    market_source_dataset_ids: tuple[str, ...]
    fundamental_source_dataset_ids: tuple[str, ...]
    configuration_hash: str = Field(pattern=r"^[a-f0-9]{64}$")
    configuration_snapshot_path: str
    configuration_snapshot_checksum: str = Field(pattern=r"^[a-f0-9]{64}$")
    validation_report_path: str
    validation_report_checksum: str = Field(pattern=r"^[a-f0-9]{64}$")
    validation_status: Literal["PASS", "PASS_WITH_WARNINGS"]
    diagnostics_path: str
    diagnostics_checksum: str = Field(pattern=r"^[a-f0-9]{64}$")
    lineage_path: str
    lineage_checksum: str = Field(pattern=r"^[a-f0-9]{64}$")
    git_commit: str
    metadata: tuple[FactorMetadata, ...]


class FactorPublication(ImmutableModel):
    schema_version: Literal["1.0.0"]
    publication_id: str
    manifest_path: str
    manifest_hash: str = Field(pattern=r"^[a-f0-9]{64}$")
    artifact_checksum: str = Field(pattern=r"^[a-f0-9]{64}$")
    git_commit: str
    configuration_hash: str = Field(pattern=r"^[a-f0-9]{64}$")


def schema_fingerprint(schema: pa.Schema = FACTOR_SCHEMA) -> str:
    return hashlib.sha256(schema.remove_metadata().serialize().to_pybytes()).hexdigest()


def publish_factor_parquet(
    path: Path, table: pa.Table, *, schema: pa.Schema = FACTOR_SCHEMA
) -> tuple[str, int]:
    if not table.schema.equals(schema, check_metadata=False):
        raise PublicationConflictError("factor table does not match the v1 Arrow contract")
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(
        dir=path.parent, prefix=f".{path.name}-", suffix=".tmp"
    )
    os.close(descriptor)
    temporary = Path(temporary_name)
    try:
        pq.write_table(table, temporary, compression="zstd")
        try:
            descriptor = os.open(temporary, os.O_RDONLY)
            try:
                os.fsync(descriptor)
            finally:
                os.close(descriptor)
        except OSError:
            # Some Windows/filesystem combinations reject fsync on read-only handles.
            pass
        checksum = sha256_file(temporary)
        if path.exists():
            if sha256_file(path) != checksum:
                raise PublicationConflictError(f"factor artifact identity collision: {path}")
            return checksum, path.stat().st_size
        os.replace(temporary, path)
        return checksum, path.stat().st_size
    finally:
        temporary.unlink(missing_ok=True)


def authenticate_factor_publication(publication_path: Path, project_root: Path) -> FactorManifest:
    root = project_root.resolve()
    try:
        publication = FactorPublication.model_validate_json(
            publication_path.read_text(encoding="utf-8")
        )
        manifest_path = resolve_project_path(publication.manifest_path, root)
        manifest = FactorManifest.model_validate_json(manifest_path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise EvidenceIntegrityError(f"Invalid factor publication evidence: {exc}") from exc
    if (
        publication.publication_id != manifest.publication_id
        or publication.manifest_hash != manifest.content_hash()
        or publication.artifact_checksum != manifest.artifact_checksum
        or publication.git_commit != manifest.git_commit
        or publication.configuration_hash != manifest.configuration_hash
    ):
        raise EvidenceIntegrityError("Factor publication does not bind the manifest authority.")
    evidence = (
        (manifest.artifact_path, manifest.artifact_checksum, "factor artifact"),
        (
            manifest.portfolio_artifact_path,
            manifest.portfolio_artifact_checksum,
            "factor portfolio artifact",
        ),
        (
            manifest.configuration_snapshot_path,
            manifest.configuration_snapshot_checksum,
            "factor configuration",
        ),
        (
            manifest.validation_report_path,
            manifest.validation_report_checksum,
            "factor validation",
        ),
        (manifest.diagnostics_path, manifest.diagnostics_checksum, "factor diagnostics"),
        (manifest.lineage_path, manifest.lineage_checksum, "factor lineage"),
    )
    bound_content: dict[str, bytes] = {}
    for value, checksum, label in evidence:
        path = resolve_project_path(value, root)
        try:
            content = path.read_bytes()
        except OSError as exc:
            raise EvidenceIntegrityError(f"Persisted {label} is missing or changed.") from exc
        if hashlib.sha256(content).hexdigest() != checksum:
            raise EvidenceIntegrityError(f"Persisted {label} is missing or changed.")
        bound_content[label] = content
    if len(bound_content["factor artifact"]) != manifest.artifact_byte_size:
        raise EvidenceIntegrityError("Factor artifact byte size differs from manifest.")
    if (
        schema_fingerprint(pq.read_schema(pa.BufferReader(bound_content["factor artifact"])))
        != manifest.schema_fingerprint
    ):
        raise EvidenceIntegrityError("Factor artifact schema differs from manifest.")
    if len(bound_content["factor portfolio artifact"]) != manifest.portfolio_artifact_byte_size:
        raise EvidenceIntegrityError("Factor portfolio byte size differs from manifest.")
    if (
        schema_fingerprint(
            pq.read_schema(pa.BufferReader(bound_content["factor portfolio artifact"]))
        )
        != manifest.portfolio_schema_fingerprint
    ):
        raise EvidenceIntegrityError("Factor portfolio schema differs from manifest.")
    config_value = json.loads(bound_content["factor configuration"].decode())
    config_hash = hashlib.sha256(
        json.dumps(config_value, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
    if config_hash != manifest.configuration_hash:
        raise EvidenceIntegrityError("Factor configuration identity differs from manifest.")
    validation = json.loads(bound_content["factor validation"].decode())
    if (
        validation.get("publication_id") != manifest.publication_id
        or validation.get("status") != manifest.validation_status
        or validation.get("row_count") != manifest.row_count
    ):
        raise EvidenceIntegrityError("Factor validation identity differs from manifest.")
    diagnostics = json.loads(bound_content["factor diagnostics"].decode())
    if diagnostics.get("publication_id") != manifest.publication_id:
        raise EvidenceIntegrityError("Factor diagnostics identity differs from manifest.")
    lineage = json.loads(bound_content["factor lineage"].decode())
    if (
        lineage.get("publication_id") != manifest.publication_id
        or set(lineage.get("parent_dataset_ids", []))
        != {parent.dataset_id for parent in manifest.parents}
        or lineage.get("artifact_checksum") != manifest.artifact_checksum
        or lineage.get("portfolio_artifact_checksum") != manifest.portfolio_artifact_checksum
        or set(lineage.get("market_source_dataset_ids", []))
        != set(manifest.market_source_dataset_ids)
        or set(lineage.get("fundamental_source_dataset_ids", []))
        != set(manifest.fundamental_source_dataset_ids)
    ):
        raise EvidenceIntegrityError("Factor lineage identity differs from manifest.")
    return manifest


class FactorRepository:
    def __init__(self, project_root: Path, manifest_root: Path) -> None:
        self.project_root = project_root.resolve()
        self.manifest_root = manifest_root

    def list_authenticated(self) -> tuple[str, ...]:
        authenticated: list[str] = []
        for publication in sorted(self.manifest_root.glob("*/factor-publication.json")):
            try:
                authenticated.append(
                    authenticate_factor_publication(publication, self.project_root).publication_id
                )
            except EvidenceIntegrityError:
                continue
        return tuple(authenticated)

    def read_table(self, publication_id: str) -> pa.Table:
        manifest = self.authenticate(publication_id)
        return _read_manifest_parquet(
            manifest.artifact_path, manifest.artifact_checksum, self.project_root
        )

    def read_portfolios(self, publication_id: str) -> pa.Table:
        manifest = self.authenticate(publication_id)
        return _read_manifest_parquet(
            manifest.portfolio_artifact_path,
            manifest.portfolio_artifact_checksum,
            self.project_root,
        )

    def authenticate(self, publication_id: str) -> FactorManifest:
        publication = self.manifest_root / publication_id / "factor-publication.json"
        if not publication.is_file():
            raise EvidenceIntegrityError(f"Factor publication is unavailable: {publication_id}")
        manifest = authenticate_factor_publication(publication, self.project_root)
        if manifest.publication_id != publication_id:
            raise EvidenceIntegrityError("Factor publication path and identity differ.")
        return manifest


def _read_manifest_parquet(relative_path: str, checksum: str, project_root: Path) -> pa.Table:
    path = resolve_project_path(relative_path, project_root)
    try:
        content = path.read_bytes()
    except OSError as exc:
        raise EvidenceIntegrityError("Authenticated factor artifact became unavailable.") from exc
    if hashlib.sha256(content).hexdigest() != checksum:
        raise EvidenceIntegrityError("Factor artifact changed during authenticated read.")
    return pq.read_table(pa.BufferReader(content))
