"""Fit/transform preprocessing with explicit training-window identity."""

import hashlib
import json
from dataclasses import dataclass

import pandas as pd
from sklearn.preprocessing import RobustScaler, StandardScaler

from institutional_factor_platform.exceptions import DataQualityError, TemporalIntegrityError


@dataclass
class SafePreprocessor:
    feature_names: tuple[str, ...]
    missing_policy: str
    scaling: str
    winsor_lower: float | None = None
    winsor_upper: float | None = None
    fitted_through: pd.Timestamp | None = None
    medians: pd.Series | None = None
    lower: pd.Series | None = None
    upper: pd.Series | None = None
    scaler: StandardScaler | RobustScaler | None = None

    def fit(
        self, frame: pd.DataFrame, dates: pd.Series, *, allowed_training_end: pd.Timestamp
    ) -> "SafePreprocessor":
        self._validate_columns(frame)
        observed = pd.to_datetime(dates, utc=True)
        end = pd.Timestamp(allowed_training_end)
        if end.tzinfo is None:
            end = end.tz_localize("UTC")
        else:
            end = end.tz_convert("UTC")
        if observed.max() > end:
            raise TemporalIntegrityError(
                "Preprocessor fit includes validation or test observations"
            )
        values = frame.loc[:, self.feature_names].astype(float)
        if self.missing_policy == "reject" and values.isna().any().any():
            raise DataQualityError("Missing feature encountered under reject policy")
        if self.missing_policy == "training_median":
            self.medians = values.median()
            values = values.fillna(self.medians)
        elif self.missing_policy not in {"native", "reject"}:
            raise DataQualityError("Unsupported fitted missingness policy")
        if self.winsor_lower is not None and self.winsor_upper is not None:
            self.lower = values.quantile(self.winsor_lower)
            self.upper = values.quantile(self.winsor_upper)
            values = values.clip(self.lower, self.upper, axis=1)
        if self.scaling == "standard":
            self.scaler = StandardScaler().fit(values)
        elif self.scaling == "robust":
            self.scaler = RobustScaler().fit(values)
        elif self.scaling not in {"none", "percentile", "rank"}:
            raise DataQualityError("Unsupported scaling policy")
        self.fitted_through = end
        return self

    def transform(self, frame: pd.DataFrame) -> pd.DataFrame:
        if self.fitted_through is None:
            raise DataQualityError("Preprocessor is not fitted")
        self._validate_columns(frame)
        values = frame.loc[:, self.feature_names].astype(float).copy()
        if self.medians is not None:
            values = values.fillna(self.medians)
        if self.missing_policy != "native" and values.isna().any().any():
            raise DataQualityError("Missing feature remains after preprocessing")
        if self.lower is not None and self.upper is not None:
            values = values.clip(self.lower, self.upper, axis=1)
        if self.scaling in {"percentile", "rank"}:
            values = values.rank(axis=0, pct=self.scaling == "percentile")
        elif self.scaler is not None:
            values = pd.DataFrame(
                self.scaler.transform(values), columns=self.feature_names, index=values.index
            )
        return values

    def identity(self) -> str:
        if self.fitted_through is None:
            raise DataQualityError("Unfitted preprocessor has no identity")
        payload = {
            "features": self.feature_names,
            "missing": self.missing_policy,
            "scaling": self.scaling,
            "fitted_through": self.fitted_through.isoformat(),
            "medians": None if self.medians is None else self.medians.to_dict(),
            "lower": None if self.lower is None else self.lower.to_dict(),
            "upper": None if self.upper is None else self.upper.to_dict(),
        }
        return hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()

    def _validate_columns(self, frame: pd.DataFrame) -> None:
        actual = tuple(column for column in frame if column in set(self.feature_names))
        if actual != self.feature_names:
            raise DataQualityError("Feature order or schema differs from preprocessor identity")


def cross_sectional_median(
    frame: pd.DataFrame, features: tuple[str, ...], dates: pd.Series
) -> pd.DataFrame:
    result = frame.copy()
    groups = pd.to_datetime(dates, utc=True)
    for feature in features:
        result[feature] = result[feature].fillna(
            result.groupby(groups)[feature].transform("median")
        )
    return result
