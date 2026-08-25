"""Construct temporally aligned model matrices from authenticated Phase 2 tables."""

from collections.abc import Mapping

import pandas as pd

from institutional_factor_platform.exceptions import DataQualityError, TemporalIntegrityError


def build_research_panel(
    factors: pd.DataFrame,
    portfolios: pd.DataFrame,
    mappings: Mapping[str, str],
) -> pd.DataFrame:
    required_factor = {"security_id", "date", "factor_id", "raw_value", "available_at"}
    required_portfolio = {
        "formation_date",
        "date",
        "factor_id",
        "quantile",
        "value_weighted_return",
        "available_at",
    }
    if required_factor - set(factors) or required_portfolio - set(portfolios):
        raise DataQualityError("Phase 2 publication lacks required Phase 3 fields")
    factor_dates = pd.to_datetime(factors["date"]).dt.date
    factor_available = pd.to_datetime(factors["available_at"], utc=True).dt.date
    portfolio_dates = pd.to_datetime(portfolios["date"]).dt.date
    portfolio_available = pd.to_datetime(portfolios["available_at"], utc=True).dt.date
    if (factor_available > factor_dates).any() or (portfolio_available != portfolio_dates).any():
        raise TemporalIntegrityError("Phase 3 input evidence violates observation availability")
    common = factors.loc[factors["factor_id"].isin(["risk_free_rate", "excess_return"])].copy()
    conflicting = common.groupby(["date", "factor_id"])["raw_value"].nunique(dropna=False)
    if (conflicting > 1).any():
        raise DataQualityError("Market or risk-free values conflict across securities")
    common = common.drop_duplicates(["date", "factor_id"]).pivot(
        index="date", columns="factor_id", values="raw_value"
    )
    if {"risk_free_rate", "excess_return"} - set(common):
        raise DataQualityError("Authenticated market-excess and risk-free factors are required")
    common = common.rename(columns={"excess_return": "market_excess"})

    spread_parts: list[pd.Series] = []
    for alias, factor_id in mappings.items():
        selected = portfolios.loc[portfolios["factor_id"].eq(factor_id)].copy()
        if selected.empty:
            raise DataQualityError(f"Mapped Phase 2 factor is unavailable: {alias}={factor_id}")
        bounds = selected.groupby("date")["quantile"].agg(["min", "max"])
        complete_dates = bounds.index[bounds["min"] != bounds["max"]]
        if complete_dates.empty:
            raise DataQualityError(f"Factor {factor_id} lacks both extreme portfolios")
        # Sparse early formation dates can legitimately contain only one quantile.
        # They are non-estimable for a high-minus-low spread and must be excluded
        # from the complete-case model intersection rather than invalidating later
        # dates that carry both authenticated extremes.
        selected = selected.loc[selected["date"].isin(complete_dates)].copy()
        bounds = bounds.loc[complete_dates]
        low = selected.merge(
            bounds["min"].rename("bound").reset_index(), on="date", validate="many_to_one"
        ).loc[lambda value: value["quantile"].eq(value["bound"])]
        high = selected.merge(
            bounds["max"].rename("bound").reset_index(), on="date", validate="many_to_one"
        ).loc[lambda value: value["quantile"].eq(value["bound"])]
        if low["date"].duplicated().any() or high["date"].duplicated().any():
            raise DataQualityError(f"Factor {factor_id} has duplicate extreme portfolios")
        spread = (
            high.set_index("date")["value_weighted_return"]
            - low.set_index("date")["value_weighted_return"]
        )
        spread.name = alias
        spread_parts.append(spread)
    model_factors = pd.concat(spread_parts, axis=1) if spread_parts else None

    assets = portfolios.loc[
        :,
        [
            "date",
            "factor_id",
            "quantile",
            "value_weighted_return",
            "formation_date",
            "available_at",
        ],
    ].copy()
    assets["asset_id"] = assets["factor_id"].astype(str) + ":Q" + assets["quantile"].astype(str)
    panel = assets.merge(common.reset_index(), on="date", validate="many_to_one")
    if model_factors is not None:
        panel = panel.merge(model_factors.reset_index(), on="date", validate="many_to_one")
    panel["excess_return"] = panel["value_weighted_return"] - panel["risk_free_rate"]
    panel = panel.sort_values(["asset_id", "date"], kind="stable").reset_index(drop=True)
    if panel.empty:
        raise DataQualityError("No exactly aligned Phase 2 observations are available")
    return panel
