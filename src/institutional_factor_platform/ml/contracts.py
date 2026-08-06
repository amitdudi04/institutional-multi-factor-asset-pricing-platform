"""Versioned identity and temporal contracts for Phase 5 research."""

import hashlib
import json
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class FrozenModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    def content_hash(self) -> str:
        payload = json.dumps(self.model_dump(mode="json"), sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(payload.encode()).hexdigest()


class FeatureDefinition(FrozenModel):
    name: str
    family: str
    definition: str
    rationale: str
    source: str
    unit: str
    direction: Literal[-1, 0, 1]
    availability_policy: str
    transformation_chain: tuple[str, ...]
    missingness_policy: str
    fitted_state_scope: Literal["none", "formation_cross_section", "training_window"]
    version: str


class FeatureSchema(FrozenModel):
    schema_version: Literal["1.0.0"]
    feature_set_version: str
    features: tuple[FeatureDefinition, ...]

    @model_validator(mode="after")
    def unique_ordered_features(self) -> "FeatureSchema":
        names = [item.name for item in self.features]
        if len(names) != len(set(names)):
            raise ValueError("Feature schema contains duplicate names")
        if names != sorted(names):
            raise ValueError("Feature schema order must be deterministic")
        return self


class TargetSpecification(FrozenModel):
    schema_version: Literal["1.0.0"]
    target_type: str
    horizon: int = Field(ge=1)
    benchmark_id: str | None
    unit: str
    transformation: str
    quantiles: int | None = Field(default=None, ge=2)


class SplitAssignment(FrozenModel):
    security_id: str
    formation_date: datetime
    target_start: datetime
    target_end: datetime
    fold: int = Field(ge=0)
    partition: Literal["train", "validation", "test", "purged", "embargo"]


class PredictionRecord(FrozenModel):
    model_id: str
    run_id: str
    security_id: str
    formation_date: datetime
    decision_time: datetime
    horizon: int
    target_type: str
    prediction: float
    probability: float | None = Field(default=None, ge=0, le=1)
    rank: float | None = None
    uncertainty_method: str | None = None
    uncertainty_value: float | None = None
    feature_coverage: float = Field(ge=0, le=1)
    mapping_status: Literal["VALID"]
    model_version: str
    feature_schema_hash: str = Field(pattern=r"^[a-f0-9]{64}$")
    configuration_hash: str = Field(pattern=r"^[a-f0-9]{64}$")
    git_commit: str
    prediction_available_at: datetime


class ExplanationRecord(FrozenModel):
    model_id: str
    model_checksum: str = Field(pattern=r"^[a-f0-9]{64}$")
    prediction_checksum: str = Field(pattern=r"^[a-f0-9]{64}$")
    preprocessing_hash: str = Field(pattern=r"^[a-f0-9]{64}$")
    feature_schema_hash: str = Field(pattern=r"^[a-f0-9]{64}$")
    feature_matrix_hash: str = Field(pattern=r"^[a-f0-9]{64}$")
    security_id: str
    formation_date: datetime
    method: Literal["coefficient", "permutation", "shap"]
    library_version: str
    background_hash: str = Field(pattern=r"^[a-f0-9]{64}$")
    configuration_hash: str = Field(pattern=r"^[a-f0-9]{64}$")
    seed: int
    git_commit: str


class ModelCard(FrozenModel):
    schema_version: Literal["1.0.0"]
    model_id: str
    family: str
    task: Literal["regression", "classification", "ranking"]
    target: TargetSpecification
    intended_use: str
    prohibited_use: str
    universe: str
    training_period: tuple[str, str]
    validation_period: tuple[str, str]
    test_period: tuple[str, str]
    features: tuple[str, ...]
    preprocessing_hash: str = Field(pattern=r"^[a-f0-9]{64}$")
    hyperparameters: dict[str, object]
    seed: int
    metrics: dict[str, float | None]
    economic_evaluation: dict[str, object]
    explanations: dict[str, object]
    drift: dict[str, object]
    limitations: tuple[str, ...]
    known_failure_modes: tuple[str, ...]
    data_dependencies: tuple[str, ...]
    artifact_checksums: dict[str, str]
    configuration_hash: str = Field(pattern=r"^[a-f0-9]{64}$")
    git_commit: str
    status: Literal["EXPERIMENTAL", "VALIDATED_RESEARCH", "CHALLENGER", "REJECTED", "DEPRECATED"]
