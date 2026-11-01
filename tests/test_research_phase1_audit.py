"""Independent Phase 1 arithmetic and missing-holding-evidence regressions."""

from datetime import UTC, date, datetime
from math import prod

import numpy as np
import pandas as pd
import pytest

from institutional_factor_platform.backtest.costs import TransactionCostModel
from institutional_factor_platform.backtest.engine import run_backtest
from institutional_factor_platform.exceptions import DataQualityError
from institutional_factor_platform.factors.config import load_factor_config
from institutional_factor_platform.factors.definitions import (
    FACTOR_DEFINITIONS,
    compute_characteristics,
)
from institutional_factor_platform.factors.portfolio import compute_factor_portfolios
from institutional_factor_platform.factors.preprocessing import preprocess_characteristics
from institutional_factor_platform.risk.metrics import drawdown, maximum_drawdown


@pytest.mark.parametrize(
    "returns",
    [
        [-0.2, 0.1],
        [-0.1, -0.1, -0.1],
        [-0.2, 0.25, -0.1],
        [0.02, 0.02],
        [-0.02, -0.02],
        [0.0, 0.0],
        [0.1, -0.2, 0.3],
    ],
)
def test_drawdown_from_initial_nav(returns: list[float]) -> None:
    wealth, peak = 1.0, 1.0
    reference = []
    for value in returns:
        wealth *= 1 + value
        peak = max(peak, wealth)
        reference.append(wealth / peak - 1)
    series = pd.Series(returns, index=pd.date_range("2020-01-01", periods=len(returns)))
    np.testing.assert_allclose(drawdown(series), reference, atol=1e-14)
    assert drawdown(series).index.equals(series.index)
    assert maximum_drawdown(series) == pytest.approx(min(reference))


@pytest.mark.parametrize("rate", [5.0, 10.0, 20.0])
@pytest.mark.parametrize("trades", [[1.0, 0.0], [-1.0, 0.0], [-1.0, 1.0], [-0.1, 0.1]])
def test_per_side_fee_identity(rate: float, trades: list[float]) -> None:
    model = TransactionCostModel(0, rate, rate / 2, 0)
    result = model.estimate(np.array(trades))
    expected = sum(abs(trade) * rate / 10000 for trade in trades)
    assert result["total_cost"] == pytest.approx(expected)
    assert sum(model.estimate(np.array([trade]))["total_cost"] for trade in trades) == (
        pytest.approx(expected)
    )
    assert result["spread"] == pytest.approx(expected / 2)
    assert result["slippage"] == pytest.approx(expected / 2)


def test_backtest_trade_ledger_includes_deployment_and_drift() -> None:
    returns = pd.DataFrame({"A": [0.0, 0.0, 0.1, 0.0], "B": [0.0, 0.0, 0.0, 0.0]})
    result = run_backtest(
        returns,
        pd.Series(0.0, index=returns.index),
        lambda history, current: np.array([0.5, 0.5]),
        TransactionCostModel(0, 10, 5, 0),
        window=2,
    )
    # Deployment L1=1; then drift to 11/21,10/21, rebalance L1=1/21.
    expected_costs = [0.001, 0.001 / 21]
    np.testing.assert_allclose(result.returns["transaction_cost"], expected_costs)
    np.testing.assert_allclose(result.returns["net_return"], [0.049, -0.001 / 21])
    ledger = result.transactions.groupby("date")["total_cost"].sum()
    np.testing.assert_allclose(ledger, expected_costs)
    assert prod(1 + value for value in result.returns["net_return"]) == pytest.approx(
        1.049 * (1 - 0.001 / 21)
    )


@pytest.mark.parametrize("missing", ["first", "last", "all", "null"])
def test_factor_portfolio_rejects_incomplete_formed_holding(missing: str) -> None:
    formation = date(2020, 1, 31)
    factors = pd.DataFrame(
        [
            {"security_id": s, "date": formation, "factor_id": "book_to_market", "score_value": i}
            for i, s in enumerate(["A", "B", "C"])
        ]
    )
    characteristics = factors[["security_id", "date"]].assign(market_cap=100.0)
    rows = []
    for day in [date(2020, 2, 3), date(2020, 2, 4)]:
        for security in ["A", "B", "C"]:
            if security == "C" and (
                missing == "all"
                or (missing == "first" and day.day == 3)
                or (missing == "last" and day.day == 4)
            ):
                continue
            rows.append(
                {
                    "security_id": security,
                    "date": day,
                    "return": np.nan if missing == "null" and security == "C" else 0.01,
                    "benchmark_return": 0.01,
                    "available_at": datetime.combine(day, datetime.min.time(), tzinfo=UTC),
                }
            )
    with pytest.raises(DataQualityError, match="Incomplete holding-period"):
        compute_factor_portfolios(factors, characteristics, pd.DataFrame(rows))


def test_factor_formula_references_and_beta_aliases() -> None:
    dates = pd.bdate_range("2020-01-01", periods=280)
    rows = []
    for security in ["A", "B"]:
        for i, day in enumerate(dates):
            rows.append(
                {
                    "security_id": security,
                    "date": day.date(),
                    "available_at": day.tz_localize("UTC"),
                    "sector": "sample",
                    "industry": "sample",
                    "exchange": "XNYS",
                    "return": 0.001 + (i % 7 - 3) * 0.002,
                    "market_return": (i % 5 - 2) * 0.001,
                    "risk_free": 0.0001,
                    "benchmark_return": 0.001,
                    "price": 10.0,
                    "high": 11.0,
                    "low": 9.0,
                    "volume": 100.0,
                    "shares_outstanding": 1000.0,
                    "total_debt": 30.0,
                    "total_assets": 100.0,
                }
            )
    panel = pd.DataFrame(rows)
    result = compute_characteristics(panel, load_factor_config())
    a = result.loc[result["security_id"].eq("A")]
    observed_returns = panel.loc[panel["security_id"].eq("A"), "return"].tolist()
    assert a.iloc[-1]["momentum_12_1m"] == pytest.approx(
        prod(1 + value for value in observed_returns[-252:-21]) - 1
    )
    assert a.iloc[-1]["leverage"] == pytest.approx(0.3)
    assert a.iloc[-1]["turnover"] == pytest.approx(0.1)
    assert a.iloc[-1]["average_dollar_volume"] == pytest.approx(1000.0)
    assert a.iloc[-1]["amihud_illiquidity"] == pytest.approx(abs(observed_returns[-1]) / 1000)
    assert a.iloc[-1]["bid_ask_proxy"] == pytest.approx(0.2)
    assert result["equity_issuance"].isna().all()
    assert len(FACTOR_DEFINITIONS) == len({d.factor_id for d in FACTOR_DEFINITIONS}) == 48
    # Stable registry identities do not imply independent economic exposures.
    pd.testing.assert_series_equal(result["beta"], result["rolling_beta"], check_names=False)
    pd.testing.assert_series_equal(result["beta"], result["rolling_market_beta"], check_names=False)


@pytest.mark.parametrize("count", [1, 2, 3, 4])
def test_sparse_cross_sections_follow_declared_threshold(count: int) -> None:
    characteristics = pd.DataFrame(
        {
            "security_id": [str(i) for i in range(count)],
            "date": date(2020, 1, 31),
            "available_at": datetime(2020, 1, 31, tzinfo=UTC),
            "book_to_market": [float(i) for i in range(count)],
        }
    )
    result = preprocess_characteristics(
        characteristics,
        ("book_to_market",),
        load_factor_config().preprocessing,
    )
    assert result["score_value"].notna().sum() == (count if count >= 3 else 0)
