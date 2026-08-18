"""OLS/WLS, rolling, expanding, panel, and Fama-MacBeth estimators."""

from dataclasses import dataclass
from typing import Literal

import numpy as np
import pandas as pd
import statsmodels.api as sm

from institutional_factor_platform.exceptions import DataQualityError
from institutional_factor_platform.model_validation.inputs import validate_regression_frame

Covariance = Literal["nonrobust", "HC0", "HC1", "HC2", "HC3", "HAC"]


@dataclass(frozen=True, slots=True)
class RegressionResult:
    model_id: str
    estimator: str
    covariance: str
    nobs: int
    df_resid: float
    coefficients: pd.DataFrame
    fitted: pd.Series
    residuals: pd.Series
    metrics: dict[str, float]


def fit_regression(
    frame: pd.DataFrame,
    dependent: str,
    factors: tuple[str, ...],
    *,
    model_id: str = "custom",
    weights: pd.Series | None = None,
    covariance: Covariance = "HAC",
    hac_lags: int = 3,
    confidence_level: float = 0.95,
    minimum_observations: int = 8,
) -> RegressionResult:
    clean = validate_regression_frame(frame, dependent, factors, minimum_observations)
    design = sm.add_constant(clean.loc[:, factors], has_constant="add")
    if weights is None:
        fitted = sm.OLS(clean[dependent], design).fit()
        estimator = "OLS"
    else:
        aligned = pd.to_numeric(weights.reindex(clean.index), errors="coerce")
        if aligned.isna().any() or (aligned <= 0).any() or not np.isfinite(aligned).all():
            raise DataQualityError("WLS weights must be finite, positive, and index-aligned")
        fitted = sm.WLS(clean[dependent], design, weights=aligned).fit()
        estimator = "WLS"
    if covariance == "HAC":
        if hac_lags >= len(clean):
            raise DataQualityError("HAC lags must be smaller than the observation count")
        robust = fitted.get_robustcov_results(cov_type="HAC", maxlags=hac_lags, use_correction=True)
    elif covariance == "nonrobust":
        robust = fitted
    else:
        robust = fitted.get_robustcov_results(cov_type=covariance)
    alpha = 1.0 - confidence_level
    intervals = np.asarray(robust.conf_int(alpha=alpha))
    names = tuple(str(name) for name in design.columns)
    coefficients = pd.DataFrame(
        {
            "term": names,
            "estimate": np.asarray(robust.params, dtype=float),
            "standard_error": np.asarray(robust.bse, dtype=float),
            "t_statistic": np.asarray(robust.tvalues, dtype=float),
            "p_value": np.asarray(robust.pvalues, dtype=float),
            "confidence_lower": intervals[:, 0],
            "confidence_upper": intervals[:, 1],
        }
    )
    metrics = {
        "r_squared": float(fitted.rsquared),
        "adjusted_r_squared": float(fitted.rsquared_adj),
        "aic": float(fitted.aic),
        "bic": float(fitted.bic),
        "residual_standard_error": float(np.sqrt(fitted.ssr / fitted.df_resid)),
    }
    return RegressionResult(
        model_id,
        estimator,
        covariance,
        int(fitted.nobs),
        float(fitted.df_resid),
        coefficients,
        pd.Series(np.asarray(fitted.fittedvalues), index=clean.index, name="fitted"),
        pd.Series(np.asarray(fitted.resid), index=clean.index, name="residual"),
        metrics,
    )


def window_regressions(
    frame: pd.DataFrame,
    date_column: str,
    dependent: str,
    factors: tuple[str, ...],
    *,
    window: int,
    expanding: bool = False,
    **kwargs: object,
) -> pd.DataFrame:
    ordered = frame.sort_values(date_column, kind="stable")
    if ordered[date_column].duplicated().any():
        raise DataQualityError("Rolling regressions require one observation per date")
    rows: list[dict[str, object]] = []
    minimum_value = kwargs.get("minimum_observations", 8)
    if isinstance(minimum_value, bool) or not isinstance(minimum_value, int):
        raise DataQualityError("Rolling minimum_observations must be an integer")
    minimum = minimum_value
    for end in range(window, len(ordered) + 1):
        start = 0 if expanding else end - window
        sample = ordered.iloc[start:end]
        if len(sample.dropna(subset=[dependent, *factors])) < minimum:
            continue
        result = fit_regression(sample, dependent, factors, **kwargs)  # type: ignore[arg-type]
        for record in result.coefficients.to_dict("records"):
            rows.append(
                {
                    "window_end": sample[date_column].iloc[-1],
                    "window_start": sample[date_column].iloc[0],
                    **record,
                }
            )
    return pd.DataFrame(rows)


def fit_panel(
    frame: pd.DataFrame,
    dependent: str,
    factors: tuple[str, ...],
    *,
    entity: str,
    time: str,
    entity_effects: bool = False,
    time_effects: bool = False,
    **kwargs: object,
) -> RegressionResult:
    augmented = frame.copy()
    extra: list[str] = []
    for column, enabled, prefix in (
        (entity, entity_effects, "entity"),
        (time, time_effects, "time"),
    ):
        if enabled:
            dummies = pd.get_dummies(augmented[column], prefix=prefix, drop_first=True, dtype=float)
            augmented = pd.concat([augmented, dummies], axis=1)
            extra.extend(str(value) for value in dummies.columns)
    return fit_regression(augmented, dependent, (*factors, *extra), **kwargs)  # type: ignore[arg-type]


def fama_macbeth(
    frame: pd.DataFrame,
    date_column: str,
    dependent: str,
    exposures: tuple[str, ...],
    *,
    minimum_cross_section: int,
    hac_lags: int = 0,
) -> pd.DataFrame:
    estimates: list[pd.Series] = []
    for current_date, group in frame.groupby(date_column, sort=True):
        if len(group.dropna(subset=[dependent, *exposures])) < minimum_cross_section:
            continue
        result = fit_regression(
            group,
            dependent,
            exposures,
            covariance="nonrobust",
            minimum_observations=minimum_cross_section,
        )
        values = result.coefficients.set_index("term")["estimate"]
        values.name = current_date
        estimates.append(values)
    if len(estimates) <= hac_lags + 1:
        raise DataQualityError("Insufficient valid cross-sections for Fama-MacBeth inference")
    periods = pd.DataFrame(estimates)
    rows: list[dict[str, float | str | int]] = []
    for term in periods:
        intercept = sm.add_constant(pd.DataFrame(index=periods.index), has_constant="add")
        result = sm.OLS(periods[term], intercept).fit(
            cov_type="HAC", cov_kwds={"maxlags": hac_lags, "use_correction": True}
        )
        rows.append(
            {
                "term": str(term),
                "estimate": float(result.params.iloc[0]),
                "standard_error": float(result.bse.iloc[0]),
                "t_statistic": float(result.tvalues.iloc[0]),
                "p_value": float(result.pvalues.iloc[0]),
                "periods": len(periods),
            }
        )
    return pd.DataFrame(rows)
