"""Focused financial failures found in actual Phase 3 dependency traces."""

import numpy as np
import pandas as pd
import pytest

from institutional_factor_platform.ml.evaluation import block_bootstrap_ic
from institutional_factor_platform.ml.features import monthly_decision_features
from institutional_factor_platform.ml.targets import build_targets
from institutional_factor_platform.portfolio.service import _risk_free_series


def test_portfolio_cash_matches_full_holding_interval() -> None:
    dates = pd.to_datetime(["2024-01-02", "2024-01-03", "2024-01-04"])
    frame = pd.DataFrame(
        {"date": dates, "factor_id": "risk_free_rate", "raw_value": [0.01, 0.02, 0.03]}
    )
    periods = pd.DataFrame({"formation_date": [pd.Timestamp("2024-01-01")], "date": [dates[1]]})
    value = _risk_free_series(frame, pd.DatetimeIndex([dates[1]]), periods)
    assert value.iloc[0] == pytest.approx(1.01 * 1.02 - 1)


def test_one_common_month_end_not_one_last_observation_per_security() -> None:
    dates = pd.to_datetime(["2024-01-30", "2024-01-31", "2024-01-30"], utc=True)
    frame = pd.DataFrame(
        {
            "security_id": ["a", "a", "b"],
            "formation_date": dates,
            "decision_time": dates + pd.Timedelta(hours=23),
            "feature_available_at": dates,
        }
    )
    result = monthly_decision_features(frame)
    assert result.security_id.tolist() == ["a"]
    assert result.formation_date.nunique() == 1


def test_target_horizon_counts_common_sessions_not_security_observations() -> None:
    days = pd.date_range("2024-01-01", periods=5, freq="B", tz="UTC")
    rows = [
        dict(
            security_id=sid,
            date=d,
            available_at=d + pd.Timedelta(hours=23),
            **{"return": 0.01, "benchmark_return": 0.002},
        )
        for sid in ["a", "b"]
        for d in days
        if not (sid == "a" and d == days[1])
    ]
    targets, _ = build_targets(
        pd.DataFrame(rows), kind="future_excess_return", horizon=2, benchmark_id="m"
    )
    assert targets.loc[targets.security_id.eq("a") & targets.formation_date.eq(days[0])].empty
    first = targets.loc[targets.security_id.eq("b") & targets.formation_date.eq(days[0])].iloc[0]
    assert first.target_end == days[2]
    assert first.target == pytest.approx(1.01**2 - 1.002**2)


def test_bootstrap_interval_targets_mean_date_ic_not_pooled_rank_correlation() -> None:
    frame = pd.DataFrame(
        {
            "formation_date": [0] * 3 + [1] * 3,
            "prediction": [0.0, 1.0, 2.0, 10.0, 11.0, 12.0],
            "target": [10.0, 11.0, 12.0, 0.0, 1.0, 2.0],
        }
    )
    value = block_bootstrap_ic(frame, block_length=1, resamples=20, seed=17)
    assert value["estimate"] == pytest.approx(1.0)
    assert value["lower"] == pytest.approx(1.0)
    assert value["upper"] == pytest.approx(1.0)


def test_bootstrap_constant_prediction_is_not_zero_ic() -> None:
    frame = pd.DataFrame(
        {"formation_date": [0] * 4, "prediction": np.zeros(4), "target": np.arange(4.0)}
    )
    assert block_bootstrap_ic(frame, block_length=1, resamples=10, seed=17) == {
        "estimate": None,
        "lower": None,
        "upper": None,
    }
