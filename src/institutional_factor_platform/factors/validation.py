"""Deterministic Phase 2 factor-output validation."""

from datetime import UTC, datetime, time
from math import isfinite
from typing import Literal

import pandas as pd
from pydantic import BaseModel, ConfigDict, Field

from institutional_factor_platform.exceptions import DataQualityError, TemporalIntegrityError
from institutional_factor_platform.factors.definitions import DEFINITION_BY_ID


class FactorValidationFinding(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    rule: str
    severity: Literal["INFO", "WARNING", "ERROR", "CRITICAL"]
    message: str
    affected_count: int = Field(ge=0)


class FactorValidationReport(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    schema_version: Literal["1.0.0"]
    publication_id: str
    generated_at: datetime
    row_count: int = Field(gt=0)
    security_count: int = Field(gt=0)
    date_count: int = Field(gt=0)
    factor_count: int = Field(gt=0)
    status: Literal["PASS", "PASS_WITH_WARNINGS", "FAIL"]
    findings: tuple[FactorValidationFinding, ...]


NONNEGATIVE_FACTORS = {
    "market_cap",
    "rolling_volatility",
    "downside_volatility",
    "semi_variance",
    "idiosyncratic_volatility",
    "average_dollar_volume",
    "turnover",
    "amihud_illiquidity",
    "bid_ask_proxy",
    "tracking_error",
}
INDICATORS = {"size_small", "size_mid", "size_large"}
RETURN_FACTORS = {
    "market_return",
    "excess_return",
    "risk_free_rate",
    "momentum_1m",
    "momentum_3m",
    "momentum_6m",
    "momentum_12_1m",
    "momentum_12m",
    "momentum_24m",
    "residual_momentum",
}


def validate_factor_output(frame: pd.DataFrame, publication_id: str) -> FactorValidationReport:
    required = {
        "security_id",
        "date",
        "factor_id",
        "raw_value",
        "winsorized_value",
        "normalized_value",
        "score_value",
        "normalization_method",
        "available_at",
        "factor_version",
    }
    if set(frame.columns) != required:
        raise DataQualityError("factor output columns do not match the v1 contract")
    if frame.empty:
        raise DataQualityError("factor output is empty")
    if frame.duplicated(["security_id", "date", "factor_id"]).any():
        raise DataQualityError("factor output contains duplicate security/date/factor keys")
    if not set(frame["factor_id"]).issubset(DEFINITION_BY_ID):
        raise DataQualityError("factor output contains an undefined factor")
    cutoffs = pd.to_datetime(frame["date"]).map(
        lambda value: datetime.combine(value.date(), time.max, tzinfo=UTC)
    )
    available = pd.to_datetime(frame["available_at"], utc=True)
    if (available > cutoffs).any():
        raise TemporalIntegrityError("factor output uses evidence unavailable at computation time")
    for column in ("raw_value", "winsorized_value", "normalized_value", "score_value"):
        observed = frame[column].dropna()
        if not observed.map(isfinite).all():
            raise DataQualityError(f"factor output {column} contains non-finite values")
    if (
        frame.loc[
            frame["raw_value"].isna(),
            ["winsorized_value", "normalized_value", "score_value"],
        ]
        .notna()
        .any()
        .any()
    ):
        raise DataQualityError("factor preprocessing does not preserve missing raw values")
    for factor_id in NONNEGATIVE_FACTORS:
        if (frame.loc[frame["factor_id"].eq(factor_id), "raw_value"].dropna() < 0).any():
            raise DataQualityError(f"{factor_id} violates its nonnegative range")
    for factor_id in INDICATORS:
        values = set(frame.loc[frame["factor_id"].eq(factor_id), "raw_value"].dropna())
        if not values.issubset({0.0, 1.0}):
            raise DataQualityError(f"{factor_id} is not a binary membership indicator")
    for factor_id in RETURN_FACTORS:
        if (frame.loc[frame["factor_id"].eq(factor_id), "raw_value"].dropna() <= -1.0).any():
            raise DataQualityError(f"{factor_id} contains an impossible simple return")
    missing = int(frame["raw_value"].isna().sum())
    findings = (
        (
            FactorValidationFinding(
                rule="missing_values_preserved",
                severity="WARNING",
                message="Unavailable factor values remain null and are never imputed.",
                affected_count=missing,
            ),
        )
        if missing
        else ()
    )
    return FactorValidationReport(
        schema_version="1.0.0",
        publication_id=publication_id,
        generated_at=datetime.now(UTC),
        row_count=len(frame),
        security_count=frame["security_id"].nunique(),
        date_count=frame["date"].nunique(),
        factor_count=frame["factor_id"].nunique(),
        status="PASS_WITH_WARNINGS" if findings else "PASS",
        findings=findings,
    )
