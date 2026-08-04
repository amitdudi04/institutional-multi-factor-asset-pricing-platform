"""Explicit instantaneous shock propagation with unmapped-exposure disclosure."""

from dataclasses import dataclass

import numpy as np

from institutional_factor_platform.exceptions import DataQualityError


@dataclass(frozen=True, slots=True)
class Scenario:
    name: str
    shocks: dict[str, float]
    kind: str = "custom"

    def __post_init__(self) -> None:
        allowed = {
            "market_crash",
            "interest_rate",
            "volatility",
            "inflation",
            "liquidity",
            "custom",
        }
        if (
            self.kind not in allowed
            or not self.name
            or not self.shocks
            or not all(np.isfinite(value) for value in self.shocks.values())
        ):
            raise DataQualityError("Scenario definition is invalid")


def apply_scenario(
    scenario: Scenario, weights: np.ndarray, exposures: dict[str, np.ndarray]
) -> dict[str, object]:
    mapped: dict[str, float] = {}
    unmapped: list[str] = []
    total = 0.0
    for factor, shock in scenario.shocks.items():
        vector = exposures.get(factor)
        if vector is None:
            unmapped.append(factor)
            continue
        if vector.shape != weights.shape or not np.isfinite(vector).all():
            raise DataQualityError(f"Scenario exposure is invalid: {factor}")
        contribution = float(weights @ vector * shock)
        mapped[factor] = contribution
        total += contribution
    return {
        "scenario": scenario.name,
        "kind": scenario.kind,
        "portfolio_impact": total,
        "contributions": mapped,
        "unmapped_shocks": sorted(unmapped),
        "is_forecast": False,
    }
