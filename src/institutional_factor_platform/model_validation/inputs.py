"""Fail-closed validation for regression and covariance inputs."""

import numpy as np
import pandas as pd

from institutional_factor_platform.exceptions import DataQualityError


def validate_regression_frame(
    frame: pd.DataFrame, dependent: str, factors: tuple[str, ...], minimum: int
) -> pd.DataFrame:
    required = (dependent, *factors)
    missing = set(required) - set(frame.columns)
    if missing:
        raise DataQualityError(f"Regression input is missing columns: {sorted(missing)}")
    clean = frame.loc[:, required].apply(pd.to_numeric, errors="coerce").dropna()
    if len(clean) < minimum:
        raise DataQualityError(f"Regression requires at least {minimum} complete observations")
    if not np.isfinite(clean.to_numpy()).all():
        raise DataQualityError("Regression input contains non-finite observations")
    if clean[dependent].nunique() <= 1:
        raise DataQualityError("Dependent return is constant")
    constant = [name for name in factors if clean[name].nunique() <= 1]
    if constant:
        raise DataQualityError(f"Factor columns are constant: {constant}")
    matrix = clean.loc[:, factors].to_numpy(dtype=float)
    if np.linalg.matrix_rank(np.column_stack([np.ones(len(clean)), matrix])) < len(factors) + 1:
        raise DataQualityError("Factor design matrix is rank deficient")
    covariance = np.cov(matrix, rowvar=False)
    if not np.isfinite(np.atleast_2d(covariance)).all():
        raise DataQualityError("Factor covariance matrix is invalid")
    return clean


def covariance_diagnostics(frame: pd.DataFrame, factors: tuple[str, ...]) -> dict[str, object]:
    matrix = frame.loc[:, factors].to_numpy(dtype=float)
    covariance = np.atleast_2d(np.cov(matrix, rowvar=False))
    return {
        "rank": int(np.linalg.matrix_rank(matrix)),
        "factor_count": len(factors),
        "condition_number": float(np.linalg.cond(matrix)),
        "covariance": covariance.tolist(),
    }
