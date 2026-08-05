"""Point-in-time factor quantile portfolio diagnostics for Phase 2 research."""

from math import ceil

import pandas as pd

from institutional_factor_platform.exceptions import DataQualityError, TemporalIntegrityError
from institutional_factor_platform.factors.definitions import FACTOR_VERSION

NON_PORTFOLIO_FACTORS = {
    "market_return",
    "excess_return",
    "risk_free_rate",
    "size_small",
    "size_mid",
    "size_large",
}


def compute_factor_portfolios(
    factors: pd.DataFrame,
    characteristics: pd.DataFrame,
    market: pd.DataFrame,
    quantiles: int = 3,
    rebalancing: str = "monthly",
) -> pd.DataFrame:
    """Form month-end value-weighted quantiles and realize the next holding period."""
    if rebalancing != "monthly":
        raise DataQualityError("Phase 2 factor portfolios require approved monthly rebalancing")
    formation = factors[["security_id", "date", "factor_id", "score_value"]].merge(
        characteristics[["security_id", "date", "market_cap"]],
        on=["security_id", "date"],
        validate="many_to_one",
    )
    formation = formation.loc[~formation["factor_id"].isin(NON_PORTFOLIO_FACTORS)]
    formation["month"] = pd.to_datetime(formation["date"]).dt.to_period("M")
    formation = formation.loc[
        formation["date"].eq(formation.groupby("month")["date"].transform("max"))
    ].drop(columns="month")

    formation_dates = sorted(formation["date"].unique())
    realized_parts: list[pd.DataFrame] = []
    market_end = market["date"].max()
    for index, formation_date in enumerate(formation_dates):
        period_end = formation_dates[index + 1] if index + 1 < len(formation_dates) else market_end
        holding = market.loc[market["date"].gt(formation_date) & market["date"].le(period_end)]
        if holding.empty:
            continue
        realized = (
            holding.groupby("security_id")
            .agg(
                realization_date=("date", "max"),
                realized_return=("return", lambda values: (1.0 + values).prod() - 1.0),
                realized_benchmark=(
                    "benchmark_return",
                    lambda values: (1.0 + values).prod() - 1.0,
                ),
                realized_available_at=("available_at", "max"),
            )
            .reset_index()
        )
        realized["date"] = formation_date
        realized_parts.append(realized)
    if not realized_parts:
        raise DataQualityError("Insufficient post-formation history for factor portfolios")
    future = pd.concat(realized_parts, ignore_index=True)
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
    formation = formation.dropna(subset=["score_value", "market_cap"])
    formation = formation.loc[formation["market_cap"] > 0].copy()
    formation["percentile"] = formation.groupby(["date", "factor_id"])["score_value"].rank(
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


def validate_factor_portfolios(frame: pd.DataFrame, quantiles: int = 3) -> None:
    if frame.empty or frame.duplicated(["formation_date", "date", "factor_id", "quantile"]).any():
        raise DataQualityError("factor portfolio output is empty or has duplicate group keys")
    if (frame["date"] <= frame["formation_date"]).any():
        raise TemporalIntegrityError("factor portfolio returns must follow their formation date")
    if (pd.to_datetime(frame["available_at"], utc=True).dt.date < frame["date"]).any():
        raise TemporalIntegrityError("factor portfolio returns precede their available evidence")
    if (frame["security_count"] <= 0).any() or not frame["quantile"].between(1, quantiles).all():
        raise DataQualityError("factor portfolio membership is invalid")
    for column in ("value_weighted_return", "benchmark_return", "active_return"):
        if not frame[column].map(lambda value: float("-inf") < value < float("inf")).all():
            raise DataQualityError(f"factor portfolio {column} contains non-finite values")
    if (frame[["value_weighted_return", "benchmark_return"]] <= -1.0).any().any():
        raise DataQualityError("factor portfolio contains an impossible simple return")
