"""Predictive, classification, ranking, comparison, and uncertainty metrics."""

import math
from itertools import pairwise

import numpy as np
import pandas as pd
from numpy.typing import NDArray
from scipy.stats import pearsonr, spearmanr
from sklearn.metrics import (
    accuracy_score,
    average_precision_score,
    balanced_accuracy_score,
    brier_score_loss,
    confusion_matrix,
    f1_score,
    log_loss,
    mean_absolute_error,
    mean_squared_error,
    median_absolute_error,
    precision_score,
    r2_score,
    recall_score,
    roc_auc_score,
)

from institutional_factor_platform.exceptions import DataQualityError


def regression_metrics(
    y: NDArray[np.float64], prediction: NDArray[np.float64]
) -> dict[str, float | None]:
    _aligned(y, prediction)
    error = prediction - y
    return {
        "mae": float(mean_absolute_error(y, prediction)),
        "rmse": float(math.sqrt(mean_squared_error(y, prediction))),
        "median_absolute_error": float(median_absolute_error(y, prediction)),
        "r_squared": float(r2_score(y, prediction)) if len(y) > 1 else None,
        "pearson": _correlation(pearsonr, y, prediction),
        "spearman": _correlation(spearmanr, y, prediction),
        "information_coefficient": _correlation(spearmanr, y, prediction),
        "directional_accuracy": float(np.mean(np.sign(y) == np.sign(prediction))),
        "prediction_bias": float(np.mean(error)),
        "residual_dispersion": float(np.std(error, ddof=1)) if len(error) > 1 else None,
    }


def classification_metrics(
    y: NDArray[np.float64], probability: NDArray[np.float64], threshold: float = 0.5
) -> dict[str, object]:
    _aligned(y, probability)
    if ((probability < 0) | (probability > 1)).any():
        raise DataQualityError("Classification probability lies outside [0,1]")
    predicted = (probability >= threshold).astype(int)
    two_classes = len(np.unique(y)) == 2
    return {
        "accuracy": float(accuracy_score(y, predicted)),
        "balanced_accuracy": float(balanced_accuracy_score(y, predicted)),
        "precision": float(precision_score(y, predicted, zero_division=0)),
        "recall": float(recall_score(y, predicted, zero_division=0)),
        "f1": float(f1_score(y, predicted, zero_division=0)),
        "roc_auc": float(roc_auc_score(y, probability)) if two_classes else None,
        "pr_auc": float(average_precision_score(y, probability)) if two_classes else None,
        "log_loss": float(log_loss(y, probability, labels=[0, 1])),
        "brier": float(brier_score_loss(y, probability)),
        "calibration_error": calibration_error(y, probability),
        "confusion_matrix": confusion_matrix(y, predicted, labels=[0, 1]).tolist(),
    }


def ranking_metrics(
    frame: pd.DataFrame,
    *,
    target: str = "target",
    prediction: str = "prediction",
    top_fraction: float = 0.2,
) -> dict[str, float | None]:
    if frame.empty or set(frame.columns) < {"formation_date", target, prediction}:
        raise DataQualityError("Ranking evaluation lacks cross-sectional identity")
    daily = (
        frame.groupby("formation_date", sort=True)
        .apply(lambda x: x[target].corr(x[prediction], method="spearman"), include_groups=False)
        .dropna()
    )
    sorted_frame = frame.assign(_q=frame.groupby("formation_date")[prediction].rank(pct=True))
    top = sorted_frame.loc[sorted_frame["_q"] >= 1 - top_fraction, target].mean()
    bottom = sorted_frame.loc[sorted_frame["_q"] <= top_fraction, target].mean()
    return {
        "spearman": None if daily.empty else float(daily.mean()),
        "ic_dispersion": None if len(daily) < 2 else float(daily.std(ddof=1)),
        "top_minus_bottom": float(top - bottom),
        "top_k_precision": float(
            (sorted_frame.loc[sorted_frame["_q"] >= 1 - top_fraction, target] > 0).mean()
        ),
        "prediction_turnover": _rank_turnover(sorted_frame, prediction),
    }


def calibration_error(
    y: NDArray[np.float64], probability: NDArray[np.float64], bins: int = 10
) -> float:
    edges = np.linspace(0, 1, bins + 1)
    result = 0.0
    for low, high in pairwise(edges):
        mask = (probability >= low) & (probability <= high if high == 1 else probability < high)
        if mask.any():
            result += float(mask.mean() * abs(y[mask].mean() - probability[mask].mean()))
    return result


def block_bootstrap_ic(
    frame: pd.DataFrame, *, block_length: int, resamples: int, seed: int
) -> dict[str, float | None]:
    if block_length < 1 or resamples < 10:
        raise DataQualityError("Bootstrap budget is invalid")
    dates = np.array(sorted(frame["formation_date"].unique()))
    rng = np.random.default_rng(seed)
    values = []
    for _ in range(resamples):
        sampled: list[object] = []
        while len(sampled) < len(dates):
            start = int(rng.integers(0, max(1, len(dates) - block_length + 1)))
            sampled.extend(dates[start : start + block_length])
        parts = [frame.loc[frame["formation_date"].eq(d)] for d in sampled[: len(dates)]]
        sample = pd.concat(parts)
        value = sample["target"].corr(sample["prediction"], method="spearman")
        if pd.notna(value):
            values.append(float(value))
    if not values:
        return {"estimate": None, "lower": None, "upper": None}
    return {
        "estimate": float(np.mean(values)),
        "lower": float(np.quantile(values, 0.025)),
        "upper": float(np.quantile(values, 0.975)),
    }


def _aligned(left: NDArray[np.float64], right: NDArray[np.float64]) -> None:
    if (
        left.shape != right.shape
        or left.ndim != 1
        or not len(left)
        or not np.isfinite(left).all()
        or not np.isfinite(right).all()
    ):
        raise DataQualityError("Metric inputs are empty, non-finite, or misaligned")


def _correlation(
    function: object, left: NDArray[np.float64], right: NDArray[np.float64]
) -> float | None:
    if len(left) < 2 or np.std(left) == 0 or np.std(right) == 0:
        return None
    result = function(left, right)  # type: ignore[operator]
    return float(result.statistic)


def _rank_turnover(frame: pd.DataFrame, prediction: str) -> float | None:
    pivot = frame.pivot(index="formation_date", columns="security_id", values=prediction).rank(
        axis=1, pct=True
    )
    return None if len(pivot) < 2 else float(pivot.diff().abs().iloc[1:].mean(axis=1).mean())
