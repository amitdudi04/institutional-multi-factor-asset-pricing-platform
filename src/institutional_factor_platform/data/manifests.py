"""Validated, immutable Phase 1 lifecycle and evidence manifests (schema v2)."""

import hashlib
import json
from datetime import datetime
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from institutional_factor_platform.data.domain import DatasetStatus, RetrievalStatus
from institutional_factor_platform.exceptions import ManifestError


class ManifestModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    schema_version: Literal["2.0.0"]

    def canonical_json(self) -> str:
        return json.dumps(self.model_dump(mode="json"), sort_keys=True, separators=(",", ":"))

    def content_hash(self) -> str:
        return hashlib.sha256(self.canonical_json().encode()).hexdigest()

    def write_immutable(self, path: Path) -> None:
        content = json.dumps(self.model_dump(mode="json"), sort_keys=True, indent=2) + "\n"
        if path.exists():
            if path.read_text(encoding="utf-8") != content:
                raise ManifestError(f"Refusing to overwrite immutable manifest: {path}")
            return
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")


class RunManifest(ManifestModel):
    run_id: str
    attempt: int = Field(default=1, ge=1)
    parent_run_id: str | None = None
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

    @model_validator(mode="after")
    def lifecycle_is_coherent(self) -> "RunManifest":
        if self.status == "RUNNING" and self.completion_time is not None:
            raise ValueError("running manifest cannot have a completion time")
        if self.status != "RUNNING" and self.completion_time is None:
            raise ValueError("terminal manifest requires a completion time")
        if self.completion_time is not None and self.completion_time < self.start_time:
            raise ValueError("completion time cannot precede start time")
        if self.status == "SUCCESS" and not self.output_artifacts:
            raise ValueError("successful run requires output artifacts")
        if self.status == "FAILED" and not self.errors:
            raise ValueError("failed run requires error evidence")
        return self


class SourceManifest(ManifestModel):
    source_manifest_id: str
    source: str
    request: dict[str, Any]
    retrieval_time: datetime
    response_status: RetrievalStatus
    response_metadata: dict[str, Any] = Field(default_factory=dict)
    raw_artifact_id: str | None = None
    raw_artifact_path: str | None = None
    checksum: str | None = Field(default=None, pattern=r"^[a-f0-9]{64}$")
    byte_size: int | None = Field(default=None, ge=0)
    media_type: str | None = None
    row_count: int | None = Field(default=None, ge=0)
    requested_start: str | None = None
    requested_end: str | None = None
    returned_start: str | None = None
    returned_end: str | None = None
    partial_failures: tuple[str, ...] = ()
    rate_limit_note: str | None = None
    source_terms_note: str

    @model_validator(mode="after")
    def successful_source_has_raw_evidence(self) -> "SourceManifest":
        if self.response_status is RetrievalStatus.SUCCESS:
            required = (self.raw_artifact_id, self.raw_artifact_path, self.checksum, self.byte_size)
            if any(value is None for value in required) or self.row_count in (None, 0):
                raise ValueError("successful source manifest requires non-empty raw/row evidence")
        return self


class DatasetManifest(ManifestModel):
    dataset_id: str
    dataset_type: str
    schema_name: str
    schema_fingerprint: str = Field(pattern=r"^[a-f0-9]{64}$")
    parent_artifacts: tuple[str, ...]
    source_manifest_id: str
    transformation_name: str
    transformation_version: str = Field(pattern=r"^\d+\.\d+\.\d+$")
    row_count: int = Field(gt=0)
    column_count: int = Field(gt=0)
    primary_key: tuple[str, ...]
    date_start: str | None = None
    date_end: str | None = None
    security_count: int | None = Field(default=None, ge=0)
    missingness_summary: dict[str, int] = Field(default_factory=dict)
    unit_metadata: dict[str, str] = Field(default_factory=dict)
    validation_report_id: str
    validation_report_path: str
    validation_status: DatasetStatus
    lineage_path: str
    lineage_complete: bool
    quarantine_status: bool
    parquet_path: str
    output_checksum: str = Field(pattern=r"^[a-f0-9]{64}$")
    output_byte_size: int = Field(gt=0)
    catalog_registration_state: Literal["NOT_REGISTERED", "REGISTERED"]
    promotion_state: Literal["NOT_ELIGIBLE", "ELIGIBLE", "PUBLISHED"]
    creation_time: datetime
    configuration_hash: str = Field(pattern=r"^[a-f0-9]{64}$")
    code_version: str
    git_commit: str
    temporal_policy_version: str

    @model_validator(mode="after")
    def promotion_evidence_is_complete(self) -> "DatasetManifest":
        eligible = self.validation_status in {
            DatasetStatus.PASS,
            DatasetStatus.PASS_WITH_WARNINGS,
        }
        if self.promotion_state in {"ELIGIBLE", "PUBLISHED"}:
            if not eligible or self.quarantine_status or not self.lineage_complete:
                raise ValueError("promotion requires eligible validation and complete lineage")
        if self.promotion_state == "PUBLISHED" and self.catalog_registration_state != "REGISTERED":
            raise ValueError("published dataset must be registered")
        if self.validation_status is DatasetStatus.QUARANTINED and not self.quarantine_status:
            raise ValueError("quarantined status requires quarantine evidence")
        return self


class PromotionManifest(ManifestModel):
    dataset_id: str
    dataset_manifest_path: str
    dataset_manifest_hash: str = Field(pattern=r"^[a-f0-9]{64}$")
    output_checksum: str = Field(pattern=r"^[a-f0-9]{64}$")
    lineage_path: str
    validation_status: DatasetStatus
    promoted_at: datetime
    git_commit: str
    configuration_hash: str = Field(pattern=r"^[a-f0-9]{64}$")
