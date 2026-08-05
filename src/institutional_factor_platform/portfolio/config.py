"""Strict Phase 4 portfolio configuration without invented open-decision values."""

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


class ConstraintConfig(StrictModel):
    long_only: Literal[True]
    leverage_limit: float = Field(ge=1.0, le=1.0)
    minimum_weight: float = Field(ge=0, le=1)
    maximum_weight: float | None = Field(default=None, gt=0, le=1)
    turnover_limit: float | None = Field(default=None, ge=0, le=2)
    transaction_cost_limit: float | None = Field(default=None, ge=0)
    sector_limits: dict[str, float]
    exposure_limits: dict[str, tuple[float, float]]
    liquidity_trade_limits: dict[str, float]


class CostConfig(StrictModel):
    commission_bps: float | None = Field(default=None, ge=0)
    spread_bps: float | None = Field(default=None, ge=0)
    slippage_bps: float | None = Field(default=None, ge=0)
    market_impact_coefficient: float | None = Field(default=None, ge=0)

    def require_explicit(self) -> tuple[float, float, float, float]:
        values = (
            self.commission_bps,
            self.spread_bps,
            self.slippage_bps,
            self.market_impact_coefficient,
        )
        if any(value is None for value in values):
            raise ConfigurationError(
                "Transaction-cost values are open owner decisions and must be explicit for a run"
            )
        return values  # type: ignore[return-value]


class PublicationConfig(StrictModel):
    output_root: Path
    manifest_root: Path

    @model_validator(mode="after")
    def paths_are_safe(self) -> "PublicationConfig":
        for value in (self.output_root, self.manifest_root):
            if value.is_absolute() or ".." in value.parts:
                raise ValueError("Portfolio publication paths must remain project-relative")
        return self


class PortfolioConfig(StrictModel):
    schema_version: Literal["1.0.0"]
    frequency: Literal["monthly"]
    annualization_periods: int = Field(gt=0)
    estimation_window: int = Field(ge=3)
    minimum_observations: int = Field(ge=3)
    covariance_method: Literal["sample", "ledoit_wolf", "robust"]
    constraints: ConstraintConfig
    costs: CostConfig
    publication: PublicationConfig

    @model_validator(mode="after")
    def windows_are_coherent(self) -> "PortfolioConfig":
        if self.minimum_observations > self.estimation_window:
            raise ValueError("Minimum observations cannot exceed estimation window")
        return self

    def canonical_hash(self) -> str:
        payload = json.dumps(self.model_dump(mode="json"), sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(payload.encode()).hexdigest()


def load_portfolio_config(path: Path | None = None) -> PortfolioConfig:
    config_path = (path or find_project_root() / "config" / "portfolio.yaml").resolve()
    try:
        return PortfolioConfig.model_validate(yaml.safe_load(config_path.read_text("utf-8")))
    except (OSError, yaml.YAMLError, ValueError) as exc:
        raise ConfigurationError(f"Invalid portfolio configuration {config_path}: {exc}") from exc
