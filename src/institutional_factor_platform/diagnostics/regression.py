"""Residual, multicollinearity, and influence diagnostics."""

import numpy as np
import pandas as pd
import statsmodels.api as sm
from statsmodels.stats.outliers_influence import variance_inflation_factor

from institutional_factor_platform.model_validation.inputs import covariance_diagnostics
from institutional_factor_platform.regression.engine import RegressionResult
from institutional_factor_platform.statistical_tests.tests import residual_tests


def regression_diagnostics(
    result: RegressionResult, frame: pd.DataFrame, factors: tuple[str, ...]
) -> tuple[dict[str, object], pd.DataFrame]:
    clean = frame.loc[result.residuals.index, factors].astype(float)
    design = sm.add_constant(clean, has_constant="add")
    fitted = sm.OLS(result.residuals + result.fitted, design).fit()
    influence = fitted.get_influence()
    summary = influence.summary_frame()
    influence_table = pd.DataFrame(
        {
            "observation": [str(value) for value in clean.index],
            "leverage": np.asarray(summary["hat_diag"], dtype=float),
            "cooks_distance": np.asarray(summary["cooks_d"], dtype=float),
            "studentized_residual": np.asarray(summary["student_resid"], dtype=float),
        }
    )
    vif = [
        {"term": str(name), "vif": float(variance_inflation_factor(design.to_numpy(), index))}
        for index, name in enumerate(design.columns)
    ]
    diagnostics = {
        "residual_tests": residual_tests(result.residuals, clean),
        "multicollinearity": {"vif": vif, **covariance_diagnostics(clean, factors)},
        "influence": {
            "maximum_leverage": float(influence_table["leverage"].max()),
            "maximum_cooks_distance": float(influence_table["cooks_distance"].max()),
        },
    }
    return diagnostics, influence_table
