"""Deterministic point-in-time feature assembly from validated tables."""

from datetime import UTC, datetime, time

import pandas as pd

from institutional_factor_platform.exceptions import DataQualityError, TemporalIntegrityError
from institutional_factor_platform.ml.contracts import FeatureDefinition, FeatureSchema

META_COLUMNS = ("security_id", "formation_date", "decision_time", "feature_available_at")
PROHIBITED_NAMES = {"target", "future_return", "future_benchmark_return", "target_rank"}


def assemble_factor_features(
    authenticated_factors: pd.DataFrame,
    factor_ids: tuple[str, ...],
    value_column: str,
    *,
    source_publication_id: str,
    minimum_coverage: float,
) -> tuple[pd.DataFrame, FeatureSchema, dict[str, object]]:
    required = {"security_id", "date", "available_at", "factor_id", value_column}
    if set(authenticated_factors.columns) < required:
        raise DataQualityError("Authenticated factor table lacks required feature columns")
    if not factor_ids or len(factor_ids) != len(set(factor_ids)):
        raise DataQualityError("Feature selection must be explicit and unique")
    if set(factor_ids) & PROHIBITED_NAMES or any("future" in name for name in factor_ids):
        raise TemporalIntegrityError("Target-derived or future feature requested")
    frame = authenticated_factors.loc[
        authenticated_factors["factor_id"].isin(factor_ids), list(required)
    ].copy()
    if frame.duplicated(["security_id", "date", "factor_id"]).any():
        raise DataQualityError("Feature source contains duplicate security/date/factor keys")
    frame["formation_date"] = pd.to_datetime(frame["date"], utc=True)
    frame["feature_available_at"] = pd.to_datetime(frame["available_at"], utc=True)
    frame["decision_time"] = frame["formation_date"].map(
        lambda value: datetime.combine(value.date(), time.max, tzinfo=UTC)
    )
    if (frame["feature_available_at"] > frame["decision_time"]).any():
        raise TemporalIntegrityError("Feature evidence is unavailable at decision time")
    wide = frame.pivot(
        index=["security_id", "formation_date", "decision_time"],
        columns="factor_id",
        values=value_column,
    )
    ordered = tuple(sorted(factor_ids))
    wide = wide.reindex(columns=ordered).reset_index()
    availability = (
        frame.groupby(["security_id", "formation_date"], sort=True)["feature_available_at"]
        .max()
        .reset_index()
    )
    wide = wide.merge(availability, on=["security_id", "formation_date"], validate="one_to_one")
    coverage = wide[list(ordered)].notna().mean(axis=1)
    excluded = int((coverage < minimum_coverage).sum())
    wide["feature_coverage"] = coverage
    wide = (
        wide.loc[coverage >= minimum_coverage]
        .sort_values(["formation_date", "security_id"])
        .reset_index(drop=True)
    )
    definitions = tuple(
        FeatureDefinition(
            name=name,
            family=name.split("_", 1)[0],
            definition=f"Authenticated Phase 2 {value_column}",
            rationale="Owner-selected classical characteristic",
            source=source_publication_id,
            unit="score" if value_column != "raw_value" else "source_unit",
            direction=0,
            availability_policy="available_at <= decision_time",
            transformation_chain=(value_column,),
            missingness_policy="configured",
            fitted_state_scope="none",
            version="1.0.0",
        )
        for name in ordered
    )
    schema = FeatureSchema(
        schema_version="1.0.0", feature_set_version="1.0.0", features=definitions
    )
    report = {
        "requested": ordered,
        "accepted": ordered,
        "excluded_rows": excluded,
        "rows": len(wide),
    }
    return wide, schema, report


def add_interactions(
    frame: pd.DataFrame, interactions: tuple[tuple[str, str], ...]
) -> pd.DataFrame:
    result = frame.copy()
    for left, right in interactions:
        if (
            left not in result
            or right not in result
            or left in PROHIBITED_NAMES
            or right in PROHIBITED_NAMES
        ):
            raise DataQualityError("Interaction references an unavailable or prohibited feature")
        name = f"{left}__x__{right}"
        if name in result:
            raise DataQualityError("Interaction feature identity collides")
        result[name] = result[left] * result[right]
    return result


def monthly_decision_features(frame: pd.DataFrame) -> pd.DataFrame:
    """Select the last authenticated decision observation per security/month."""
    required = {"security_id", "formation_date", "decision_time", "feature_available_at"}
    if frame.empty or required - set(frame):
        raise DataQualityError("Monthly feature sampling requires decision-time identity")
    result = frame.copy()
    result["formation_date"] = pd.to_datetime(result["formation_date"], utc=True)
    result["_decision_month"] = result["formation_date"].dt.tz_localize(None).dt.to_period("M")
    result = (
        result.sort_values(["security_id", "formation_date"], kind="stable")
        .groupby(["security_id", "_decision_month"], sort=True, as_index=False)
        .tail(1)
        .drop(columns="_decision_month")
        .sort_values(["formation_date", "security_id"], kind="stable")
        .reset_index(drop=True)
    )
    if (
        result.assign(month=result["formation_date"].dt.tz_localize(None).dt.to_period("M"))
        .duplicated(["security_id", "month"])
        .any()
    ):
        raise DataQualityError("Monthly feature sampling produced duplicate decisions")
    return result
