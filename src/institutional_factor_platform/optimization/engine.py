"""Fail-closed constrained portfolio optimization methods."""

from dataclasses import dataclass
from typing import Literal

import numpy as np
from scipy.optimize import OptimizeResult, linprog, minimize

from institutional_factor_platform.constraints.models import ConstraintSet
from institutional_factor_platform.exceptions import DataQualityError
from institutional_factor_platform.optimization.covariance import validate_covariance
from institutional_factor_platform.optimization.hrp import hierarchical_risk_parity
from institutional_factor_platform.portfolio.allocations import equal_weight

Method = Literal[
    "minimum_variance",
    "mean_variance",
    "maximum_sharpe",
    "maximum_diversification",
    "risk_parity",
    "hrp",
    "cvar",
]


@dataclass(frozen=True, slots=True)
class OptimizationResult:
    method: str
    weights: np.ndarray
    objective_value: float
    expected_return: float
    volatility: float
    converged: bool
    iterations: int
    diagnostics: dict[str, float]


def optimize(
    method: Method,
    expected_returns: np.ndarray,
    covariance: np.ndarray,
    constraints: ConstraintSet,
    *,
    asset_ids: tuple[str, ...] | None = None,
    previous_weights: np.ndarray | None = None,
    risk_free: float = 0.0,
    risk_aversion: float = 1.0,
    scenarios: np.ndarray | None = None,
    cvar_confidence: float = 0.95,
    sectors: tuple[str, ...] | None = None,
    exposures: dict[str, np.ndarray] | None = None,
    transaction_cost_rate: float | None = None,
) -> OptimizationResult:
    mean = np.asarray(expected_returns, dtype=float)
    matrix = np.asarray(covariance, dtype=float)
    validate_covariance(matrix)
    n = len(mean)
    if mean.shape != (matrix.shape[0],) or not np.isfinite(mean).all():
        raise DataQualityError("Expected returns and covariance dimensions differ")
    constraints.validate(n)
    ids = asset_ids or tuple(str(index) for index in range(n))
    if len(ids) != n:
        raise DataQualityError("Asset identifiers must align with expected returns")
    if method == "hrp":
        weights = hierarchical_risk_parity(matrix)
        return _result(
            method,
            weights,
            mean,
            matrix,
            0.0,
            True,
            0,
            constraints,
            ids,
            previous_weights,
            sectors,
            exposures,
        )
    if method == "cvar":
        if scenarios is None:
            raise DataQualityError("CVaR optimization requires explicit return scenarios")
        weights, objective, iterations = _cvar(
            np.asarray(scenarios, dtype=float), constraints, cvar_confidence
        )
        return _result(
            method,
            weights,
            mean,
            matrix,
            objective,
            True,
            iterations,
            constraints,
            ids,
            previous_weights,
            sectors,
            exposures,
        )
    if method == "maximum_sharpe" and _supports_tangency_transform(constraints, sectors, exposures):
        transformed = _maximum_sharpe_long_only(mean, matrix, risk_free)
        if transformed is not None:
            weights, iterations = transformed
            variance = float(weights @ matrix @ weights)
            objective = -float((mean @ weights - risk_free) / np.sqrt(variance))
            output = _result(
                method,
                weights,
                mean,
                matrix,
                objective,
                True,
                iterations,
                constraints,
                ids,
                previous_weights,
                sectors,
                exposures,
            )
            output.diagnostics["tangency_transform"] = 1.0
            return output
    start = previous_weights.copy() if previous_weights is not None else equal_weight(n)
    functions = {
        "minimum_variance": lambda w: float(w @ matrix @ w),
        "mean_variance": lambda w: float(risk_aversion * w @ matrix @ w - mean @ w),
        "maximum_sharpe": lambda w: -float((mean @ w - risk_free) / np.sqrt(w @ matrix @ w)),
        "maximum_diversification": lambda w: (
            -float((w @ np.sqrt(np.diag(matrix))) / np.sqrt(w @ matrix @ w))
        ),
        "risk_parity": lambda w: _risk_parity_objective(w, matrix),
    }
    if method not in functions:
        raise DataQualityError(f"Unsupported optimizer: {method}")
    scipy_constraints: list[dict[str, object]] = [
        {"type": "eq", "fun": lambda w: float(w.sum() - 1.0)}
    ]
    if constraints.turnover_limit is not None and previous_weights is not None:
        scipy_constraints.append(
            {
                "type": "ineq",
                "fun": lambda w: float(
                    constraints.turnover_limit - np.abs(w - previous_weights).sum()
                ),
            }
        )
    if sectors is not None:
        if len(sectors) != n:
            raise DataQualityError("Sector labels must align with assets")
        sector_array = np.asarray(sectors)
        for sector, limit in constraints.sector_limits.items():
            mask = sector_array == sector
            scipy_constraints.append(
                {
                    "type": "ineq",
                    "fun": lambda w, mask=mask, limit=limit: float(limit - w[mask].sum()),
                }
            )
    for name, vector in (exposures or {}).items():
        if vector.shape != (n,) or not np.isfinite(vector).all():
            raise DataQualityError(f"Exposure vector is invalid: {name}")
        if name in constraints.exposure_limits:
            low, high = constraints.exposure_limits[name]
            scipy_constraints.extend(
                [
                    {
                        "type": "ineq",
                        "fun": lambda w, vector=vector, low=low: float(w @ vector - low),
                    },
                    {
                        "type": "ineq",
                        "fun": lambda w, vector=vector, high=high: float(high - w @ vector),
                    },
                ]
            )
    if constraints.transaction_cost_limit is not None:
        if previous_weights is None or transaction_cost_rate is None or transaction_cost_rate < 0:
            raise DataQualityError(
                "Transaction-cost constraints require previous weights and an explicit cost rate"
            )
        scipy_constraints.append(
            {
                "type": "ineq",
                "fun": lambda w: float(
                    constraints.transaction_cost_limit
                    - np.abs(w - previous_weights).sum() * transaction_cost_rate
                ),
            }
        )
    upper = constraints.maximum_weight or 1.0
    bounds: list[tuple[float, float]] = []
    for index, asset_id in enumerate(ids):
        low, high = constraints.minimum_weight, upper
        if previous_weights is not None and asset_id in constraints.liquidity_trade_limits:
            trade_limit = constraints.liquidity_trade_limits[asset_id]
            low = max(low, float(previous_weights[index] - trade_limit))
            high = min(high, float(previous_weights[index] + trade_limit))
        bounds.append((low, high))

    def solve(initial: np.ndarray) -> OptimizeResult:
        return minimize(
            functions[method],
            initial,
            method="SLSQP",
            bounds=bounds,
            constraints=scipy_constraints,
            options={"ftol": 1e-12, "maxiter": 2000},
        )

    result = solve(start)
    deterministic_retry = False
    if (not result.success or not np.isfinite(result.fun)) and previous_weights is not None:
        result = solve(equal_weight(n))
        deterministic_retry = True
    if not result.success or not np.isfinite(result.fun):
        boundary_results = [solve(candidate) for candidate in np.eye(n, dtype=float)]
        converged = [
            candidate
            for candidate in boundary_results
            if candidate.success and np.isfinite(candidate.fun)
        ]
        if converged:
            result = min(converged, key=lambda candidate: float(candidate.fun))
            deterministic_retry = True
    if not result.success or not np.isfinite(result.fun):
        raise DataQualityError(f"Optimizer failed to converge: {result.message}")
    weights = np.asarray(result.x, dtype=float)
    output = _result(
        method,
        weights,
        mean,
        matrix,
        float(result.fun),
        True,
        int(result.nit),
        constraints,
        ids,
        previous_weights,
        sectors,
        exposures,
    )
    output.diagnostics["deterministic_retry"] = float(deterministic_retry)
    return output


