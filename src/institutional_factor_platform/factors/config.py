"""Strict, reproducible Phase 2 factor-engine configuration."""

import hashlib
import json
from pathlib import Path
from typing import Literal

import yaml
from pydantic import BaseModel, ConfigDict, Field, model_validator

from institutional_factor_platform.data.evidence import atomic_write_json
from institutional_factor_platform.exceptions import ConfigurationError
from institutional_factor_platform.project import find_project_root


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class WindowConfig(StrictModel):
    short: int = Field(ge=2)
    medium: int = Field(gt=2)
    half_year: int = Field(gt=2)
    one_year: int = Field(gt=2)
    two_year: int = Field(gt=2)
    minimum_observations: int = Field(ge=2)

    @model_validator(mode="after")
    def ordered(self) -> "WindowConfig":
        values = (self.short, self.medium, self.half_year, self.one_year, self.two_year)
        if tuple(sorted(values)) != values or len(set(values)) != len(values):
            raise ValueError("factor windows must be strictly increasing")
        if self.minimum_observations > self.short:
            raise ValueError("minimum observations cannot exceed the shortest window")
        return self


class PreprocessingConfig(StrictModel):
    method: Literal["none", "winsorized", "robust_zscore", "zscore", "minmax", "rank", "percentile"]
    neutralize_by: Literal["none", "sector", "industry"]
    winsor_lower: float = Field(ge=0.0, lt=0.5)
    winsor_upper: float = Field(gt=0.5, le=1.0)
    minimum_cross_section: int = Field(ge=2)
    ddof: Literal[0, 1]

    @model_validator(mode="after")
    def quantiles_ordered(self) -> "PreprocessingConfig":
        if self.winsor_lower >= self.winsor_upper:
            raise ValueError("winsorization quantiles are reversed")
        return self


class BreakpointConfig(StrictModel):
    exchange: str = Field(min_length=1)
    small_quantile: float = Field(gt=0.0, lt=0.5)
    large_quantile: float = Field(gt=0.5, lt=1.0)


class ReturnPlausibilityConfig(StrictModel):
    max_abs_security_return: float = Field(gt=0.0)
    max_abs_market_return: float = Field(gt=0.0)
    max_abs_risk_free: float = Field(gt=0.0)


class PortfolioConfig(StrictModel):
    quantiles: int = Field(ge=2, le=10)
    weighting: Literal["value_weighted"]
    rolling_periods: int = Field(ge=2)


class FactorPublicationConfig(StrictModel):
    output_root: Path
    manifest_root: Path

    @model_validator(mode="after")
    def paths_are_relative(self) -> "FactorPublicationConfig":
        if self.output_root.is_absolute() or self.manifest_root.is_absolute():
            raise ValueError("factor publication paths must be project-relative")
        if ".." in self.output_root.parts or ".." in self.manifest_root.parts:
            raise ValueError("factor publication paths cannot escape the project root")
        return self


class FactorConfig(StrictModel):
    schema_version: Literal["1.0.0"]
    frequency: Literal["daily"]
    rebalancing: Literal["monthly"]
    annualization_periods: int = Field(gt=0)
    plausibility: ReturnPlausibilityConfig
    windows: WindowConfig
    preprocessing: PreprocessingConfig
    breakpoints: BreakpointConfig
    portfolios: PortfolioConfig
    publication: FactorPublicationConfig

    def canonical_hash(self) -> str:
        payload = json.dumps(
            self.model_dump(mode="json"), sort_keys=True, separators=(",", ":")
        ).encode()
        return hashlib.sha256(payload).hexdigest()

    def write_snapshot(self, path: Path) -> None:
        atomic_write_json(path, self.model_dump(mode="json"))


def load_factor_config(path: Path | None = None) -> FactorConfig:
    config_path = (path or find_project_root() / "config" / "factors.yaml").resolve()
    try:
        value = yaml.safe_load(config_path.read_text(encoding="utf-8"))
        return FactorConfig.model_validate(value)
    except (OSError, yaml.YAMLError, ValueError) as exc:
        raise ConfigurationError(f"Invalid factor configuration {config_path}: {exc}") from exc
