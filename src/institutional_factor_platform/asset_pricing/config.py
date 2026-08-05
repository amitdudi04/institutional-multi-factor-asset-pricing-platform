"""Strict Phase 3 configuration and reproducible identity."""

import hashlib
import json
from pathlib import Path
from typing import Literal

import yaml
from pydantic import BaseModel, ConfigDict, Field, model_validator

from institutional_factor_platform.asset_pricing.models import MODEL_SPECS
from institutional_factor_platform.exceptions import ConfigurationError
from institutional_factor_platform.project import find_project_root


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class PublicationConfig(StrictModel):
    output_root: Path
    manifest_root: Path

    @model_validator(mode="after")
    def safe_relative_paths(self) -> "PublicationConfig":
        for value in (self.output_root, self.manifest_root):
            if value.is_absolute() or ".." in value.parts:
                raise ValueError("Phase 3 publication paths must remain project-relative")
        return self


class AssetPricingConfig(StrictModel):
    schema_version: Literal["1.0.0"]
    frequency: Literal["monthly"]
    annualization_periods: int = Field(gt=0)
    minimum_observations: int = Field(ge=8)
    confidence_level: float = Field(gt=0.5, lt=1.0)
    hac_lags: int = Field(ge=0)
    rolling_window: int = Field(ge=8)
    expanding_minimum: int = Field(ge=8)
    models: dict[str, tuple[str, ...]]
    factor_mappings: dict[str, str]
    publication: PublicationConfig

    @model_validator(mode="after")
    def coherent(self) -> "AssetPricingConfig":
        if self.expanding_minimum < self.minimum_observations:
            raise ValueError("expanding minimum cannot be below the observation minimum")
        if self.rolling_window < self.minimum_observations:
            raise ValueError("rolling window cannot be below the observation minimum")
        for model_id, factors in self.models.items():
            if model_id not in MODEL_SPECS or tuple(factors) != MODEL_SPECS[model_id].factors:
                raise ValueError(f"model mapping contradicts approved specification: {model_id}")
        required = {factor for values in self.models.values() for factor in values}
        if required - {"market_excess"} - set(self.factor_mappings):
            raise ValueError("every non-market model factor requires an explicit Phase 2 mapping")
        return self

    def canonical_hash(self) -> str:
        payload = json.dumps(self.model_dump(mode="json"), sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(payload.encode()).hexdigest()


def load_asset_pricing_config(path: Path | None = None) -> AssetPricingConfig:
    config_path = (path or find_project_root() / "config" / "asset_pricing.yaml").resolve()
    try:
        return AssetPricingConfig.model_validate(yaml.safe_load(config_path.read_text("utf-8")))
    except (OSError, yaml.YAMLError, ValueError) as exc:
        raise ConfigurationError(
            f"Invalid asset-pricing configuration {config_path}: {exc}"
        ) from exc
