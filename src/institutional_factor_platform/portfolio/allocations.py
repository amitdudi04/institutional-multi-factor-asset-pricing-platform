"""Transparent non-optimized portfolio allocation methods."""

import numpy as np

from institutional_factor_platform.exceptions import DataQualityError


def equal_weight(asset_count: int) -> np.ndarray:
    if asset_count <= 0:
        raise DataQualityError("Equal-weight portfolio requires at least one asset")
    return np.full(asset_count, 1.0 / asset_count)


def market_cap_weight(market_caps: np.ndarray) -> np.ndarray:
    values = np.asarray(market_caps, dtype=float)
    if values.ndim != 1 or not np.isfinite(values).all() or (values <= 0).any():
        raise DataQualityError("Market capitalizations must be finite positive values")
    return values / values.sum()