def _risk_parity_objective(weights: np.ndarray, covariance: np.ndarray) -> float:
    variance = float(weights @ covariance @ weights)
    contributions = weights * (covariance @ weights) / variance
    return float(((contributions - 1.0 / len(weights)) ** 2).sum())


def _supports_tangency_transform(
    constraints: ConstraintSet,
    sectors: tuple[str, ...] | None,
    exposures: dict[str, np.ndarray] | None,
) -> bool:
    return (
        constraints.long_only
        and constraints.minimum_weight == 0
        and constraints.maximum_weight is None
        and constraints.turnover_limit is None
        and constraints.transaction_cost_limit is None
        and not constraints.sector_limits
        and not constraints.exposure_limits
        and not constraints.liquidity_trade_limits
        and sectors is None
        and not exposures
    )


def _maximum_sharpe_long_only(
    expected_returns: np.ndarray, covariance: np.ndarray, risk_free: float
) -> tuple[np.ndarray, int] | None:
    excess = expected_returns - risk_free
    if float(excess.max()) <= 0:
        return None
    initial = equal_weight(len(excess))
    initial_excess = float(excess @ initial)
    if initial_excess <= 0:
        initial = np.zeros(len(excess), dtype=float)
        initial[int(np.argmax(excess))] = 1.0
        initial_excess = float(excess @ initial)
    initial /= initial_excess
    scale = max(float(np.diag(covariance).max()), np.finfo(float).eps)
    result = minimize(
        lambda value: float(value @ (covariance / scale) @ value),
        initial,
        method="SLSQP",
        bounds=[(0.0, None)] * len(excess),
        constraints=[{"type": "eq", "fun": lambda value: float(excess @ value - 1.0)}],
        options={"ftol": 1e-12, "maxiter": 2000},
    )
    if not result.success or not np.isfinite(result.fun) or float(result.x.sum()) <= 0:
        return None
    weights = np.asarray(result.x, dtype=float)
    weights /= weights.sum()
    return weights, int(result.nit)


