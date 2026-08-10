"""Strict Phase 5 configuration; unresolved empirical choices remain unset."""

import hashlib
import json
from pathlib import Path
from typing import Literal

import yaml
from pydantic import BaseModel, ConfigDict, Field, model_validator

from institutional_factor_platform.exceptions import ConfigurationError
from institutional_factor_platform.project import find_project_root


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class InputConfig(StrictModel):
    phase2_publication_id: str | None = None
    phase3_publication_id: str | None = None
    phase4_publication_id: str | None = None


class FeatureConfig(StrictModel):
    families: tuple[str, ...] = ()
    value_column: Literal["raw_value", "winsorized_value", "normalized_value", "score_value"]
    interactions: tuple[tuple[str, str], ...] = ()
    minimum_coverage: float = Field(ge=0, le=1)


class TargetConfig(StrictModel):
    kind: (
        Literal[
            "future_return",
            "future_excess_return",
            "percentile_rank",
            "ordinal_rank",
            "quantile_bucket",
            "outperformance",
            "future_volatility",
            "future_downside_volatility",
            "future_drawdown",
            "future_risk_quantile",
        ]
        | None
    ) = None
    horizon: int | None = Field(default=None, ge=1)
    benchmark_id: str | None = None
    threshold: float | None = None
    quantiles: int = Field(default=5, ge=2, le=20)
    annualization_periods: int = Field(default=252, ge=1)
    minimum_acceptable_return: float = 0.0
    risk_quantile_alpha: float = Field(default=0.05, gt=0, lt=1)

    def require_explicit(self) -> tuple[str, int]:
        if self.kind is None or self.horizon is None:
            raise ConfigurationError(
                "ML target and horizon are open owner decisions and must be explicit for a run"
            )
        if self.kind in {"future_excess_return", "outperformance"} and not self.benchmark_id:
            raise ConfigurationError("Benchmark identity is required for this target")
        return self.kind, self.horizon


class MissingConfig(StrictModel):
    policy: Literal["reject", "training_median", "cross_sectional_median", "native"]
    add_indicators: bool = False


class PreprocessingConfig(StrictModel):
    scaling: Literal["none", "standard", "robust", "percentile", "rank"]
    winsor_lower: float | None = Field(default=None, ge=0, le=0.5)
    winsor_upper: float | None = Field(default=None, ge=0.5, le=1)

    @model_validator(mode="after")
    def coherent_winsorization(self) -> "PreprocessingConfig":
        if (self.winsor_lower is None) != (self.winsor_upper is None):
            raise ValueError("Both winsorization bounds must be provided together")
        if self.winsor_lower is not None and self.winsor_lower >= self.winsor_upper:  # type: ignore[operator]
            raise ValueError("Winsorization bounds are reversed")
        return self


class SplitConfig(StrictModel):
    method: Literal["holdout", "expanding", "rolling", "walk_forward"]
    train_periods: int = Field(ge=2)
    validation_periods: int = Field(ge=1)
    test_periods: int = Field(ge=1)
    rolling_periods: int | None = Field(default=None, ge=2)
    purge_overlaps: bool = True
    embargo_periods: int = Field(default=0, ge=0)
    retrain_every: int = Field(default=1, ge=1)


class ModelConfig(StrictModel):
    enabled: tuple[
        Literal[
            "zero",
            "historical_mean",
            "factor_composite",
            "linear",
            "logistic",
            "ridge",
            "lasso",
            "elastic_net",
            "random_forest",
            "xgboost",
        ],
        ...,
    ]
    random_seed: int = Field(ge=0)
    thread_limit: int = Field(default=1, ge=1, le=8)


class SearchConfig(StrictModel):
    method: Literal["grid", "random"]
    maximum_trials: int = Field(ge=1, le=100)
    selection_metric: str
    tie_break: Literal["simpler", "first"] = "simpler"
    spaces: dict[str, dict[str, tuple[object, ...]]] = Field(default_factory=dict)


class CalibrationConfig(StrictModel):
    method: Literal["none", "sigmoid", "isotonic"]
    minimum_samples: int = Field(ge=10)


class ExplainabilityConfig(StrictModel):
    enabled: bool
    sample_size: int = Field(ge=1, le=10_000)
    background_size: int = Field(ge=1, le=5_000)
    random_seed: int = Field(ge=0)


class DriftConfig(StrictModel):
    psi_bins: int = Field(ge=2, le=50)
    warning_threshold: float = Field(gt=0)


class EconomicConfig(StrictModel):
    enabled: bool
    portfolio_method: Literal["equal_weight"] = "equal_weight"
    selection_quantile: float | None = Field(default=None, gt=0, lt=1)


class PublicationConfig(StrictModel):
    output_root: Path
    manifest_root: Path

    @model_validator(mode="after")
    def safe_paths(self) -> "PublicationConfig":
        for path in (self.output_root, self.manifest_root):
            if path.is_absolute() or ".." in path.parts:
                raise ValueError("ML publication paths must remain project-relative")
        return self


class MachineLearningConfig(StrictModel):
    schema_version: Literal["1.0.0"]
    inputs: InputConfig
    features: FeatureConfig
    target: TargetConfig
    missing: MissingConfig
    preprocessing: PreprocessingConfig
    split: SplitConfig
    models: ModelConfig
    search: SearchConfig
    calibration: CalibrationConfig
    explainability: ExplainabilityConfig
    drift: DriftConfig
    economic_evaluation: EconomicConfig
    publication: PublicationConfig

    def canonical_hash(self) -> str:
        payload = json.dumps(self.model_dump(mode="json"), sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(payload.encode()).hexdigest()


def load_ml_config(path: Path | None = None) -> MachineLearningConfig:
    config_path = (path or find_project_root() / "config" / "machine_learning.yaml").resolve()
    try:
        return MachineLearningConfig.model_validate(yaml.safe_load(config_path.read_text("utf-8")))
    except (OSError, yaml.YAMLError, ValueError) as exc:
        raise ConfigurationError(f"Invalid ML configuration {config_path}: {exc}") from exc
