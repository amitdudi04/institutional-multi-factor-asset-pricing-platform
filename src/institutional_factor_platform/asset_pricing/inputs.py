"""Construct frequency-matched, temporally aligned asset-pricing model matrices."""

from collections.abc import Mapping

import numpy as np
import pandas as pd

from institutional_factor_platform.exceptions import DataQualityError, TemporalIntegrityError


def _normalized_dates(frame: pd.DataFrame, columns: tuple[str, ...]) -> pd.DataFrame:
    result = frame.copy()
    for column in columns:
        result[column] = pd.to_datetime(result[column], errors="raise").dt.normalize()
    return result


def _holding_period_market_factors(factors: pd.DataFrame, periods: pd.DataFrame) -> pd.DataFrame:
    """Compound daily market and cash returns over each exact portfolio holding interval."""
    common_ids = ["market_return", "risk_free_rate", "excess_return"]
    common = factors.loc[factors["factor_id"].isin(common_ids)].copy()
    conflicts = common.groupby(["date", "factor_id"])["raw_value"].nunique(dropna=False)
    if (conflicts > 1).any():
        raise DataQualityError("Market or risk-free values conflict across securities")
    daily = common.drop_duplicates(["date", "factor_id"]).pivot(
        index="date", columns="factor_id", values="raw_value"
    )
    required = {"market_return", "risk_free_rate"}
    if required - set(daily.columns):
        raise DataQualityError(
            "Authenticated daily market-return and risk-free factors are required"
        )

    daily = daily.sort_index()
    market = pd.to_numeric(daily["market_return"], errors="coerce")
    risk_free = pd.to_numeric(daily["risk_free_rate"], errors="coerce")
    if market.isna().any() or risk_free.isna().any():
        raise DataQualityError("Daily market or risk-free series contains missing values")
    if not np.isfinite(market.to_numpy()).all() or not np.isfinite(risk_free.to_numpy()).all():
        raise DataQualityError("Daily market or risk-free series contains non-finite values")
    if (market <= -1.0).any() or (risk_free <= -1.0).any():
        raise DataQualityError(
            "Daily market or risk-free series contains an impossible simple return"
        )

    if "excess_return" in daily.columns:
        observed_excess = pd.to_numeric(daily["excess_return"], errors="coerce")
        expected_excess = market - risk_free
        available = observed_excess.notna()
        if available.any() and not np.allclose(
            observed_excess.loc[available].to_numpy(),
            expected_excess.loc[available].to_numpy(),
            rtol=0.0,
            atol=1e-8,
        ):
            raise DataQualityError(
                "Daily market-excess values do not reconcile to market less cash"
            )

    rows: list[dict[str, object]] = []
    intervals = (
        periods[["formation_date", "date"]]
        .drop_duplicates()
        .sort_values(["formation_date", "date"])
    )
    if (intervals["date"] <= intervals["formation_date"]).any():
        raise TemporalIntegrityError("Portfolio realization must follow its formation date")

    for interval in intervals.itertuples(index=False):
        start = pd.Timestamp(interval.formation_date)
        end = pd.Timestamp(interval.date)
        window = daily.loc[(daily.index > start) & (daily.index <= end)]
        if window.empty:
            raise DataQualityError(
                f"No authenticated daily market observations for holding interval "
                f"{start.date()} to {end.date()}"
            )
        market_total = float((1.0 + window["market_return"].astype(float)).prod() - 1.0)
        cash_total = float((1.0 + window["risk_free_rate"].astype(float)).prod() - 1.0)
        rows.append(
            {
                "formation_date": start,
                "date": end,
                "market_excess": market_total - cash_total,
                "risk_free_rate": cash_total,
            }
        )
    return pd.DataFrame(rows)


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

    factor_frame = _normalized_dates(factors, ("date",))
    portfolio_frame = _normalized_dates(portfolios, ("formation_date", "date"))
    period_factors = _holding_period_market_factors(factor_frame, portfolio_frame)

    keys = ["formation_date", "date"]
    spread_parts: list[pd.Series] = []
    for alias, factor_id in mappings.items():
        selected = portfolio_frame.loc[portfolio_frame["factor_id"].eq(factor_id)].copy()
        if selected.empty:
            raise DataQualityError(f"Mapped Phase 2 factor is unavailable: {alias}={factor_id}")
        bounds = (
            selected.groupby(keys)["quantile"]
            .agg(min_quantile="min", max_quantile="max")
            .reset_index()
        )
        complete = bounds.loc[bounds["min_quantile"] != bounds["max_quantile"]]
        if complete.empty:
            raise DataQualityError(f"Factor {factor_id} lacks both extreme portfolios")
        # Early formation intervals may contain only one quantile. Exclude those intervals.
        selected = selected.merge(complete[keys], on=keys, validate="many_to_one")
        low = selected.merge(
            complete[[*keys, "min_quantile"]], on=keys, validate="many_to_one"
        ).loc[lambda value: value["quantile"].eq(value["min_quantile"])]
        high = selected.merge(
            complete[[*keys, "max_quantile"]], on=keys, validate="many_to_one"
        ).loc[lambda value: value["quantile"].eq(value["max_quantile"])]
        if low.duplicated(keys).any() or high.duplicated(keys).any():
            raise DataQualityError(f"Factor {factor_id} has duplicate extreme portfolios")
        spread = (
            high.set_index(keys)["value_weighted_return"]
            - low.set_index(keys)["value_weighted_return"]
        )
        spread.name = alias
        spread_parts.append(spread)

    model_factors = pd.concat(spread_parts, axis=1) if spread_parts else None
    assets = portfolio_frame.loc[
        :,
        [
            "formation_date",
            "date",
            "factor_id",
            "quantile",
            "value_weighted_return",
            "available_at",
        ],
    ].copy()
    assets["asset_id"] = assets["factor_id"].astype(str) + ":Q" + assets["quantile"].astype(str)
    panel = assets.merge(period_factors, on=keys, validate="many_to_one")
    if model_factors is not None:
        model_factors.index.names = keys
        panel = panel.merge(model_factors.reset_index(), on=keys, validate="many_to_one")
    panel["excess_return"] = panel["value_weighted_return"] - panel["risk_free_rate"]
    panel = panel.sort_values(["asset_id", "date"], kind="stable").reset_index(drop=True)
    if panel.empty:
        raise DataQualityError("No exactly aligned Phase 2 observations are available")
    return panel
