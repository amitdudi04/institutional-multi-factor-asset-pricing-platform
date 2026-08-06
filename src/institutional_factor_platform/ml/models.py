"""Typed baseline, linear, forest, and XGBoost research models."""

import hashlib
import io
from dataclasses import dataclass
from typing import Literal, Protocol, TypeAlias, cast

import joblib
import numpy as np
from numpy.typing import NDArray
from sklearn.base import BaseEstimator
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.linear_model import ElasticNet, Lasso, LinearRegression, LogisticRegression, Ridge
from xgboost import XGBClassifier, XGBRegressor

from institutional_factor_platform.exceptions import DataQualityError, EvidenceIntegrityError

Task = Literal["regression", "classification", "ranking"]
FloatMatrix: TypeAlias = NDArray[np.float64]


class Predictor(Protocol):
    def fit(self, x: FloatMatrix, y: FloatMatrix) -> object: ...
    def predict(self, x: FloatMatrix) -> FloatMatrix: ...


class ConstantModel:
    def __init__(self, value: float | None = None) -> None:
        self.value = value

    def fit(self, x: FloatMatrix, y: FloatMatrix) -> "ConstantModel":
        if y.size == 0:
            raise DataQualityError("Cannot fit baseline on empty target")
        if self.value is None:
            self.value = float(np.mean(y))
        return self

    def predict(self, x: FloatMatrix) -> FloatMatrix:
        if self.value is None:
            raise DataQualityError("Baseline is not fitted")
        return np.full(x.shape[0], self.value, dtype=float)


@dataclass
class ResearchModel:
    model_id: str
    family: str
    task: Task
    feature_names: tuple[str, ...]
    preprocessor_hash: str
    target_hash: str
    seed: int
    estimator: Predictor

    def fit(self, x: FloatMatrix, y: FloatMatrix) -> "ResearchModel":
        if x.ndim != 2 or y.ndim != 1 or len(x) != len(y) or not len(y):
            raise DataQualityError("Model fit arrays are empty or misaligned")
        if (
            x.shape[1] != len(self.feature_names)
            or not np.isfinite(x).all()
            or not np.isfinite(y).all()
        ):
            raise DataQualityError("Model fit violates feature schema or finite-value policy")
        if self.task == "classification" and len(np.unique(y)) < 2:
            raise DataQualityError("Classification requires at least two target classes")
        self.estimator.fit(x, y)
        return self

    def predict(self, x: FloatMatrix, feature_names: tuple[str, ...]) -> FloatMatrix:
        if feature_names != self.feature_names:
            raise EvidenceIntegrityError("Prediction feature schema or order differs")
        values = np.asarray(self.estimator.predict(x), dtype=float)
        if values.shape != (len(x),) or not np.isfinite(values).all():
            raise DataQualityError("Model returned invalid predictions")
        return cast(FloatMatrix, values)

    def predict_probability(self, x: FloatMatrix, feature_names: tuple[str, ...]) -> FloatMatrix:
        if self.task != "classification" or feature_names != self.feature_names:
            raise DataQualityError("Probability prediction requires matching classification model")
        method = getattr(self.estimator, "predict_proba", None)
        if method is None:
            raise DataQualityError("Estimator does not provide probabilities")
        values = np.asarray(method(x), dtype=float)[:, 1]
        if ((values < 0) | (values > 1)).any():
            raise DataQualityError("Estimator returned invalid probabilities")
        return cast(FloatMatrix, values)

    def trusted_bytes(self) -> bytes:
        buffer = io.BytesIO()
        joblib.dump(self, buffer)
        return buffer.getvalue()

    @staticmethod
    def load_trusted(content: bytes, expected_checksum: str) -> "ResearchModel":
        if hashlib.sha256(content).hexdigest() != expected_checksum:
            raise EvidenceIntegrityError(
                "Model checksum failed before trusted-local deserialization"
            )
        value = joblib.load(io.BytesIO(content))
        if not isinstance(value, ResearchModel):
            raise EvidenceIntegrityError("Authenticated artifact is not a supported research model")
        return value


def create_model(
    family: str,
    task: Task,
    features: tuple[str, ...],
    preprocessor_hash: str,
    target_hash: str,
    *,
    seed: int,
    threads: int = 1,
    parameters: dict[str, object] | None = None,
) -> ResearchModel:
    params = dict(parameters or {})
    if family == "zero":
        estimator: Predictor = ConstantModel(0.0)
    elif family == "historical_mean":
        estimator = ConstantModel()
    elif family in {"linear", "factor_composite"}:
        estimator = LinearRegression(**params)
    elif family == "ridge":
        estimator = Ridge(random_state=seed, **params)
    elif family == "lasso":
        estimator = Lasso(random_state=seed, **params)
    elif family == "elastic_net":
        estimator = ElasticNet(random_state=seed, **params)
    elif family == "logistic":
        estimator = LogisticRegression(random_state=seed, max_iter=1_000, **params)
    elif family == "random_forest":
        cls: type[BaseEstimator] = (
            RandomForestClassifier if task == "classification" else RandomForestRegressor
        )
        estimator = cast(Predictor, cls(random_state=seed, n_jobs=threads, **params))
    elif family == "xgboost":
        xgb: type[BaseEstimator] = XGBClassifier if task == "classification" else XGBRegressor
        defaults: dict[str, object] = {
            "random_state": seed,
            "n_jobs": threads,
            "tree_method": "hist",
            "n_estimators": 100,
            "max_depth": 3,
            "learning_rate": 0.05,
        }
        defaults.update(params)
        estimator = cast(Predictor, xgb(**defaults))
    else:
        raise DataQualityError(f"Unsupported model family: {family}")
    identifier = hashlib.sha256(
        f"{family}|{task}|{features}|{preprocessor_hash}|{target_hash}|{seed}|{sorted(params.items())}".encode()
    ).hexdigest()
    return ResearchModel(
        f"model-{identifier[:32]}",
        family,
        task,
        features,
        preprocessor_hash,
        target_hash,
        seed,
        estimator,
    )
