"""Validated versioned run, source, and dataset manifests."""

import hashlib
import json
from datetime import datetime
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

from institutional_factor_platform.data.domain import DatasetStatus, RetrievalStatus
from institutional_factor_platform.exceptions import ManifestError


class ManifestModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    schema_version: str = Field(pattern=r"^\d+\.\d+\.\d+$")

    def canonical_json(self) -> str:
        return json.dumps(self.model_dump(mode="json"), sort_keys=True, separators=(",", ":"))

    def content_hash(self) -> str:
        return hashlib.sha256(self.canonical_json().encode()).hexdigest()

    def write_immutable(self, path: Path) -> None:
        content = json.dumps(self.model_dump(mode="json"), sort_keys=True, indent=2) + "\n"
        if path.exists() and path.read_text(encoding="utf-8") != content:
            raise ManifestError(f"Refusing to overwrite immutable manifest: {path}")
        path.parent.mkdir(parents=True, exist_ok=True)
        if not path.exists():
            path.write_text(content, encoding="utf-8")


class RunManifest(ManifestModel):
    run_id: str
    run_type: str
    start_time: datetime
    completion_time: datetime | None = None
    status: Literal["RUNNING", "SUCCESS", "PARTIAL", "FAILED"]
    code_version: str
    git_commit: str
    configuration_hash: str
    configuration_snapshot_path: str
    environment_version: str
    requested_sources: tuple[str, ...] = ()
    requested_datasets: tuple[str, ...] = ()
    output_artifacts: tuple[str, ...] = ()
    warnings: tuple[str, ...] = ()
    errors: tuple[str, ...] = ()


class SourceManifest(ManifestModel):
    source: str
    request: dict[str, Any]
    retrieval_time: datetime
    response_status: RetrievalStatus
    raw_artifact_path: str | None = None
    checksum: str | None = None
    row_count: int | None = Field(default=None, ge=0)
    date_start: str | None = None
    date_end: str | None = None
    partial_failures: tuple[str, ...] = ()
    rate_limit_note: str | None = None
    source_terms_note: str


class DatasetManifest(ManifestModel):
    dataset_id: str
    dataset_type: str
    schema_name: str
    parent_artifacts: tuple[str, ...]
    transformation_name: str
    transformation_version: str
    row_count: int = Field(ge=0)
    column_count: int = Field(ge=0)
    primary_key: tuple[str, ...]
    date_start: str | None = None
    date_end: str | None = None
    security_count: int | None = Field(default=None, ge=0)
    missingness_summary: dict[str, int] = Field(default_factory=dict)
    validation_status: DatasetStatus
    quarantine_status: bool
    parquet_path: str | None = None
    duckdb_registered: bool = False
    creation_time: datetime
    configuration_hash: str
    code_version: str
    lineage_references: tuple[str, ...] = ()
