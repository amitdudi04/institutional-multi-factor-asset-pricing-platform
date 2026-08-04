"""Named statistical tests with explicit statistics and p-values."""

import pandas as pd
import statsmodels.api as sm
from statsmodels.stats.diagnostic import acorr_ljungbox, het_breuschpagan, het_white
from statsmodels.stats.stattools import durbin_watson, jarque_bera
from statsmodels.tsa.stattools import adfuller

from institutional_factor_platform.exceptions import DataQualityError


def residual_tests(
    residuals: pd.Series, design: pd.DataFrame, *, ljung_box_lags: int = 5
) -> dict[str, object]:
    values = pd.to_numeric(residuals, errors="coerce").dropna().to_numpy(dtype=float)
    if len(values) < max(8, ljung_box_lags + 2):
        raise DataQualityError("Residual diagnostics require more complete observations")
    aligned = design.loc[residuals.dropna().index].astype(float)
    exog = sm.add_constant(aligned, has_constant="add").to_numpy(dtype=float)
    jb, jb_p, skew, kurtosis = jarque_bera(values)
    bp_lm, bp_p, bp_f, bp_f_p = het_breuschpagan(values, exog)
    if exog.shape[1] > 1 and len(values) > exog.shape[1] * 2:
        white_lm, white_p, white_f, white_f_p = het_white(values, exog)
        white: dict[str, float] | None = {
            "lm_statistic": float(white_lm),
            "lm_p_value": float(white_p),
            "f_statistic": float(white_f),
            "f_p_value": float(white_f_p),
        }
    else:
        white = None
    lag = min(ljung_box_lags, len(values) // 3)
    ljung = acorr_ljungbox(values, lags=[lag], return_df=True).iloc[0]
    adf_stat, adf_p, adf_lags, adf_nobs, *_ = adfuller(values, autolag="AIC")
    return {
        "jarque_bera": {
            "statistic": float(jb),
            "p_value": float(jb_p),
            "skew": float(skew),
            "kurtosis": float(kurtosis),
        },
        "breusch_pagan": {
            "lm_statistic": float(bp_lm),
            "lm_p_value": float(bp_p),
            "f_statistic": float(bp_f),
            "f_p_value": float(bp_f_p),
        },
        "white": white,
        "durbin_watson": float(durbin_watson(values)),
        "ljung_box": {
            "lag": lag,
            "statistic": float(ljung["lb_stat"]),
            "p_value": float(ljung["lb_pvalue"]),
        },
        "adf": {
            "statistic": float(adf_stat),
            "p_value": float(adf_p),
            "lags": int(adf_lags),
            "observations": int(adf_nobs),
        },
    }


def normal_prediction_interval(
    fitted: pd.Series, prediction_standard_error: pd.Series, confidence_level: float
) -> pd.DataFrame:
    from scipy.stats import norm

    z_value = float(norm.ppf(0.5 + confidence_level / 2.0))
    return pd.DataFrame(
        {
            "prediction_lower": fitted - z_value * prediction_standard_error,
            "prediction_upper": fitted + z_value * prediction_standard_error,
        }
    )
