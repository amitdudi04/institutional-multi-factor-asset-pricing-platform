"""Typed, strict Phase 1 configuration and reproducibility helpers."""

import hashlib
import json
import os
from datetime import date
from pathlib import Path
from typing import Literal

import yaml
from pydantic import BaseModel, ConfigDict, Field, SecretStr, model_validator

from institutional_factor_platform.configuration import load_configuration
from institutional_factor_platform.exceptions import ConfigurationError
from institutional_factor_platform.project import find_project_root


class StrictModel(BaseModel):
    """Base configuration model that rejects unknown fields."""

    model_config = ConfigDict(extra="forbid", frozen=True)


class ProjectSettings(StrictModel):
    name: str = "institutional-factor-platform"
    environment: str
    base_currency: Literal["USD"]
    research_frequency: Literal["daily"]
    start_date: date
    end_date: date | None = None

    @model_validator(mode="after")
    def dates_are_ordered(self) -> "ProjectSettings":
        if self.end_date is not None and self.end_date < self.start_date:
            raise ValueError("project.end_date must not precede project.start_date")
        return self


class PathSettings(StrictModel):
    raw: Path
    interim: Path
    processed: Path
    manifests: Path
    quarantine: Path
    data_quality: Path
    metadata: Path
    logs: Path
    duckdb: Path

    def resolved(self, root: Path) -> dict[str, Path]:
        result: dict[str, Path] = {}
        for name, value in self:
            path = Path(value)
            resolved = (root / path).resolve() if not path.is_absolute() else path.resolve()
            if root.resolve() not in (resolved, *resolved.parents):
                raise ConfigurationError(f"paths.{name} escapes project root: {value}")
            result[name] = resolved
        return result


class UniverseSettings(StrictModel):
    country: Literal["US"]
    currency: Literal["USD"]
    allowed_asset_types: tuple[Literal["common_stock"], ...]
    allowed_cap_bands: tuple[Literal["large_cap", "mid_cap"], ...]
    include_financials: bool = True
    include_reits: bool = False
    primary_listings_only: bool = True
    excluded_listing_types: tuple[str, ...]


class YahooSettings(StrictModel):
    enabled: bool
    interval: Literal["1d"] = "1d"
    benchmark_ticker: str = "SPY"


class FredSettings(StrictModel):
    enabled: bool
    series_ids: tuple[str, ...] = ("DGS3MO",)
    api_key: SecretStr | None = None

    @model_validator(mode="after")
    def series_are_approved(self) -> "FredSettings":
        allowed = {"DGS3MO", "TB3MS"}
        invalid = set(self.series_ids) - allowed
        if invalid:
            raise ValueError(f"unapproved FRED series: {sorted(invalid)}")
        return self


class FrenchSettings(StrictModel):
    enabled: bool
    datasets: tuple[str, ...]


class SecSettings(StrictModel):
    enabled: bool
    application_name: str
    contact_email: str | None = None

    def require_live_user_agent(self) -> str:
        if not self.contact_email or "@" not in self.contact_email:
            raise ConfigurationError(
                "Live SEC retrieval requires IFP_SEC_CONTACT_EMAIL "
                "with the owner's valid contact email."
            )
        return f"{self.application_name} {self.contact_email}"


class SourceSettings(StrictModel):
    allowed: tuple[
        Literal["owner_supplied", "yahoo_finance", "fred", "kenneth_french", "sec_edgar"], ...
    ]
    yahoo: YahooSettings
    fred: FredSettings
    french: FrenchSettings
    sec: SecSettings


class StorageSettings(StrictModel):
    parquet_compression: Literal["zstd", "snappy"] = "zstd"
    raw_immutable: Literal[True] = True
    duckdb_read_only_default: bool = True


class VersionSettings(StrictModel):
    schema_version: str = Field(pattern=r"^\d+\.\d+\.\d+$")


