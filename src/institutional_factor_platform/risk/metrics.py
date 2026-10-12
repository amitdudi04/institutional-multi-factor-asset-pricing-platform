"""Explicit-frequency portfolio and tail-risk metrics."""

import numpy as np
import pandas as pd
from scipy.stats import norm

from institutional_factor_platform.exceptions import DataQualityError


def _values(returns: pd.Series, minimum: int = 2) -> np.ndarray:
    values = pd.to_numeric(returns, errors="coerce").dropna().to_numpy(dtype=float)
    if len(values) < minimum or not np.isfinite(values).all() or (values <= -1).any():
        raise DataQualityError(
            "Risk metric requires valid simple returns and sufficient observations"
        )
    return values


def volatility(returns: pd.Series, annualization: int = 12) -> float:
    return float(np.std(_values(returns), ddof=1) * np.sqrt(annualization))


def rolling_volatility(returns: pd.Series, window: int, annualization: int = 12) -> pd.Series:
    if window < 2:
        raise DataQualityError("Rolling volatility window must be at least two")
    return returns.rolling(window).std(ddof=1) * np.sqrt(annualization)


def beta_alpha(
    returns: pd.Series,
    benchmark: pd.Series,
    annualization: int = 12,
    risk_free: pd.Series | float = 0.0,
) -> tuple[float, float]:
    aligned = pd.concat([returns, benchmark], axis=1).dropna()
    if len(aligned) < 3:
        raise DataQualityError("Beta requires at least three aligned return observations")
    if np.isscalar(risk_free):
        rf = np.full(len(aligned), float(risk_free), dtype=float)
    else:
        rf_series = pd.to_numeric(pd.Series(risk_free), errors="coerce").reindex(aligned.index)
        if rf_series.isna().any():
            raise DataQualityError("Risk-free returns must align with portfolio and benchmark dates")
        rf = rf_series.to_numpy(dtype=float)
    if not np.isfinite(rf).all() or (rf <= -1.0).any():
        raise DataQualityError("Risk-free returns must be finite simple returns greater than -100%")

    portfolio_excess = aligned.iloc[:, 0].to_numpy(dtype=float) - rf
    benchmark_excess = aligned.iloc[:, 1].to_numpy(dtype=float) - rf
    benchmark_variance = float(np.var(benchmark_excess, ddof=1))
    if benchmark_variance <= 0:
        raise DataQualityError("Beta requires variable benchmark excess returns")
    beta = float(np.cov(portfolio_excess, benchmark_excess, ddof=1)[0, 1] / benchmark_variance)
    alpha = float(
        (portfolio_excess.mean() - beta * benchmark_excess.mean()) * annualization
    )
    return beta, alpha


def rolling_beta(returns: pd.Series, benchmark: pd.Series, window: int) -> pd.Series:
    aligned = pd.concat([returns, benchmark], axis=1).dropna()
    return (
        aligned.iloc[:, 0].rolling(window).cov(aligned.iloc[:, 1])
        / aligned.iloc[:, 1].rolling(window).var()
    )


def drawdown(returns: pd.Series) -> pd.Series:
    wealth = (1.0 + returns).cumprod()
    return wealth / wealth.cummax() - 1.0


def maximum_drawdown(returns: pd.Series) -> float:
    _values(returns)
    return float(drawdown(returns).min())


def downside_deviation(returns: pd.Series, target: float = 0.0, annualization: int = 12) -> float:
    values = _values(returns)
    downside = np.minimum(values - target, 0.0)
    return float(np.sqrt(np.mean(downside**2)) * np.sqrt(annualization))


def value_at_risk(
    returns: pd.Series, confidence: float = 0.95, method: str = "historical"
) -> float:
    values = _values(returns)
    if not 0 < confidence < 1:
        raise DataQualityError("VaR confidence must be in (0, 1)")
    if method == "historical":
        return max(0.0, float(-np.quantile(values, 1.0 - confidence)))
    if method == "parametric":
        return max(0.0, float(-(values.mean() + norm.ppf(1.0 - confidence) * values.std(ddof=1))))
    raise DataQualityError(f"Unsupported VaR method: {method}")


def expected_shortfall(returns: pd.Series, confidence: float = 0.95) -> float:
    values = _values(returns)
    threshold = np.quantile(values, 1.0 - confidence)
    tail = values[values <= threshold]
    return max(0.0, float(-tail.mean()))


def risk_contributions(
    weights: np.ndarray, covariance: np.ndarray
) -> tuple[np.ndarray, np.ndarray]:
    variance = float(weights @ covariance @ weights)
    if variance <= 0:
        raise DataQualityError("Risk contributions require positive portfolio variance")
    volatility_value = np.sqrt(variance)
    marginal = covariance @ weights / volatility_value
    component = weights * marginal
    return marginal, component


def diversification_ratio(weights: np.ndarray, covariance: np.ndarray) -> float:
    return float((weights @ np.sqrt(np.diag(covariance))) / np.sqrt(weights @ covariance @ weights))


def _ratio(numerator: float, denominator: float) -> float | None:
    return None if abs(denominator) <= np.finfo(float).eps else float(numerator / denominator)


def risk_summary(
    returns: pd.Series,
    benchmark: pd.Series,
    risk_free: pd.Series | float = 0.0,
    annualization: int = 12,
) -> dict[str, float | None]:
    values = _values(returns)
    benchmark_values = _values(benchmark)
    if len(values) != len(benchmark_values):
        raise DataQualityError("Portfolio and benchmark returns must be exactly aligned")
    rf = np.full(len(values), risk_free) if np.isscalar(risk_free) else _values(risk_free)
    if len(rf) != len(values):
        raise DataQualityError("Risk-free returns must align")
    excess = values - rf
    active = values - benchmark_values
    vol = float(values.std(ddof=1) * np.sqrt(annualization))
    downside = downside_deviation(pd.Series(excess), annualization=annualization)
    max_dd = abs(maximum_drawdown(pd.Series(values)))
    cumulative = float(np.prod(1.0 + values) - 1.0)
    beta, alpha = beta_alpha(
        pd.Series(values),
        pd.Series(benchmark_values),
        annualization,
        risk_free=pd.Series(rf),
    )
    gains = np.maximum(values, 0).sum()
    losses = -np.minimum(values, 0).sum()
    return {
        "cumulative_return": cumulative,
        "volatility": vol,
        "beta": beta,
        "alpha": alpha,
        "tracking_error": float(active.std(ddof=1) * np.sqrt(annualization)),
        "information_ratio": _ratio(
            float(active.mean() * np.sqrt(annualization)), float(active.std(ddof=1))
        ),
        "sharpe": _ratio(float(excess.mean() * np.sqrt(annualization)), float(excess.std(ddof=1))),
        "sortino": _ratio(float(excess.mean() * annualization), downside),
        "calmar": _ratio(float(values.mean() * annualization), max_dd),
        "omega": _ratio(float(gains), float(losses)),
        "maximum_drawdown": -max_dd,
        "downside_deviation": downside,
        "historical_var_95": value_at_risk(pd.Series(values)),
        "parametric_var_95": value_at_risk(pd.Series(values), method="parametric"),
        "cvar_95": expected_shortfall(pd.Series(values)),
    }
