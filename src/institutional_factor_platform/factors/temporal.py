"""Point-in-time alignment and anti-leakage validation for Phase 2."""

import re
from datetime import UTC, datetime, time
from math import isfinite, nan

import pandas as pd
import pyarrow as pa

from institutional_factor_platform.exceptions import DataQualityError, TemporalIntegrityError
from institutional_factor_platform.factors.contracts import FUNDAMENTAL_SCHEMA, MARKET_SCHEMA


def _require_columns(frame: pd.DataFrame, schema: pa.Schema, label: str) -> None:
    missing = set(schema.names) - set(frame.columns)
    extra = set(frame.columns) - set(schema.names)
    if missing or extra:
        raise DataQualityError(
            f"{label} columns do not match contract; missing={sorted(missing)}, "
            f"extra={sorted(extra)}"
        )


def validate_market_input(frame: pd.DataFrame, parent_ids: set[str]) -> pd.DataFrame:
    _require_columns(frame, MARKET_SCHEMA, "market input")
    value = frame.copy()
    value["date"] = pd.to_datetime(value["date"]).dt.date
    value["available_at"] = pd.to_datetime(value["available_at"], utc=True).astype(
        "datetime64[ns, UTC]"
    )
    value["eligibility_available_at"] = pd.to_datetime(
        value["eligibility_available_at"], utc=True
    ).astype("datetime64[ns, UTC]")
    value["classification_available_at"] = pd.to_datetime(
        value["classification_available_at"], utc=True
    ).astype("datetime64[ns, UTC]")
    if value.empty:
        raise DataQualityError("market input is empty")
    if value.duplicated(["security_id", "date"]).any():
        raise DataQualityError("market input has duplicate security/date keys")
    if value["security_id"].isna().any() or value["date"].isna().any():
        raise DataQualityError("market input has null primary keys")
    if (
        not value["security_id"]
        .map(lambda item: bool(re.fullmatch(r"sec_[a-f0-9]{32}", item)))
        .all()
    ):
        raise DataQualityError("market input contains an invalid canonical security identifier")
    cutoffs = pd.to_datetime(value["date"]).map(
        lambda date_value: datetime.combine(date_value.date(), time.max, tzinfo=UTC)
    )
    if (
        (value["available_at"] > cutoffs).any()
        or (value["eligibility_available_at"] > cutoffs).any()
        or (value["classification_available_at"] > cutoffs).any()
    ):
        raise TemporalIntegrityError("market input is not available on its computation date")
    if value["eligible"].isna().any():
        raise DataQualityError("point-in-time universe eligibility is required")
    if value[["sector", "industry"]].isna().any().any():
        raise DataQualityError("point-in-time sector and industry classifications are required")
    if not set(value["source_dataset_id"]).issubset(parent_ids):
        raise DataQualityError("market input references an unauthenticated parent dataset")
    for column in ("return", "market_return", "risk_free", "benchmark_return"):
        finite = value[column].dropna()
        if not finite.map(isfinite).all() or (finite <= -1.0).any():
            raise DataQualityError(f"{column} contains invalid decimal returns")
    for column in ("price", "high", "low", "volume", "shares_outstanding"):
        if (value[column].dropna() < 0).any():
            raise DataQualityError(f"{column} contains negative values")
    if (value["high"].dropna() < value["low"].dropna()).any():
        raise DataQualityError("market high is below low")
    return value.sort_values(["security_id", "date"]).reset_index(drop=True)


def validate_fundamental_input(frame: pd.DataFrame, parent_ids: set[str]) -> pd.DataFrame:
    _require_columns(frame, FUNDAMENTAL_SCHEMA, "fundamental input")
    value = frame.copy()
    value["period_end"] = pd.to_datetime(value["period_end"]).dt.date
    value["available_at"] = pd.to_datetime(value["available_at"], utc=True).astype(
        "datetime64[ns, UTC]"
    )
    if value.duplicated(["security_id", "available_at", "field"]).any():
        raise DataQualityError("fundamental input has duplicate point-in-time keys")
    if not set(value["source_dataset_id"]).issubset(parent_ids):
        raise DataQualityError("fundamental input references an unauthenticated parent dataset")
    availability_dates = value["available_at"].dt.date
    if (value["period_end"] > availability_dates).any():
        raise TemporalIntegrityError("fundamental period ends after its availability")
    if not value["value"].map(isfinite).all():
        raise DataQualityError("fundamental input contains non-finite values")
    if value[["security_id", "field", "unit"]].isna().any().any():
        raise DataQualityError("fundamental identity, field, and unit are required")
    if (
        not value["security_id"]
        .map(lambda item: bool(re.fullmatch(r"sec_[a-f0-9]{32}", item)))
        .all()
    ):
        raise DataQualityError(
            "fundamental input contains an invalid canonical security identifier"
        )
    return value.sort_values(["security_id", "available_at", "field"]).reset_index(drop=True)


def point_in_time_panel(market: pd.DataFrame, fundamentals: pd.DataFrame) -> pd.DataFrame:
    """As-of join each reported field with no forward publication use."""
    panel = market.copy()
    panel["available_at"] = pd.to_datetime(panel["available_at"], utc=True)
    panel["eligibility_available_at"] = pd.to_datetime(panel["eligibility_available_at"], utc=True)
    panel["available_at"] = panel[["available_at", "eligibility_available_at"]].max(axis=1)
    panel["available_at"] = panel[["available_at", "classification_available_at"]].max(axis=1)
    panel["computation_cutoff"] = pd.to_datetime(panel["date"]).map(
        lambda value: datetime.combine(value.date(), time.max, tzinfo=UTC)
    )
    panel["fundamental_available_at_max"] = pd.Series(
        pd.NaT, index=panel.index, dtype="datetime64[ns, UTC]"
    )
    for field_name in sorted(fundamentals["field"].unique()):
        field = fundamentals.loc[
            fundamentals["field"].eq(field_name),
            ["security_id", "available_at", "value"],
        ].rename(columns={"available_at": "fundamental_available_at", "value": field_name})
        parts: list[pd.DataFrame] = []
        for security_id, market_part in panel.groupby("security_id", sort=False):
            right = field.loc[field["security_id"].eq(security_id)].sort_values(
                "fundamental_available_at"
            )
            left = market_part.sort_values("computation_cutoff")
            if right.empty:
                merged = left.copy()
                merged[field_name] = nan
                merged[f"{field_name}__available_at"] = pd.Series(
                    pd.NaT, index=merged.index, dtype="datetime64[ns, UTC]"
                )
            else:
                merged = pd.merge_asof(
                    left,
                    right.drop(columns="security_id"),
                    left_on="computation_cutoff",
                    right_on="fundamental_available_at",
                    direction="backward",
                    allow_exact_matches=True,
                ).rename(columns={"fundamental_available_at": f"{field_name}__available_at"})
            parts.append(merged)
        panel = pd.concat(parts, ignore_index=True)
    availability_columns = [column for column in panel if column.endswith("__available_at")]
    if availability_columns:
        panel["fundamental_available_at_max"] = panel[availability_columns].max(axis=1)
    panel["available_at"] = panel[["available_at", "fundamental_available_at_max"]].max(axis=1)
    if (panel["available_at"] > panel["computation_cutoff"]).any():
        raise TemporalIntegrityError("point-in-time alignment introduced future evidence")
    return panel.sort_values(["security_id", "date"]).reset_index(drop=True)
