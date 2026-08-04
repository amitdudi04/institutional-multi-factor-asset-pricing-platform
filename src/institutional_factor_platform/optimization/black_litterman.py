"""Black-Litterman and modular Bayesian posterior construction."""

import numpy as np

from institutional_factor_platform.exceptions import DataQualityError
from institutional_factor_platform.optimization.covariance import validate_covariance


def black_litterman_posterior(
    covariance: np.ndarray,
    market_weights: np.ndarray,
    risk_aversion: float,
    views: np.ndarray,
    view_returns: np.ndarray,
    omega: np.ndarray,
    *,
    tau: float = 0.05,
) -> tuple[np.ndarray, np.ndarray]:
    validate_covariance(covariance)
    n = covariance.shape[0]
    weights = np.asarray(market_weights, dtype=float)
    p = np.asarray(views, dtype=float)
    q = np.asarray(view_returns, dtype=float)
    uncertainty = np.asarray(omega, dtype=float)
    if (
        weights.shape != (n,)
        or p.ndim != 2
        or p.shape[1] != n
        or q.shape != (p.shape[0],)
        or uncertainty.shape != (p.shape[0], p.shape[0])
        or risk_aversion <= 0
        or tau <= 0
    ):
        raise DataQualityError("Black-Litterman inputs are dimensionally invalid")
    prior = risk_aversion * covariance @ weights
    prior_precision = np.linalg.inv(tau * covariance)
    view_precision = np.linalg.inv(uncertainty)
    posterior_covariance = np.linalg.inv(prior_precision + p.T @ view_precision @ p)
    posterior_mean = posterior_covariance @ (prior_precision @ prior + p.T @ view_precision @ q)
    return posterior_mean, covariance + posterior_covariance


def bayesian_mean(
    prior_mean: np.ndarray,
    prior_covariance: np.ndarray,
    sample_mean: np.ndarray,
    sample_covariance: np.ndarray,
) -> tuple[np.ndarray, np.ndarray]:
    if prior_mean.shape != sample_mean.shape:
        raise DataQualityError("Bayesian mean vectors must align")
    prior_precision = np.linalg.inv(prior_covariance)
    sample_precision = np.linalg.inv(sample_covariance)
    posterior_covariance = np.linalg.inv(prior_precision + sample_precision)
    posterior_mean = posterior_covariance @ (
        prior_precision @ prior_mean + sample_precision @ sample_mean
    )
    return posterior_mean, posterior_covariance
