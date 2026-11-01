"""Independent small reference checks for the research Phase 2 audit."""

from datetime import UTC, date, datetime
from math import prod

import numpy as np
import pandas as pd
import pytest
from scipy.stats import t as student_t

from institutional_factor_platform.asset_pricing.inputs import (
    _holding_period_market_factors,
    build_research_panel,
)
from institutional_factor_platform.exceptions import DataQualityError, TemporalIntegrityError
from institutional_factor_platform.regression.engine import fit_regression


def test_market_and_cash_match_the_exact_holding_interval() -> None:
    days = [date(2020, 1, 31), date(2020, 2, 3), date(2020, 2, 4)]
    rows = []
    for day, market, cash in zip(days, [0.5, -0.1, 0.2], [0.3, 0.01, 0.02], strict=True):
        for factor, value in [
            ("market_return", market),
            ("risk_free_rate", cash),
            ("excess_return", market - cash),
        ]:
            rows.append(
                {
                    "security_id": "A",
                    "date": day,
                    "factor_id": factor,
                    "raw_value": value,
                    "available_at": datetime.combine(day, datetime.min.time(), tzinfo=UTC),
                }
            )
    portfolios = pd.DataFrame(
        [
            {
                "formation_date": days[0],
                "date": days[-1],
                "factor_id": "value",
                "quantile": q,
                "value_weighted_return": r,
                "available_at": datetime(2020, 2, 4, tzinfo=UTC),
            }
            for q, r in [(1, 0.03), (3, 0.06)]
        ]
    )
    panel = build_research_panel(pd.DataFrame(rows), portfolios, {"HML": "value"})
    cash = prod([1.01, 1.02]) - 1
    market = prod([0.9, 1.2]) - 1
    np.testing.assert_allclose(panel.risk_free_rate, cash)
    np.testing.assert_allclose(panel.market_excess, market - cash)
    np.testing.assert_allclose(panel.excess_return, panel.value_weighted_return - cash)
    np.testing.assert_allclose(panel.HML, 0.03)


@pytest.mark.parametrize("lag", [0, 3, 6, 12])
def test_ols_hac_against_explicit_bartlett_sandwich(lag: int) -> None:
    i = np.arange(48, dtype=float)
    x = np.sin(i / 3) * 0.03
    y = 0.004 + 0.7 * x + np.cos(i / 5) * 0.002
    frame = pd.DataFrame({"y": y, "x": x})
    observed = fit_regression(frame, "y", ("x",), covariance="HAC", hac_lags=lag)
    design = np.column_stack([np.ones(len(i)), x])
    beta = np.linalg.lstsq(design, y, rcond=None)[0]
    errors = y - design @ beta
    scores = design * errors[:, None]
    meat = scores.T @ scores
    for j in range(1, lag + 1):
        gamma = scores[j:].T @ scores[:-j]
        meat += (1 - j / (lag + 1)) * (gamma + gamma.T)
    bread = np.linalg.inv(design.T @ design)
    covariance = bread @ meat @ bread * len(i) / (len(i) - 2)
    se = np.sqrt(np.diag(covariance))
    p = 2 * student_t.sf(np.abs(beta / se), len(i) - 2)
    np.testing.assert_allclose(observed.coefficients.estimate, beta, atol=1e-14)
    np.testing.assert_allclose(observed.coefficients.standard_error, se, atol=1e-14)
    np.testing.assert_allclose(observed.coefficients.p_value, p, atol=1e-12)
    r2 = 1 - errors @ errors / np.sum((y - y.mean()) ** 2)
    assert observed.metrics["adjusted_r_squared"] == pytest.approx(
        1 - (1 - r2) * (len(i) - 1) / (len(i) - 2)
    )


@pytest.mark.parametrize(
    "fault", ["missing", "nan", "infinite", "impossible", "conflict", "excess", "empty", "reversed"]
)
def test_holding_factor_compounding_rejects_invalid_evidence(fault: str) -> None:
    day = pd.Timestamp("2020-02-04")
    factors = pd.DataFrame(
        {
            "date": [day] * 3,
            "factor_id": ["market_return", "risk_free_rate", "excess_return"],
            "raw_value": [0.02, 0.001, 0.019],
        }
    )
    periods = pd.DataFrame({"formation_date": [pd.Timestamp("2020-01-31")], "date": [day]})
    if fault == "missing":
        factors = factors.loc[factors.factor_id.ne("market_return")]
    elif fault in {"nan", "infinite", "impossible"}:
        factors.loc[0, "raw_value"] = {"nan": np.nan, "infinite": np.inf, "impossible": -1.0}[fault]
    elif fault == "conflict":
        factors = pd.concat([factors, factors.iloc[[0]].assign(raw_value=0.03)])
    elif fault == "excess":
        factors.loc[2, "raw_value"] = 0.9
    elif fault == "empty":
        periods.loc[0, "formation_date"] = pd.Timestamp("2020-02-05")
        periods.loc[0, "date"] = pd.Timestamp("2020-02-06")
    else:
        periods.loc[0, "formation_date"] = day
    with pytest.raises((DataQualityError, TemporalIntegrityError)):
        _holding_period_market_factors(factors, periods)
