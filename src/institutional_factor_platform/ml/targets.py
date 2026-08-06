"""Explicit point-in-time target construction."""

import numpy as np
import pandas as pd

from institutional_factor_platform.exceptions import DataQualityError, TemporalIntegrityError
from institutional_factor_platform.ml.contracts import TargetSpecification


def build_targets(
    returns: pd.DataFrame,
    *,
    kind: str,
    horizon: int,
    benchmark_id: str | None = None,
    threshold: float = 0.0,
    quantiles: int = 5,
) -> tuple[pd.DataFrame, TargetSpecification]:
    required = {"security_id", "date", "return", "available_at"}
    if set(returns.columns) < required or returns.empty or horizon < 1:
        raise DataQualityError("Return source does not satisfy the target contract")
    frame = returns.copy().sort_values(["security_id", "date"])
    frame["date"] = pd.to_datetime(frame["date"], utc=True)
    frame["available_at"] = pd.to_datetime(frame["available_at"], utc=True)
    if frame[["security_id", "date", "return", "available_at"]].isna().any().any():
        raise DataQualityError("Target source contains missing required identity or values")
    if frame.duplicated(["security_id", "date"]).any():
        raise DataQualityError("Target source contains duplicate security/date keys")
    if (frame["available_at"] < frame["date"]).any():
        raise TemporalIntegrityError("Return availability precedes its observation identity")
    grouped = frame.groupby("security_id", sort=False)
    forward = grouped["return"].transform(
        lambda x: (1 + x).rolling(horizon).apply(np.prod, raw=True).shift(-horizon) - 1
    )
    start = grouped["date"].shift(-1)
    end = grouped["date"].shift(-horizon)
    available = grouped["available_at"].shift(-horizon)
    target = forward.copy()
    unit = "decimal_return"
    if kind in {"future_excess_return", "outperformance"}:
        if benchmark_id is None or "benchmark_return" not in frame:
            raise DataQualityError("Authenticated benchmark and identity are required")
        benchmark = (
            frame["benchmark_return"]
            .rolling(horizon)
            .apply(lambda x: np.prod(1 + x) - 1, raw=True)
            .shift(-horizon)
        )
        target = forward - benchmark
    result = pd.DataFrame(
        {
            "security_id": frame["security_id"],
            "formation_date": frame["date"],
            "target_start": start,
            "target_end": end,
            "target_available_at": available,
            "target": target,
        }
    )
    result = result.dropna(subset=["target", "target_start", "target_end", "target_available_at"])
    if kind in {"percentile_rank", "ordinal_rank", "quantile_bucket", "future_risk_quantile"}:
        ranks = result.groupby("formation_date")["target"].rank(
            method="first", pct=kind == "percentile_rank"
        )
        if kind in {"quantile_bucket", "future_risk_quantile"}:
            ranks = result.groupby("formation_date")["target"].transform(
                lambda x: pd.qcut(
                    x.rank(method="first"), min(quantiles, len(x)), labels=False, duplicates="drop"
                )
            )
        result["target"] = ranks
        unit = "rank"
    elif kind == "outperformance":
        result["target"] = (result["target"] > threshold).astype(int)
        unit = "binary"
    elif kind in {"future_volatility", "future_downside_volatility", "future_drawdown"}:

        def risk(x: pd.Series) -> pd.Series:
            future = x.shift(-1)[::-1].rolling(horizon).std(ddof=1)[::-1]
            return future

        result["target"] = grouped["return"].transform(risk).loc[result.index]
        if kind == "future_drawdown":
            result["target"] = (result["target"] > threshold).astype(int)
            unit = "binary"
        else:
            unit = "volatility"
    spec = TargetSpecification(
        schema_version="1.0.0",
        target_type=kind,
        horizon=horizon,
        benchmark_id=benchmark_id,
        unit=unit,
        transformation="future compounded simple return",
        quantiles=quantiles if "rank" in kind or "quantile" in kind else None,
    )
    return result.sort_values(["formation_date", "security_id"]).reset_index(drop=True), spec
