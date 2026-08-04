"""Deterministic hierarchical risk-parity allocation."""

import numpy as np
from scipy.cluster.hierarchy import leaves_list, linkage
from scipy.spatial.distance import squareform

from institutional_factor_platform.optimization.covariance import validate_covariance


def hierarchical_risk_parity(covariance: np.ndarray) -> np.ndarray:
    validate_covariance(covariance)
    volatility = np.sqrt(np.diag(covariance))
    correlation = covariance / np.outer(volatility, volatility)
    distance = np.sqrt(np.maximum(0.0, (1.0 - correlation) / 2.0))
    order = leaves_list(linkage(squareform(distance, checks=False), method="single")).tolist()
    weights: np.ndarray = np.ones(len(order), dtype=float)
    clusters = [order]
    while clusters:
        next_clusters: list[list[int]] = []
        for cluster in clusters:
            if len(cluster) <= 1:
                continue
            split = len(cluster) // 2
            left, right = cluster[:split], cluster[split:]
            left_variance = _cluster_variance(covariance, left)
            right_variance = _cluster_variance(covariance, right)
            allocation = 1.0 - left_variance / (left_variance + right_variance)
            weights[left] *= allocation
            weights[right] *= 1.0 - allocation
            next_clusters.extend((left, right))
        clusters = next_clusters
    return weights / weights.sum()


def _cluster_variance(covariance: np.ndarray, indices: list[int]) -> float:
    subset = covariance[np.ix_(indices, indices)]
    inverse_variance = 1.0 / np.diag(subset)
    weights = inverse_variance / inverse_variance.sum()
    return float(weights @ subset @ weights)
