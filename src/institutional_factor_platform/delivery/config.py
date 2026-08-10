"""Strict configuration and safe runtime policy for Phase 6 delivery."""

import hashlib
import ipaddress
import json
import os
from pathlib import Path
from typing import Literal

import yaml
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from institutional_factor_platform.exceptions import ConfigurationError
from institutional_factor_platform.project import find_project_root


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class APIConfig(StrictModel):
    host: str
    port: int = Field(ge=1024, le=65535)
    prefix: str = Field(pattern=r"^/[a-z0-9/-]+$")
    allow_non_loopback: bool
    unsafe_development_anonymous_non_loopback: bool
    authentication: Literal["disabled", "optional", "required"]
    token_environment_variable: str = Field(pattern=r"^[A-Z][A-Z0-9_]{2,63}$")
    allowed_origins: tuple[str, ...]
    trusted_hosts: tuple[str, ...] = Field(min_length=1)
    maximum_request_bytes: int = Field(ge=1024, le=10_485_760)
    default_page_size: int = Field(ge=1)
    maximum_page_size: int = Field(ge=1, le=5000)
    timeout_seconds: int = Field(ge=1, le=300)
    requests_per_minute: int = Field(ge=1, le=10000)

    @field_validator("allowed_origins")
    @classmethod
    def secure_origins(cls, values: tuple[str, ...]) -> tuple[str, ...]:
        if "*" in values:
            raise ValueError("wildcard CORS origins are forbidden")
        return values

    @model_validator(mode="after")
    def coherent_pagination(self) -> "APIConfig":
        if self.default_page_size > self.maximum_page_size:
            raise ValueError("default page size exceeds maximum")
        return self

    def token(self) -> str | None:
        value = os.environ.get(self.token_environment_variable)
        if value is not None and not value.strip():
            raise ConfigurationError("Configured bearer token cannot be empty")
        return value

    def validate_binding(self) -> None:
        try:
            loopback = ipaddress.ip_address(self.host).is_loopback
        except ValueError:
            loopback = self.host.lower() == "localhost"
        if loopback:
            return
        if not self.allow_non_loopback:
            raise ConfigurationError("Non-loopback API binding requires explicit authorization")
        if self.token() is None and not self.unsafe_development_anonymous_non_loopback:
            raise ConfigurationError("Anonymous non-loopback API binding is forbidden")


class DashboardConfig(StrictModel):
    api_url: str = Field(pattern=r"^https?://[^\s]+/api/v[0-9]+$")
    maximum_chart_rows: int = Field(ge=1, le=100000)


class ReportConfig(StrictModel):
    output_directory: Path
    maximum_rows: int = Field(ge=1, le=1_000_000)
    allowed_formats: tuple[Literal["markdown", "html", "json", "csv"], ...]

    @field_validator("output_directory")
    @classmethod
    def project_relative(cls, value: Path) -> Path:
        if value.is_absolute() or ".." in value.parts:
            raise ValueError("report output must be project-relative and confined")
        return value


class CacheConfig(StrictModel):
    enabled: bool
    maximum_entries: int = Field(ge=1, le=10000)


class LoggingConfig(StrictModel):
    level: Literal["DEBUG", "INFO", "WARNING", "ERROR"]
    format: Literal["json", "text"]


class FeatureConfig(StrictModel):
    reports: bool
    exports: bool


class DeliveryConfig(StrictModel):
    schema_version: Literal["1.0.0"]
    environment: Literal["local", "development", "container"]
    api: APIConfig
    dashboard: DashboardConfig
    reports: ReportConfig
    cache: CacheConfig
    logging: LoggingConfig
    features: FeatureConfig

    def canonical_hash(self) -> str:
        payload = json.dumps(self.model_dump(mode="json"), sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(payload.encode()).hexdigest()


def load_delivery_config(path: Path | None = None) -> DeliveryConfig:
    root = find_project_root()
    environment_path = os.environ.get("IFP_DELIVERY_CONFIG")
    location = path or (
        Path(environment_path) if environment_path else root / "config" / "delivery.yaml"
    )
    try:
        value = yaml.safe_load(location.read_text(encoding="utf-8"))
        config = DeliveryConfig.model_validate(value)
        config.api.validate_binding()
        return config
    except ConfigurationError:
        raise
    except (OSError, ValueError, yaml.YAMLError) as exc:
        raise ConfigurationError(f"Invalid delivery configuration: {exc}") from exc
