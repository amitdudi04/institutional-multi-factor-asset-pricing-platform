"""Checksum-bound immutable Phase 3 publication evidence and read-time isolation."""

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

REQUIRED_TABLE_COLUMNS = {
    "coefficients": {
        "asset_id",
        "model_id",
        "term",
        "estimate",
        "standard_error",
        "t_statistic",
        "p_value",
        "confidence_lower",
        "confidence_upper",
        "nobs",
        "covariance",
    },
    "residuals": {
        "asset_id",
        "model_id",
        "date",
        "observed_excess_return",
        "fitted_return",
        "residual",
    },
    "model_comparison": {
        "asset_id",
        "model_id",
        "nobs",
        "r_squared",
        "adjusted_r_squared",
        "aic",
        "bic",
        "residual_standard_error",
    },
    "rolling_coefficients": {
        "window_end",
        "window_start",
        "term",
        "estimate",
        "standard_error",
        "t_statistic",
        "p_value",
        "confidence_lower",
        "confidence_upper",
        "asset_id",
        "model_id",
        "window_type",
    },
    "influence": {
        "observation",
        "leverage",
        "cooks_distance",
        "studentized_residual",
        "asset_id",
        "model_id",
    },
}


class ImmutableModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    def content_hash(self) -> str:
        payload = json.dumps(self.model_dump(mode="json"), sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(payload.encode()).hexdigest()


class BoundArtifact(ImmutableModel):
    name: str
    path: str
    checksum: str = Field(pattern=r"^[a-f0-9]{64}$")
    byte_size: int = Field(gt=0)
    media_type: Literal["application/json", "application/vnd.apache.parquet"]


class AssetPricingManifest(ImmutableModel):
    schema_version: Literal["1.0.0"]
    publication_id: str
    created_at: datetime
    phase2_publication_id: str
    phase2_manifest_hash: str = Field(pattern=r"^[a-f0-9]{64}$")
    configuration_hash: str = Field(pattern=r"^[a-f0-9]{64}$")
    git_commit: str
    model_ids: tuple[str, ...]
    asset_ids: tuple[str, ...]
    observation_start: str
    observation_end: str
    artifacts: tuple[BoundArtifact, ...]
    validation_status: Literal["PASS", "PASS_WITH_WARNINGS"]


class AssetPricingPublication(ImmutableModel):
    schema_version: Literal["1.0.0"]
    publication_id: str
    manifest_path: str
    manifest_hash: str = Field(pattern=r"^[a-f0-9]{64}$")
    configuration_hash: str = Field(pattern=r"^[a-f0-9]{64}$")
    git_commit: str


def publish_parquet(path: Path, table: pa.Table) -> tuple[str, int]:
    path.parent.mkdir(parents=True, exist_ok=True)
    handle, name = tempfile.mkstemp(dir=path.parent, prefix=f".{path.name}-", suffix=".tmp")
    os.close(handle)
    temporary = Path(name)
    try:
        pq.write_table(table, temporary, compression="zstd")
        checksum = sha256_file(temporary)
        if path.exists():
            if sha256_file(path) != checksum:
                raise PublicationConflictError(f"Phase 3 artifact identity collision: {path}")
        else:
            os.replace(temporary, path)
        return checksum, path.stat().st_size
    finally:
        temporary.unlink(missing_ok=True)


def authenticate_asset_pricing_publication(path: Path, project_root: Path) -> AssetPricingManifest:
    root = project_root.resolve()
    try:
        publication = AssetPricingPublication.model_validate_json(path.read_text("utf-8"))
        manifest_path = resolve_project_path(publication.manifest_path, root)
        manifest = AssetPricingManifest.model_validate_json(manifest_path.read_text("utf-8"))
    except (OSError, ValueError) as exc:
        raise EvidenceIntegrityError(f"Invalid Phase 3 publication evidence: {exc}") from exc
    if (
        publication.publication_id != manifest.publication_id
        or publication.manifest_hash != manifest.content_hash()
        or publication.configuration_hash != manifest.configuration_hash
        or publication.git_commit != manifest.git_commit
    ):
        raise EvidenceIntegrityError("Phase 3 publication does not bind its manifest authority")
    names: set[str] = set()
    for artifact in manifest.artifacts:
        if artifact.name in names:
            raise EvidenceIntegrityError("Phase 3 manifest contains duplicate artifact names")
        names.add(artifact.name)
        artifact_path = resolve_project_path(artifact.path, root)
        try:
            content = artifact_path.read_bytes()
        except OSError as exc:
            raise EvidenceIntegrityError(
                f"Phase 3 artifact is unavailable: {artifact.name}"
            ) from exc
        if (
            len(content) != artifact.byte_size
            or hashlib.sha256(content).hexdigest() != artifact.checksum
        ):
            raise EvidenceIntegrityError(f"Phase 3 artifact changed: {artifact.name}")
        if artifact.media_type == "application/json":
            try:
                value = json.loads(content)
            except (UnicodeDecodeError, json.JSONDecodeError) as exc:
                raise EvidenceIntegrityError(f"Invalid bound JSON: {artifact.name}") from exc
            if isinstance(value, dict) and value.get("publication_id") not in {
                None,
                manifest.publication_id,
            }:
                raise EvidenceIntegrityError(f"Phase 3 JSON identity differs: {artifact.name}")
        else:
            try:
                schema = pq.read_schema(pa.BufferReader(content))
            except pa.ArrowException as exc:
                raise EvidenceIntegrityError(f"Invalid bound Parquet: {artifact.name}") from exc
            expected = REQUIRED_TABLE_COLUMNS.get(artifact.name)
            if expected is None or set(schema.names) != expected:
                raise EvidenceIntegrityError(f"Phase 3 table schema differs: {artifact.name}")
    required = {
        "coefficients",
        "residuals",
        "model_comparison",
        "rolling_coefficients",
        "influence",
        "diagnostics",
        "assumptions",
        "validation",
        "configuration",
        "lineage",
    }
    if names != required:
        raise EvidenceIntegrityError("Phase 3 publication artifact set is incomplete or unexpected")
    return manifest


class AssetPricingRepository:
    def __init__(self, project_root: Path, manifest_root: Path) -> None:
        self.root = project_root.resolve()
        self.manifest_root = manifest_root.resolve()

    def authenticate(self, publication_id: str) -> AssetPricingManifest:
        path = self.manifest_root / publication_id / "asset-pricing-publication.json"
        manifest = authenticate_asset_pricing_publication(path, self.root)
        if manifest.publication_id != publication_id:
            raise EvidenceIntegrityError("Phase 3 path identity differs from publication")
        return manifest

    def list_authenticated(self) -> tuple[str, ...]:
        values: list[str] = []
        for path in sorted(self.manifest_root.glob("*/asset-pricing-publication.json")):
            try:
                values.append(
                    authenticate_asset_pricing_publication(path, self.root).publication_id
                )
            except EvidenceIntegrityError:
                continue
        return tuple(values)

    def read_table(self, publication_id: str, artifact_name: str) -> pa.Table:
        manifest = self.authenticate(publication_id)
        artifact = next((item for item in manifest.artifacts if item.name == artifact_name), None)
        if artifact is None or artifact.media_type != "application/vnd.apache.parquet":
            raise EvidenceIntegrityError(
                f"Authenticated Phase 3 table is unavailable: {artifact_name}"
            )
        content = resolve_project_path(artifact.path, self.root).read_bytes()
        if hashlib.sha256(content).hexdigest() != artifact.checksum:
            raise EvidenceIntegrityError("Phase 3 artifact changed during authenticated read")
        return pq.read_table(pa.BufferReader(content))
