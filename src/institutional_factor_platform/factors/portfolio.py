"""Point-in-time factor quantile portfolio diagnostics for Phase 2 research."""

from math import ceil

import pandas as pd

from institutional_factor_platform.exceptions import DataQualityError, TemporalIntegrityError
from institutional_factor_platform.factors.definitions import FACTOR_VERSION


def compute_factor_portfolios(
    factors: pd.DataFrame,
    characteristics: pd.DataFrame,
    market: pd.DataFrame,
    quantiles: int = 3,
) -> pd.DataFrame:
    """Form value-weighted quantiles at t and realize returns only at t+1."""
    future = market.sort_values(["security_id", "date"])[
        ["security_id", "date", "return", "benchmark_return", "available_at"]
    ].copy()
    grouped = future.groupby("security_id", sort=False)
    future["realization_date"] = grouped["date"].shift(-1)
    future["realized_return"] = grouped["return"].shift(-1)
    future["realized_benchmark"] = grouped["benchmark_return"].shift(-1)
    future["realized_available_at"] = grouped["available_at"].shift(-1)
    future = future.dropna(subset=["realization_date", "realized_return", "realized_benchmark"])

    formation = factors[["security_id", "date", "factor_id", "raw_value"]].merge(
        characteristics[["security_id", "date", "market_cap"]],
        on=["security_id", "date"],
        validate="many_to_one",
    )
    formation = formation.merge(
        future[
            [
                "security_id",
                "date",
                "realization_date",
                "realized_return",
                "realized_benchmark",
                "realized_available_at",
            ]
        ],
        on=["security_id", "date"],
        validate="many_to_one",
    )
    formation = formation.dropna(subset=["raw_value", "market_cap"])
    formation = formation.loc[formation["market_cap"] > 0].copy()
    formation["percentile"] = formation.groupby(["date", "factor_id"])["raw_value"].rank(
        method="first", pct=True
    )
    formation["quantile"] = formation["percentile"].map(
        lambda value: min(quantiles, max(1, ceil(value * quantiles)))
    )

    def summarize(group: pd.DataFrame) -> pd.Series:
        weights = group["market_cap"] / group["market_cap"].sum()
        portfolio_return = float((group["realized_return"] * weights).sum())
        benchmark_return = float((group["realized_benchmark"] * weights).sum())
        return pd.Series(
            {
                "security_count": len(group),
                "value_weighted_return": portfolio_return,
                "benchmark_return": benchmark_return,
                "active_return": portfolio_return - benchmark_return,
                "available_at": group["realized_available_at"].max(),
            }
        )

    result = (
        formation.groupby(
            ["date", "realization_date", "factor_id", "quantile"], observed=True, sort=True
        )
        .apply(summarize, include_groups=False)
        .reset_index()
        .rename(columns={"date": "formation_date", "realization_date": "date"})
    )
    result["security_count"] = result["security_count"].astype("int32")
    result["quantile"] = result["quantile"].astype("int8")
    result["factor_version"] = FACTOR_VERSION
    return result


def validate_factor_portfolios(frame: pd.DataFrame) -> None:
    if frame.empty or frame.duplicated(["formation_date", "date", "factor_id", "quantile"]).any():
        raise DataQualityError("factor portfolio output is empty or has duplicate group keys")
    if (frame["date"] <= frame["formation_date"]).any():
        raise TemporalIntegrityError("factor portfolio returns must follow their formation date")
    if (pd.to_datetime(frame["available_at"], utc=True).dt.date < frame["date"]).any():
        raise TemporalIntegrityError("factor portfolio returns precede their available evidence")
    if (frame["security_count"] <= 0).any() or not frame["quantile"].between(1, 3).all():
        raise DataQualityError("factor portfolio membership is invalid")
    for column in ("value_weighted_return", "benchmark_return", "active_return"):
        if not frame[column].map(lambda value: float("-inf") < value < float("inf")).all():
            raise DataQualityError(f"factor portfolio {column} contains non-finite values")
    if (frame[["value_weighted_return", "benchmark_return"]] <= -1.0).any().any():
        raise DataQualityError("factor portfolio contains an impossible simple return")
