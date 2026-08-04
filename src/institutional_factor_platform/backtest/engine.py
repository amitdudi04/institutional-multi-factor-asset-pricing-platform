"""Calendar-ordered rolling/expanding rebalance and accounting infrastructure."""

from collections.abc import Callable
from dataclasses import dataclass
from typing import Literal

import numpy as np
import pandas as pd

from institutional_factor_platform.backtest.costs import TransactionCostModel
from institutional_factor_platform.exceptions import DataQualityError, TemporalIntegrityError


@dataclass(frozen=True, slots=True)
class BacktestResult:
    returns: pd.DataFrame
    allocations: pd.DataFrame
    transactions: pd.DataFrame


def run_backtest(
    returns: pd.DataFrame,
    benchmark: pd.Series,
    allocator: Callable[[pd.DataFrame, np.ndarray], np.ndarray],
    costs: TransactionCostModel,
    *,
    window: int,
    mode: Literal["rolling", "expanding"] = "rolling",
    rebalance_every: int = 1,
) -> BacktestResult:
    if not returns.index.is_monotonic_increasing or returns.index.has_duplicates:
        raise TemporalIntegrityError("Backtest dates must be unique and increasing")
    if (
        not returns.index.equals(benchmark.index)
        or returns.isna().any().any()
        or benchmark.isna().any()
    ):
        raise DataQualityError("Backtest and benchmark must be complete and exactly aligned")
    if window < 2 or rebalance_every < 1 or len(returns) <= window:
        raise DataQualityError("Backtest window or rebalance schedule is invalid")
    assets = tuple(str(value) for value in returns.columns)
    current = np.zeros(len(assets))
    result_rows: list[dict[str, object]] = []
    allocation_rows: list[dict[str, object]] = []
    transaction_rows: list[dict[str, object]] = []
    for position in range(window, len(returns)):
        current_date = returns.index[position]
        cost = 0.0
        if (position - window) % rebalance_every == 0:
            start = 0 if mode == "expanding" else position - window
            history = returns.iloc[start:position]
            target = np.asarray(allocator(history.copy(), current.copy()), dtype=float)
            if (
                target.shape != current.shape
                or not np.isfinite(target).all()
                or abs(target.sum() - 1) > 1e-7
            ):
                raise DataQualityError("Allocator returned invalid weights")
            trade = target - current
            cost_values = costs.estimate(trade)
            cost = cost_values["total_cost"]
            for index, asset in enumerate(assets):
                allocation_rows.append(
                    {"date": current_date, "asset_id": asset, "weight": target[index]}
                )
                if abs(trade[index]) > 0:
                    asset_cost = costs.estimate(np.array([trade[index]]))
                    transaction_rows.append(
                        {
                            "date": current_date,
                            "asset_id": asset,
                            "trade_weight": trade[index],
                            **asset_cost,
                        }
                    )
            current = target
        gross = float(current @ returns.iloc[position].to_numpy(dtype=float))
        net = gross - cost
        result_rows.append(
            {
                "date": current_date,
                "gross_return": gross,
                "transaction_cost": cost,
                "net_return": net,
                "benchmark_return": float(benchmark.iloc[position]),
                "active_return": net - float(benchmark.iloc[position]),
            }
        )
        growth = 1.0 + returns.iloc[position].to_numpy(dtype=float)
        current = current * growth / (1.0 + gross)
    return BacktestResult(
        pd.DataFrame(result_rows), pd.DataFrame(allocation_rows), pd.DataFrame(transaction_rows)
    )
