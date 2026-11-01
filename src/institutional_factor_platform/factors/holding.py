"""Complete monthly, delayed-close holdings; no synthetic terminal valuations.

An absent interior quote is admissible only when consecutive observed returns
reconcile to genuine quotes. This establishes terminal buy-and-hold PnL, not a
daily mark or intraperiod risk path. Missing endpoints reject the whole quantile.
"""

from itertools import pairwise

import numpy as np
import pandas as pd

from institutional_factor_platform.exceptions import DataQualityError


def validate_session_series(market: pd.DataFrame, sessions: pd.DatetimeIndex) -> pd.DataFrame:
    """Authenticate the common market/cash calendar before interval compounding."""
    frame = market.copy()
    frame["date"] = pd.to_datetime(frame["date"])
    values = ["market_return", "risk_free_rate"]
    if frame.duplicated(["security_id", "date"]).any():
        raise DataQualityError("Duplicate security session")
    if not np.isfinite(frame[values].to_numpy()).all() or (frame[values] <= -1).any().any():
        raise DataQualityError("Invalid market/cash return")
    grouped = frame.groupby("date")[values]
    if ((grouped.max() - grouped.min()) > 1e-12).any().any():
        raise DataQualityError("Conflicting market/cash observations")
    daily = grouped.first().sort_index()
    if not daily.index.equals(sessions):
        raise DataQualityError("Market/cash observations differ from exchange sessions")
    return daily


def monthly_cycles(sessions: pd.DatetimeIndex) -> list[tuple[pd.Timestamp, ...]]:
    """Signal at genuine month end, execute next close, exit next execution.

    Caller supplies a complete exchange calendar extending beyond observed data;
    cycles with unobserved execution/exit must subsequently be rejected.
    """
    ends = pd.Series(sessions, index=sessions).groupby(sessions.to_period("M")).max()
    positions = sessions.get_indexer(ends)
    executions = {
        s: sessions[p + 1] for s, p in zip(ends, positions, strict=True) if p + 1 < len(sessions)
    }
    signals = list(executions)
    return [(s, executions[s], executions[t]) for s, t in pairwise(signals)]


def endpoint_chain(
    quotes: pd.DataFrame,
    start: pd.Timestamp,
    end: pd.Timestamp,
    sessions: pd.DatetimeIndex,
) -> tuple[float | None, str, int]:
    """Verify every quote link and exact endpoints. Never create a quote or payout."""
    dates = pd.to_datetime(quotes["date"])
    path = quotes.loc[dates.between(start, end)].copy()
    path["date"] = pd.to_datetime(path["date"])
    path = path.sort_values("date")
    if path["date"].duplicated().any():
        raise DataQualityError("Duplicate constituent quote")
    if not path["date"].isin(sessions).all():
        raise DataQualityError("Constituent quote outside exchange calendar")
    if path.empty or path["date"].iloc[0] != start or path["date"].iloc[-1] != end:
        return None, "MISSING_ENDPOINT_NO_AUTHENTIC_TERMINAL", len(path)
    prices = path["price"].to_numpy(dtype=float)
    returns = path["return"].to_numpy(dtype=float)[1:]
    if not np.isfinite(prices).all() or (prices <= 0).any():
        return None, "INVALID_QUOTE", len(path)
    links = prices[1:] / prices[:-1] - 1
    if (
        not np.isfinite(returns).all()
        or (returns <= -1).any()
        or not np.allclose(links, returns, atol=1e-10, rtol=1e-10)
    ):
        return None, "UNRECONCILED_QUOTE_RETURN_CHAIN", len(path)
    endpoint = float(prices[-1] / prices[0] - 1)
    if not np.isclose(np.prod(1 + returns) - 1, endpoint, atol=1e-10, rtol=1e-10):
        return None, "UNRECONCILED_ENDPOINT", len(path)
    return endpoint, "COMPLETE_VALID", len(path)


def form_quantiles(scores: pd.DataFrame) -> pd.DataFrame:
    """Fix eligible membership and cap weights before inspecting future quotes."""
    if scores.duplicated(["factor_id", "security_id"]).any():
        raise DataQualityError("Duplicate formation score")
    frame = scores.loc[
        np.isfinite(scores["score_value"])
        & np.isfinite(scores["market_cap"])
        & scores["market_cap"].gt(0)
        & scores["eligible"].eq(True)
    ].copy()
    # Preserve frozen input order for historical rank(method='first') tie policy.
    sizes = frame.groupby("factor_id")["security_id"].transform("size")
    frame = frame.loc[sizes >= 3].copy()
    ranks = frame.groupby("factor_id")["score_value"].rank(method="first", pct=True)
    frame["quantile"] = np.ceil(ranks * 3).clip(1, 3).astype("int8")
    frame["weight"] = frame["market_cap"] / frame.groupby(["factor_id", "quantile"])[
        "market_cap"
    ].transform("sum")
    return frame


def matched_sample(frame: pd.DataFrame, regressors: tuple[str, ...]) -> pd.DataFrame:
    """Identical per-asset complete cases for all requested model families."""
    columns = ["excess_return", *regressors]
    if frame.duplicated(["asset_id", "date"]).any():
        raise DataQualityError("Duplicate asset interval")
    return frame.loc[np.isfinite(frame[columns].to_numpy(dtype=float)).all(axis=1)].copy()
