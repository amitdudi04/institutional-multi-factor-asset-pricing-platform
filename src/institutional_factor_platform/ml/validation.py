"""Calibration, bounded tuning, explainability, drift, and comparison controls."""

import hashlib
from dataclasses import dataclass
from itertools import product
from time import perf_counter

import numpy as np
import pandas as pd
import shap
from numpy.typing import NDArray
from scipy.stats import ks_2samp, wasserstein_distance
from sklearn.calibration import CalibratedClassifierCV
from sklearn.frozen import FrozenEstimator
from sklearn.inspection import permutation_importance

from institutional_factor_platform.exceptions import (
    DataQualityError,
    EvidenceIntegrityError,
    TemporalIntegrityError,
)
from institutional_factor_platform.ml.evaluation import classification_metrics, regression_metrics
from institutional_factor_platform.ml.models import ResearchModel, Task, create_model


@dataclass(frozen=True)
class TuningTrial:
    parameters: dict[str, object]
    metric: float | None
    status: str
    failure_reason: str | None
    duration_seconds: float


def bounded_grid_search(
    family: str,
    task: Task,
    features: tuple[str, ...],
    preprocessor_hash: str,
    target_hash: str,
    train_x: NDArray[np.float64],
    train_y: NDArray[np.float64],
    validation_x: NDArray[np.float64],
    validation_y: NDArray[np.float64],
    search_space: dict[str, tuple[object, ...]],
    *,
    maximum_trials: int,
    seed: int,
    threads: int = 1,
) -> tuple[ResearchModel, tuple[TuningTrial, ...]]:
    if maximum_trials < 1 or not search_space:
        raise DataQualityError("Hyperparameter search must be explicit and bounded")
    keys = tuple(sorted(search_space))
    candidates = list(product(*(search_space[k] for k in keys)))[:maximum_trials]
    trials = []
    best = None
    best_metric = -np.inf
    for values in candidates:
        params = dict(zip(keys, values, strict=True))
        started = perf_counter()
        try:
            model = create_model(
                family,
                task,
                features,
                preprocessor_hash,
                target_hash,
                seed=seed,
                threads=threads,
                parameters=params,
            ).fit(train_x, train_y)
            prediction = model.predict(validation_x, features)
            raw_metric: object = (
                classification_metrics(
                    validation_y, model.predict_probability(validation_x, features)
                )["roc_auc"]
                if task == "classification"
                else regression_metrics(validation_y, prediction)["spearman"]
            )
            metric = None if raw_metric is None else float(raw_metric)  # type: ignore[arg-type]
            score = -np.inf if metric is None else metric
            trials.append(
                TuningTrial(
                    params,
                    metric,
                    "PASS",
                    None,
                    perf_counter() - started,
                )
            )
            if score > best_metric:
                best_metric = score
                best = model
        except (ValueError, DataQualityError) as exc:
            trials.append(TuningTrial(params, None, "FAIL", str(exc), perf_counter() - started))
    if best is None:
        raise DataQualityError("Every bounded hyperparameter trial failed")
    return best, tuple(trials)


def calibrate_classifier(
    model: ResearchModel,
    validation_x: NDArray[np.float64],
    validation_y: NDArray[np.float64],
    *,
    method: str,
    validation_end: pd.Timestamp,
    test_start: pd.Timestamp,
) -> CalibratedClassifierCV:
    if model.task != "classification" or validation_end >= test_start:
        raise TemporalIntegrityError("Calibration must precede the test period")
    if method not in {"sigmoid", "isotonic"}:
        raise DataQualityError("Unsupported calibration method")
    calibration = CalibratedClassifierCV(FrozenEstimator(model.estimator), method=method)
    calibration.fit(validation_x, validation_y)
    return calibration


