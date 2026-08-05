"""Explicit modular transaction-cost accounting."""

from dataclasses import dataclass

import numpy as np

from institutional_factor_platform.exceptions import DataQualityError


@dataclass(frozen=True, slots=True)
class TransactionCostModel:
    commission_bps: float
    spread_bps: float
    slippage_bps: float
    market_impact_coefficient: float

    def __post_init__(self) -> None:
        if any(
            value < 0 or not np.isfinite(value)
            for value in (
                self.commission_bps,
                self.spread_bps,
                self.slippage_bps,
                self.market_impact_coefficient,
            )
        ):
            raise DataQualityError("Transaction-cost parameters must be finite and nonnegative")

    def estimate(self, trades: np.ndarray, liquidity: np.ndarray | None = None) -> dict[str, float]:
        turnover = float(np.abs(trades).sum())
        commission = turnover * self.commission_bps / 10_000.0
        spread = turnover * self.spread_bps / 20_000.0
        slippage = turnover * self.slippage_bps / 10_000.0
        if liquidity is None:
            if self.market_impact_coefficient != 0:
                raise DataQualityError("Nonzero market impact requires explicit liquidity")
            impact = 0.0
        else:
            if liquidity.shape != trades.shape or (liquidity <= 0).any():
                raise DataQualityError("Liquidity must be positive and trade-aligned")
            impact = float(
                self.market_impact_coefficient
                * np.sum((np.abs(trades) ** 1.5) / np.sqrt(liquidity))
            )
        return {
            "turnover": turnover,
            "commission": commission,
            "spread": spread,
            "slippage": slippage,
            "market_impact": impact,
            "total_cost": commission + spread + slippage + impact,
        }
