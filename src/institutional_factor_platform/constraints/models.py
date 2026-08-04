"""Validated portfolio constraint definitions and feasibility checks."""

from dataclasses import dataclass, field

import numpy as np

from institutional_factor_platform.exceptions import DataQualityError


@dataclass(frozen=True, slots=True)
class ConstraintSet:
    long_only: bool = True
    leverage_limit: float = 1.0
    minimum_weight: float = 0.0
    maximum_weight: float | None = None
    turnover_limit: float | None = None
    transaction_cost_limit: float | None = None
    sector_limits: dict[str, float] = field(default_factory=dict)
    exposure_limits: dict[str, tuple[float, float]] = field(default_factory=dict)
    liquidity_trade_limits: dict[str, float] = field(default_factory=dict)

    def validate(self, asset_count: int) -> None:
        if not self.long_only or self.leverage_limit != 1.0 or self.minimum_weight < 0:
            raise DataQualityError("Approved Phase 4 baseline is strictly long-only and unlevered")
        if self.maximum_weight is not None and not 0 < self.maximum_weight <= 1:
            raise DataQualityError("Maximum weight must be in (0, 1]")
        upper = self.maximum_weight or 1.0
        if asset_count * self.minimum_weight > 1 + 1e-12 or asset_count * upper < 1 - 1e-12:
            raise DataQualityError("Portfolio bounds are infeasible")
        if self.turnover_limit is not None and not 0 <= self.turnover_limit <= 2:
            raise DataQualityError("Turnover limit must be in [0, 2]")
        if self.transaction_cost_limit is not None and self.transaction_cost_limit < 0:
            raise DataQualityError("Transaction-cost limit cannot be negative")
        if any(not 0 <= value <= 1 for value in self.sector_limits.values()):
            raise DataQualityError("Sector limits must be in [0, 1]")
        if any(low > high for low, high in self.exposure_limits.values()):
            raise DataQualityError("Exposure lower bounds cannot exceed upper bounds")
        if any(value < 0 for value in self.liquidity_trade_limits.values()):
            raise DataQualityError("Liquidity trade limits cannot be negative")

    def verify(
        self,
        weights: np.ndarray,
        asset_ids: tuple[str, ...],
        *,
        previous: np.ndarray | None = None,
        sectors: tuple[str, ...] | None = None,
        exposures: dict[str, np.ndarray] | None = None,
        tolerance: float = 1e-7,
    ) -> dict[str, float]:
        self.validate(len(weights))
        if len(asset_ids) != len(weights) or not np.isfinite(weights).all():
            raise DataQualityError("Portfolio weights are non-finite or misaligned")
        if (
            abs(float(weights.sum()) - 1) > tolerance
            or (weights < self.minimum_weight - tolerance).any()
        ):
            raise DataQualityError("Portfolio weights violate budget or lower bounds")
        if self.maximum_weight is not None and (weights > self.maximum_weight + tolerance).any():
            raise DataQualityError("Portfolio weights violate maximum position size")
        gross = float(np.abs(weights).sum())
        if gross > self.leverage_limit + tolerance:
            raise DataQualityError("Portfolio weights violate leverage limit")
        turnover = 0.0 if previous is None else float(np.abs(weights - previous).sum())
        if self.turnover_limit is not None and turnover > self.turnover_limit + tolerance:
            raise DataQualityError("Portfolio weights violate turnover limit")
        if previous is not None:
            for index, asset_id in enumerate(asset_ids):
                limit = self.liquidity_trade_limits.get(asset_id)
                if (
                    limit is not None
                    and abs(float(weights[index] - previous[index])) > limit + tolerance
                ):
                    raise DataQualityError(f"Liquidity trade limit violated: {asset_id}")
        if sectors is not None:
            for sector, limit in self.sector_limits.items():
                actual = float(weights[np.asarray(sectors) == sector].sum())
                if actual > limit + tolerance:
                    raise DataQualityError(f"Sector limit violated: {sector}")
        for name, vector in (exposures or {}).items():
            if name in self.exposure_limits:
                actual = float(weights @ vector)
                low, high = self.exposure_limits[name]
                if actual < low - tolerance or actual > high + tolerance:
                    raise DataQualityError(f"Exposure limit violated: {name}")
        return {"net_exposure": float(weights.sum()), "gross_exposure": gross, "turnover": turnover}
