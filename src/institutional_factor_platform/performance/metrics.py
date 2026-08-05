"""Reconciled gross/net/benchmark performance analytics."""

import numpy as np
import pandas as pd

from institutional_factor_platform.exceptions import DataQualityError
from institutional_factor_platform.risk.metrics import risk_summary


def performance_summary(
    backtest: pd.DataFrame, *, risk_free: float | pd.Series = 0.0, annualization: int = 12
) -> dict[str, object]:
    required = {
        "gross_return",
        "net_return",
        "transaction_cost",
        "benchmark_return",
        "active_return",
    }
    if required - set(backtest) or len(backtest) < 3:
        raise DataQualityError("Performance summary requires a complete backtest contract")
    if not np.allclose(
        backtest["gross_return"] - backtest["transaction_cost"],
        backtest["net_return"],
        atol=1e-12,
    ):
        raise DataQualityError("Gross return minus costs does not reconcile to net return")
    if not np.allclose(
        backtest["net_return"] - backtest["benchmark_return"],
        backtest["active_return"],
        atol=1e-12,
    ):
        raise DataQualityError("Active return does not reconcile to benchmark")
    return {
        "gross_cumulative_return": float(np.prod(1 + backtest["gross_return"]) - 1),
        "net_cumulative_return": float(np.prod(1 + backtest["net_return"]) - 1),
        "benchmark_cumulative_return": float(np.prod(1 + backtest["benchmark_return"]) - 1),
        "total_transaction_cost": float(backtest["transaction_cost"].sum()),
        "risk": risk_summary(
            backtest["net_return"],
            backtest["benchmark_return"],
            risk_free,
            annualization,
        ),
    }