def _cvar(
    scenarios: np.ndarray, constraints: ConstraintSet, confidence: float
) -> tuple[np.ndarray, float, int]:
    if (
        scenarios.ndim != 2
        or len(scenarios) < 3
        or not np.isfinite(scenarios).all()
        or not 0 < confidence < 1
    ):
        raise DataQualityError("CVaR scenarios or confidence are invalid")
    observations, assets = scenarios.shape
    variables = assets + 1 + observations
    objective = np.zeros(variables)
    objective[assets] = 1.0
    objective[assets + 1 :] = 1.0 / ((1.0 - confidence) * observations)
    a_ub = np.zeros((observations, variables))
    a_ub[:, :assets] = -scenarios
    a_ub[:, assets] = -1.0
    a_ub[:, assets + 1 :] = -np.eye(observations)
    a_eq = np.zeros((1, variables))
    a_eq[0, :assets] = 1.0
    upper = constraints.maximum_weight or 1.0
    bounds = (
        [(constraints.minimum_weight, upper)] * assets
        + [(None, None)]
        + [(0.0, None)] * observations
    )
    solved = linprog(
        objective,
        A_ub=a_ub,
        b_ub=np.zeros(observations),
        A_eq=a_eq,
        b_eq=np.array([1.0]),
        bounds=bounds,
        method="highs",
    )
    if not solved.success:
        raise DataQualityError(f"CVaR optimizer failed: {solved.message}")
    return np.asarray(solved.x[:assets]), float(solved.fun), int(solved.nit)


def _result(
    method: str,
    weights: np.ndarray,
    mean: np.ndarray,
    covariance: np.ndarray,
    objective: float,
    converged: bool,
    iterations: int,
    constraints: ConstraintSet,
    ids: tuple[str, ...],
    previous: np.ndarray | None,
    sectors: tuple[str, ...] | None,
    exposures: dict[str, np.ndarray] | None,
) -> OptimizationResult:
    checks = constraints.verify(
        weights, ids, previous=previous, sectors=sectors, exposures=exposures
    )
    volatility = float(np.sqrt(weights @ covariance @ weights))
    checks.update(
        {
            "weight_sum_error": abs(float(weights.sum()) - 1.0),
            "minimum_weight": float(weights.min()),
            "maximum_weight": float(weights.max()),
        }
    )
    return OptimizationResult(
        method, weights, objective, float(mean @ weights), volatility, converged, iterations, checks
    )
