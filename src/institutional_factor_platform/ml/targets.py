"""Explicit point-in-time targets built from security returns."""

import numpy as np
import pandas as pd
from numpy.typing import NDArray

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
    annualization_periods: int = 252,
    minimum_acceptable_return: float = 0.0,
    risk_quantile_alpha: float = 0.05,
    source_publication_id: str | None = None,
    source_artifact_checksum: str | None = None,
    source_unit: str = "decimal_return",
) -> tuple[pd.DataFrame, TargetSpecification]:
    """Build one future target per security/decision date without cross-security mixing."""
    required = {"security_id", "date", "return", "available_at"}
    if set(returns.columns) < required or returns.empty or horizon < 1:
        raise DataQualityError("Return source does not satisfy the target contract")
    if annualization_periods < 1 or not 0 < risk_quantile_alpha < 1:
        raise DataQualityError("Risk target conventions are invalid")
    if source_unit != "decimal_return":
        raise DataQualityError("Target source unit must be decimal_return")
    benchmark_required = kind in {"future_excess_return", "outperformance"}
    if benchmark_required and (benchmark_id is None or "benchmark_return" not in returns):
        raise DataQualityError("Authenticated benchmark and identity are required")

    frame = returns.copy().sort_values(["security_id", "date"], kind="stable")
    frame["date"] = pd.to_datetime(frame["date"], utc=True)
    frame["available_at"] = pd.to_datetime(frame["available_at"], utc=True)
    value_columns = ["security_id", "date", "return", "available_at"]
    if benchmark_required:
        value_columns.append("benchmark_return")
    if frame[value_columns].isna().any().any():
        raise DataQualityError("Target source contains missing required identity or values")
    if frame.duplicated(["security_id", "date"]).any():
        raise DataQualityError("Target source contains duplicate security/date keys")
    if (frame["available_at"] < frame["date"]).any():
        raise TemporalIntegrityError("Return availability precedes its observation identity")

    rows: list[dict[str, object]] = []
    for security_id, security in frame.groupby("security_id", sort=True):
        security = security.reset_index(drop=True)
        for position in range(len(security) - horizon):
            decision = security.iloc[position]
            future = security.iloc[position + 1 : position + horizon + 1]
            target_start = future.iloc[0]["date"]
            target_end = future.iloc[-1]["date"]
            if not decision["date"] < target_start <= target_end:
                raise TemporalIntegrityError("Target window does not follow the decision date")
            values = future["return"].to_numpy(dtype=float)
            target = _target_value(
                values,
                kind,
                annualization_periods=annualization_periods,
                minimum_acceptable_return=minimum_acceptable_return,
                risk_quantile_alpha=risk_quantile_alpha,
            )
            if benchmark_required:
                benchmark = _compound(future["benchmark_return"].to_numpy(dtype=float))
                security_return = _compound(values)
                relative = security_return - benchmark
                target = float(relative > threshold) if kind == "outperformance" else relative
            rows.append(
                {
                    "security_id": security_id,
                    "formation_date": decision["date"],
                    "target_start": target_start,
                    "target_end": target_end,
                    "target_available_at": future["available_at"].max(),
                    "target": target,
                }
            )

    result = pd.DataFrame(rows)
    if result.empty:
        raise DataQualityError("Target horizon leaves no complete future windows")
    if kind in {"percentile_rank", "ordinal_rank", "quantile_bucket"}:
        result["target"] = _cross_sectional_rank(result, kind, quantiles)

    unit = _unit(kind)
    transformation = {
        "future_return": "forward compounded security simple return",
        "future_excess_return": "forward compounded security return minus benchmark return",
        "outperformance": "security return exceeds benchmark return plus threshold",
        "future_volatility": "forward sample volatility annualized",
        "future_downside_volatility": "forward downside deviation annualized",
        "future_drawdown": "forward cumulative-wealth maximum drawdown",
        "future_risk_quantile": "forward historical VaR positive-loss convention",
    }.get(kind, "formation-date cross-sectional rank of forward compounded return")
    specification = TargetSpecification(
        schema_version="1.0.0",
        target_type=kind,
        horizon=horizon,
        benchmark_id=benchmark_id,
        unit=unit,
        transformation=transformation,
        quantiles=quantiles
        if kind in {"percentile_rank", "ordinal_rank", "quantile_bucket"}
        else None,
        source_publication_id=source_publication_id,
        source_artifact_checksum=source_artifact_checksum,
        source_unit=source_unit,
        annualization_periods=(
            annualization_periods
            if kind in {"future_volatility", "future_downside_volatility"}
            else None
        ),
        minimum_acceptable_return=(
            minimum_acceptable_return if kind == "future_downside_volatility" else None
        ),
        risk_quantile_alpha=risk_quantile_alpha if kind == "future_risk_quantile" else None,
    )
    return result.sort_values(["formation_date", "security_id"]).reset_index(
        drop=True
    ), specification


def _target_value(
    values: NDArray[np.float64],
    kind: str,
    *,
    annualization_periods: int,
    minimum_acceptable_return: float,
    risk_quantile_alpha: float,
) -> float:
    if not np.isfinite(values).all() or (values <= -1).any():
        raise DataQualityError("Future target window contains invalid simple returns")
    if kind in {
        "future_return",
        "future_excess_return",
        "outperformance",
        "percentile_rank",
        "ordinal_rank",
        "quantile_bucket",
    }:
        return _compound(values)
    if kind == "future_volatility":
        if len(values) < 2:
            raise DataQualityError("Future volatility requires at least two observations")
        return float(np.std(values, ddof=1) * np.sqrt(annualization_periods))
    if kind == "future_downside_volatility":
        downside = np.minimum(values - minimum_acceptable_return, 0.0)
        return float(np.sqrt(np.mean(downside**2)) * np.sqrt(annualization_periods))
    if kind == "future_drawdown":
        wealth = np.cumprod(1.0 + values)
        peaks = np.maximum.accumulate(np.concatenate(([1.0], wealth)))[:-1]
        return float(np.min(wealth / peaks - 1.0))
    if kind == "future_risk_quantile":
        return max(0.0, float(-np.quantile(values, risk_quantile_alpha)))
    raise DataQualityError(f"Unsupported target kind: {kind}")


def _compound(values: NDArray[np.float64]) -> float:
    return float(np.prod(1.0 + values) - 1.0)


def _cross_sectional_rank(result: pd.DataFrame, kind: str, quantiles: int) -> pd.Series:
    grouped = result.groupby("formation_date", sort=True)["target"]
    if kind == "percentile_rank":
        return grouped.rank(method="first", pct=True)
    if kind == "ordinal_rank":
        return grouped.rank(method="first")
    return grouped.transform(
        lambda values: pd.qcut(
            values.rank(method="first"),
            min(quantiles, len(values)),
            labels=False,
            duplicates="drop",
        )
    )


def _unit(kind: str) -> str:
    if kind in {"percentile_rank", "ordinal_rank", "quantile_bucket"}:
        return "rank"
    if kind == "outperformance":
        return "binary"
    if kind in {"future_volatility", "future_downside_volatility"}:
        return "annualized_volatility"
    if kind == "future_risk_quantile":
        return "positive_loss"
    return "decimal_return"
