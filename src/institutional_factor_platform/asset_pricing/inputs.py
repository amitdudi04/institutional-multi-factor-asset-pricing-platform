"""Construct period-aligned model matrices from factor tables."""

from collections.abc import Mapping

import numpy as np
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

    portfolio_data = portfolios.copy()
    portfolio_data["formation_date"] = pd.to_datetime(portfolio_data["formation_date"])
    portfolio_data["date"] = pd.to_datetime(portfolio_data["date"])
    if (portfolio_data["formation_date"] >= portfolio_data["date"]).any():
        raise TemporalIntegrityError("Portfolio realization dates must follow formation dates")

    # The factor source is daily, while each test-asset return spans a full
    # formation-to-realization interval. Aggregate market and cash returns over
    # that same interval before constructing excess returns or regressors.
    common_ids = ["market_return", "risk_free_rate", "excess_return"]
    common_rows = factors.loc[factors["factor_id"].isin(common_ids)].copy()
    if common_rows.empty:
        raise DataQualityError("Daily market-return and risk-free factors are required")
    conflicting = common_rows.groupby(["date", "factor_id"])["raw_value"].nunique(dropna=False)
    if (conflicting > 1).any():
        raise DataQualityError("Market or risk-free values conflict across securities")
    common = common_rows.drop_duplicates(["date", "factor_id"]).pivot(
        index="date", columns="factor_id", values="raw_value"
    )
    if set(common_ids) - set(common.columns):
        raise DataQualityError(
            "Authenticated daily market-return, excess-return and risk-free factors are required"
        )
    common.index = pd.to_datetime(common.index)
    common = common.sort_index()
    if common[common_ids].isna().any().any():
        raise DataQualityError("Daily market-factor evidence contains missing values")
    if not np.isfinite(common[common_ids].to_numpy(dtype=float)).all():
        raise DataQualityError("Daily market-factor evidence contains non-finite values")
    if (common[["market_return", "risk_free_rate"]] <= -1.0).any().any():
        raise DataQualityError("Daily market and risk-free returns must be greater than -100%")
    daily_excess = common["market_return"] - common["risk_free_rate"]
    if not np.allclose(
        common["excess_return"].to_numpy(dtype=float),
        daily_excess.to_numpy(dtype=float),
        rtol=0.0,
        atol=1e-10,
    ):
        raise DataQualityError(
            "Daily market excess return does not reconcile to market minus risk-free return"
        )

    periods = (
        portfolio_data[["formation_date", "date"]]
        .drop_duplicates()
        .sort_values(["formation_date", "date"])
        .reset_index(drop=True)
    )
    period_rows: list[dict[str, object]] = []
    for formation_date, realization_date in periods.itertuples(index=False, name=None):
        daily = common.loc[
            (common.index > formation_date) & (common.index <= realization_date),
            ["market_return", "risk_free_rate"],
        ]
        if daily.empty:
            raise DataQualityError(
                f"No daily market/risk-free observations for holding period "
                f"{formation_date.date()} to {realization_date.date()}"
            )
        market_period = float(
            np.prod(1.0 + daily["market_return"].to_numpy(dtype=float)) - 1.0
        )
        risk_free_period = float(
            np.prod(1.0 + daily["risk_free_rate"].to_numpy(dtype=float)) - 1.0
        )
        period_rows.append(
            {
                "formation_date": formation_date,
                "date": realization_date,
                "market_excess": market_period - risk_free_period,
                "risk_free_rate": risk_free_period,
            }
        )
    period_factors = pd.DataFrame(period_rows)
    if period_factors.duplicated(["formation_date", "date"]).any():
        raise DataQualityError("Aggregated market-factor holding periods are not unique")

    spread_parts: list[pd.DataFrame] = []
    for alias, factor_id in mappings.items():
        selected = portfolio_data.loc[portfolio_data["factor_id"].eq(factor_id)].copy()
        if selected.empty:
            raise DataQualityError(f"Mapped Phase 2 factor is unavailable: {alias}={factor_id}")
        bounds = selected.groupby(["formation_date", "date"])["quantile"].agg(["min", "max"])
        complete_periods = bounds.loc[bounds["min"] != bounds["max"]].reset_index()
        if complete_periods.empty:
            raise DataQualityError(f"Factor {factor_id} lacks both extreme portfolios")
        # Sparse early formation periods can legitimately contain only one quantile.
        # Exclude those periods from the spread, without conflating periods that share
        # an end date but have different formation dates.
        selected = selected.merge(
            complete_periods[["formation_date", "date", "min", "max"]],
            on=["formation_date", "date"],
            validate="many_to_one",
        )
        low = selected.loc[selected["quantile"].eq(selected["min"])]
        high = selected.loc[selected["quantile"].eq(selected["max"])]
        period_keys = ["formation_date", "date"]
        if low.duplicated(period_keys).any() or high.duplicated(period_keys).any():
            raise DataQualityError(f"Factor {factor_id} has duplicate extreme portfolios")
        spread = high[period_keys + ["value_weighted_return"]].merge(
            low[period_keys + ["value_weighted_return"]],
            on=period_keys,
            suffixes=("_high", "_low"),
            validate="one_to_one",
        )
        spread[alias] = (
            spread["value_weighted_return_high"] - spread["value_weighted_return_low"]
        )
        spread_parts.append(spread[period_keys + [alias]])

    model_factors = spread_parts[0]
    for part in spread_parts[1:]:
        model_factors = model_factors.merge(
            part,
            on=["formation_date", "date"],
            how="outer",
            validate="one_to_one",
        )

    assets = portfolio_data.loc[
        :,
        [
            "date",
            "formation_date",
            "factor_id",
            "quantile",
            "value_weighted_return",
            "available_at",
        ],
    ].copy()
    assets["asset_id"] = assets["factor_id"].astype(str) + ":Q" + assets["quantile"].astype(str)
    panel = assets.merge(
        period_factors,
        on=["formation_date", "date"],
        validate="many_to_one",
    )
    panel = panel.merge(
        model_factors,
        on=["formation_date", "date"],
        validate="many_to_one",
    )
    # Both terms now represent the same formation-to-realization holding period.
    panel["excess_return"] = panel["value_weighted_return"] - panel["risk_free_rate"]
    panel = panel.sort_values(["asset_id", "date"], kind="stable").reset_index(drop=True)
    if panel.empty:
        raise DataQualityError("No exactly aligned Phase 2 observations are available")
    return panel