class ValidationSettings(VersionSettings):
    extreme_return_threshold: float = Field(gt=0)
    stale_price_sessions: int = Field(gt=0)
    market_coverage_warning_ratio: float = Field(gt=0, le=1)
    market_coverage_critical_ratio: float = Field(gt=0, le=1)

    @model_validator(mode="after")
    def coverage_thresholds_are_ordered(self) -> "ValidationSettings":
        if self.market_coverage_critical_ratio > self.market_coverage_warning_ratio:
            raise ValueError("critical coverage ratio cannot exceed warning ratio")
        return self


class CalendarSettings(StrictModel):
    equity_calendar: Literal["XNYS"]
    storage_timezone: Literal["UTC"]
    exchange_timezone: Literal["America/New_York"]


class RuntimeSettings(StrictModel):
    timeout_seconds: float = Field(gt=0)
    max_retries: int = Field(ge=0, le=10)
    backoff_seconds: float = Field(ge=0)
    jitter_seconds: float = Field(ge=0)


class RetentionSettings(StrictModel):
    raw_retention: Literal["retain_until_owner_deletion"]
    local_owner_only: Literal[True]
    public_serving: Literal[False]
    redistribution: Literal[False]


class LoggingSettings(StrictModel):
    level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
    format: Literal["json", "text"]


class Phase1Config(StrictModel):
    project: ProjectSettings
    paths: PathSettings
    universe: UniverseSettings
    sources: SourceSettings
    storage: StorageSettings
    manifests: VersionSettings
    validation: ValidationSettings
    calendars: CalendarSettings
    runtime: RuntimeSettings
    retention: RetentionSettings
    logging: LoggingSettings

    def canonical_json(self) -> str:
        return json.dumps(self.model_dump(mode="json"), sort_keys=True, separators=(",", ":"))

    def configuration_hash(self) -> str:
        return hashlib.sha256(self.canonical_json().encode()).hexdigest()

    def redacted_dict(self) -> dict[str, object]:
        data = self.model_dump(mode="json")
        fred = data["sources"]["fred"]
        if isinstance(fred, dict) and fred.get("api_key") is not None:
            fred["api_key"] = "**********"
        sec = data["sources"]["sec"]
        if isinstance(sec, dict) and sec.get("contact_email"):
            sec["contact_email"] = "[REDACTED]"
        return data

    def write_snapshot(self, path: Path) -> str:
        content = json.dumps(self.redacted_dict(), sort_keys=True, indent=2) + "\n"
        if path.exists():
            if path.read_text(encoding="utf-8") != content:
                raise ConfigurationError(f"Configuration snapshot is immutable: {path}")
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding="utf-8")
        return hashlib.sha256(content.encode()).hexdigest()


def load_phase1_config(path: Path | None = None) -> Phase1Config:
    """Load and validate Phase 1 configuration using the existing YAML loader."""
    try:
        data = load_configuration(path)
        sources = data.get("sources")
        if isinstance(sources, dict):
            sec = sources.get("sec")
            if isinstance(sec, dict) and os.environ.get("IFP_SEC_CONTACT_EMAIL"):
                sec["contact_email"] = os.environ["IFP_SEC_CONTACT_EMAIL"]
            fred = sources.get("fred")
            if isinstance(fred, dict) and os.environ.get("IFP_FRED_API_KEY"):
                fred["api_key"] = os.environ["IFP_FRED_API_KEY"]
        return Phase1Config.model_validate(data)
    except ValueError as exc:
        raise ConfigurationError(f"Invalid Phase 1 configuration: {exc}") from exc


def write_config_example(path: Path, config: Phase1Config | None = None) -> None:
    """Write a redacted human-readable example, refusing to overwrite."""
    if path.exists():
        raise ConfigurationError(f"Refusing to overwrite configuration example: {path}")
    value = (
        config or load_phase1_config(find_project_root() / "config" / "base.yaml")
    ).redacted_dict()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(value, sort_keys=False), encoding="utf-8")
