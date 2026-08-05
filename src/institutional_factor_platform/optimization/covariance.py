"""Covariance estimation, regularization, and numerical diagnostics."""

import numpy as np
import pandas as pd
from sklearn.covariance import LedoitWolf, MinCovDet

from institutional_factor_platform.exceptions import DataQualityError


def estimate_covariance(
    returns: pd.DataFrame, method: str = "sample", *, annualization: int = 12
) -> np.ndarray:
    clean = returns.dropna()
    if len(clean) < 3 or clean.shape[1] < 1 or not np.isfinite(clean.to_numpy()).all():
        raise DataQualityError("Covariance estimation requires finite complete observations")
    values = clean.to_numpy(dtype=float)
    if method == "sample":
        covariance = np.cov(values, rowvar=False, ddof=1)
    elif method == "ledoit_wolf":
        covariance = LedoitWolf().fit(values).covariance_
    elif method == "robust":
        if len(clean) <= clean.shape[1] * 2:
            raise DataQualityError(
                "Robust covariance requires more than twice as many observations as assets"
            )
        covariance = MinCovDet(random_state=0).fit(values).covariance_
    else:
        raise DataQualityError(f"Unsupported covariance method: {method}")
    covariance = np.atleast_2d(covariance) * annualization
    validate_covariance(covariance)
    return covariance


def regularize_covariance(covariance: np.ndarray, floor: float = 1e-10) -> np.ndarray:
    matrix = np.asarray(covariance, dtype=float)
    if matrix.ndim != 2 or matrix.shape[0] != matrix.shape[1] or not np.isfinite(matrix).all():
        raise DataQualityError("Covariance matrix must be finite and square")
    symmetric = (matrix + matrix.T) / 2.0
    values, vectors = np.linalg.eigh(symmetric)
    repaired = vectors @ np.diag(np.maximum(values, floor)) @ vectors.T
    validate_covariance(repaired)
    return repaired


def validate_covariance(covariance: np.ndarray) -> dict[str, float]:
    matrix = np.asarray(covariance, dtype=float)
    if matrix.ndim != 2 or matrix.shape[0] != matrix.shape[1] or not np.isfinite(matrix).all():
        raise DataQualityError("Covariance matrix must be finite and square")
    if not np.allclose(matrix, matrix.T, atol=1e-10):
        raise DataQualityError("Covariance matrix must be symmetric")
    eigenvalues = np.linalg.eigvalsh(matrix)
    if eigenvalues.min() < -1e-10:
        raise DataQualityError("Covariance matrix must be positive semidefinite")
    return {
        "minimum_eigenvalue": float(eigenvalues.min()),
        "maximum_eigenvalue": float(eigenvalues.max()),
        "condition_number": float(np.linalg.cond(matrix)),
        "rank": float(np.linalg.matrix_rank(matrix)),
    }