def linear_explanation(model: ResearchModel) -> pd.DataFrame:
    coefficients = getattr(model.estimator, "coef_", None)
    if coefficients is None:
        raise DataQualityError("Linear explanation requires coefficients")
    values = np.asarray(coefficients, dtype=float).reshape(-1)
    if len(values) != len(model.feature_names):
        raise EvidenceIntegrityError("Coefficient schema differs")
    return pd.DataFrame(
        {"feature": model.feature_names, "coefficient": values, "sign": np.sign(values)}
    )


def tree_explanations(
    model: ResearchModel,
    train_background: NDArray[np.float64],
    explained: NDArray[np.float64],
    y_validation: NDArray[np.float64],
    validation_x: NDArray[np.float64],
    *,
    background_dates: pd.Series,
    training_end: pd.Timestamp,
    seed: int,
) -> tuple[pd.DataFrame, pd.DataFrame, str]:
    dates = pd.to_datetime(background_dates, utc=True)
    end = pd.Timestamp(training_end)
    end = end.tz_localize("UTC") if end.tzinfo is None else end.tz_convert("UTC")
    if dates.max() > end:
        raise TemporalIntegrityError("SHAP background contains future observations")
    if train_background.shape[1] != len(model.feature_names) or explained.shape[1] != len(
        model.feature_names
    ):
        raise EvidenceIntegrityError("Explanation feature schema differs")
    estimator = model.estimator
    importance = permutation_importance(
        estimator, validation_x, y_validation, n_repeats=3, random_state=seed, n_jobs=1
    )
    permutation = pd.DataFrame(
        {"feature": model.feature_names, "permutation_importance": importance.importances_mean}
    )
    explainer = shap.TreeExplainer(estimator, data=train_background)
    values = explainer.shap_values(explained)
    if isinstance(values, list):
        values = values[-1]
    array = np.asarray(values, dtype=float)
    if array.ndim == 3:
        array = array[:, :, 1]
    if array.shape != explained.shape:
        raise EvidenceIntegrityError("SHAP output shape differs from feature matrix")
    shap_frame = pd.DataFrame(array, columns=model.feature_names)
    background_hash = hashlib.sha256(np.ascontiguousarray(train_background).tobytes()).hexdigest()
    return permutation, shap_frame, background_hash


def drift_report(
    reference: pd.DataFrame, comparison: pd.DataFrame, features: tuple[str, ...], *, bins: int = 10
) -> pd.DataFrame:
    if bins < 2:
        raise DataQualityError("PSI requires at least two bins")
    rows = []
    for feature in features:
        left = reference[feature].dropna().to_numpy(float)
        right = comparison[feature].dropna().to_numpy(float)
        if not len(left) or not len(right):
            raise DataQualityError("Drift population is empty")
        edges = np.unique(np.quantile(left, np.linspace(0, 1, bins + 1)))
        if len(edges) < 2:
            psi = 0.0
        else:
            a = np.histogram(left, bins=edges)[0] / len(left)
            b = np.histogram(right, bins=edges)[0] / len(right)
            a = np.clip(a, 1e-6, None)
            b = np.clip(b, 1e-6, None)
            psi = float(np.sum((b - a) * np.log(b / a)))
        rows.append(
            {
                "feature": feature,
                "reference_mean": float(np.mean(left)),
                "comparison_mean": float(np.mean(right)),
                "mean_shift": float(np.mean(right) - np.mean(left)),
                "variance_shift": float(np.var(right) - np.var(left)),
                "missingness_drift": float(
                    comparison[feature].isna().mean() - reference[feature].isna().mean()
                ),
                "psi": psi,
                "ks": float(ks_2samp(left, right).statistic),
                "wasserstein": float(wasserstein_distance(left, right)),
            }
        )
    return pd.DataFrame(rows)


def feature_family_ablations(
    features: tuple[str, ...], families: dict[str, tuple[str, ...]]
) -> dict[str, tuple[str, ...]]:
    result = {"complete": features}
    for family, members in sorted(families.items()):
        result[f"without_{family}"] = tuple(x for x in features if x not in set(members))
    if any(not value for value in result.values()):
        raise DataQualityError("Ablation removes every feature")
    return result
