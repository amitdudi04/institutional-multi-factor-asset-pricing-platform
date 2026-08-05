"""Authenticated immutable Phase 4 portfolio publication storage."""

import hashlib
import json
from datetime import datetime
from pathlib import Path
from typing import Literal

import pyarrow as pa
import pyarrow.parquet as pq
from pydantic import BaseModel, ConfigDict, Field

from institutional_factor_platform.data.evidence import resolve_project_path
from institutional_factor_platform.exceptions import EvidenceIntegrityError


class FrozenModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    def content_hash(self) -> str:
        value = json.dumps(self.model_dump(mode="json"), sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(value.encode()).hexdigest()


class PortfolioArtifact(FrozenModel):
    name: str
    path: str
    checksum: str = Field(pattern=r"^[a-f0-9]{64}$")
    byte_size: int = Field(gt=0)
    media_type: Literal["application/json", "application/vnd.apache.parquet"]
    columns: tuple[str, ...] = ()


class PortfolioManifest(FrozenModel):
    schema_version: Literal["1.0.0"]
    publication_id: str
    created_at: datetime
    phase2_publication_id: str
    phase2_manifest_hash: str = Field(pattern=r"^[a-f0-9]{64}$")
    phase3_publication_id: str
    phase3_manifest_hash: str = Field(pattern=r"^[a-f0-9]{64}$")
    configuration_hash: str = Field(pattern=r"^[a-f0-9]{64}$")
    git_commit: str
    method: str
    artifacts: tuple[PortfolioArtifact, ...]
    validation_status: Literal["PASS", "PASS_WITH_WARNINGS"]


class PortfolioPublication(FrozenModel):
    schema_version: Literal["1.0.0"]
    publication_id: str
    manifest_path: str
    manifest_hash: str = Field(pattern=r"^[a-f0-9]{64}$")
    configuration_hash: str = Field(pattern=r"^[a-f0-9]{64}$")
    git_commit: str


REQUIRED = {
    "allocations",
    "transactions",
    "returns",
    "optimization_diagnostics",
    "constraint_report",
    "performance_summary",
    "risk_summary",
    "benchmark_comparison",
    "scenario_report",
    "configuration",
    "lineage",
    "validation",
}


def authenticate_portfolio_publication(path: Path, root: Path) -> PortfolioManifest:
    project_root = root.resolve()
    try:
        publication = PortfolioPublication.model_validate_json(path.read_text("utf-8"))
        manifest = PortfolioManifest.model_validate_json(
            resolve_project_path(publication.manifest_path, project_root).read_text("utf-8")
        )
    except (OSError, ValueError) as exc:
        raise EvidenceIntegrityError(f"Invalid portfolio publication evidence: {exc}") from exc
    if (
        publication.publication_id != manifest.publication_id
        or publication.manifest_hash != manifest.content_hash()
        or publication.configuration_hash != manifest.configuration_hash
        or publication.git_commit != manifest.git_commit
    ):
        raise EvidenceIntegrityError("Portfolio publication does not bind its manifest")
    names: set[str] = set()
    for artifact in manifest.artifacts:
        if artifact.name in names:
            raise EvidenceIntegrityError("Duplicate portfolio artifact name")
        names.add(artifact.name)
        content = resolve_project_path(artifact.path, project_root).read_bytes()
        if (
            len(content) != artifact.byte_size
            or hashlib.sha256(content).hexdigest() != artifact.checksum
        ):
            raise EvidenceIntegrityError(f"Portfolio artifact changed: {artifact.name}")
        if artifact.media_type == "application/json":
            value = json.loads(content)
            if isinstance(value, dict) and value.get("publication_id") not in {
                None,
                manifest.publication_id,
            }:
                raise EvidenceIntegrityError(f"Portfolio JSON identity differs: {artifact.name}")
        else:
            schema = pq.read_schema(pa.BufferReader(content))
            if tuple(schema.names) != artifact.columns:
                raise EvidenceIntegrityError(f"Portfolio schema differs: {artifact.name}")
    if names != REQUIRED:
        raise EvidenceIntegrityError("Portfolio artifact inventory is incomplete or unexpected")
    return manifest


class PortfolioRepository:
    def __init__(self, root: Path, manifest_root: Path) -> None:
        self.root = root.resolve()
        self.manifest_root = manifest_root.resolve()

    def authenticate(self, publication_id: str) -> PortfolioManifest:
        path = self.manifest_root / publication_id / "portfolio-publication.json"
        manifest = authenticate_portfolio_publication(path, self.root)
        if manifest.publication_id != publication_id:
            raise EvidenceIntegrityError("Portfolio publication path identity differs")
        return manifest

    def list_authenticated(self) -> tuple[str, ...]:
        result: list[str] = []
        for path in sorted(self.manifest_root.glob("*/portfolio-publication.json")):
            try:
                result.append(authenticate_portfolio_publication(path, self.root).publication_id)
            except (EvidenceIntegrityError, OSError, json.JSONDecodeError):
                continue
        return tuple(result)
