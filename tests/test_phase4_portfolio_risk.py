"""Phase 4 optimization, risk, accounting, temporal, and evidence tests."""

from datetime import date, timedelta
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pandas as pd
import pyarrow as pa
import pytest
from pydantic import ValidationError

from institutional_factor_platform.backtest.costs import TransactionCostModel
from institutional_factor_platform.backtest.engine import run_backtest
from institutional_factor_platform.constraints.models import ConstraintSet
from institutional_factor_platform.exceptions import (
    ConfigurationError,
    DataQualityError,
    EvidenceIntegrityError,
    TemporalIntegrityError,
)
from institutional_factor_platform.optimization.black_litterman import (
    bayesian_mean,
    black_litterman_posterior,
)
from institutional_factor_platform.optimization.covariance import (
    estimate_covariance,
    regularize_covariance,
    validate_covariance,
)
from institutional_factor_platform.optimization.engine import optimize
from institutional_factor_platform.optimization.hrp import hierarchical_risk_parity
from institutional_factor_platform.performance.metrics import performance_summary
from institutional_factor_platform.portfolio import service as service_module
from institutional_factor_platform.portfolio.allocations import equal_weight, market_cap_weight
from institutional_factor_platform.portfolio.config import PortfolioConfig, load_portfolio_config
from institutional_factor_platform.portfolio.service import PortfolioResearchService
from institutional_factor_platform.research_outputs.portfolio_storage import PortfolioRepository
from institutional_factor_platform.risk.metrics import (
    beta_alpha,
    diversification_ratio,
    drawdown,
    expected_shortfall,
    maximum_drawdown,
    risk_contributions,
    risk_summary,
    rolling_beta,
    rolling_volatility,
    value_at_risk,
    volatility,
)
from institutional_factor_platform.scenarios.engine import Scenario, apply_scenario


def _returns(rows: int = 80) -> pd.DataFrame:
    index = np.arange(rows, dtype=float)
    return pd.DataFrame(
        {
            "A": 0.01 + 0.02 * np.sin(index / 3.0),
            "B": 0.008 + 0.015 * np.cos(index / 5.0),
            "C": 0.006 + 0.01 * np.sin(index / 7.0 + 1.0),
        },
        index=pd.date_range("2015-01-31", periods=rows, freq="ME"),
    )


def _covariance() -> np.ndarray:
    return np.array([[0.04, 0.006, 0.004], [0.006, 0.025, 0.003], [0.004, 0.003, 0.016]])


def test_configuration_preserves_open_owner_decisions(tmp_path: Path) -> None:
    config = load_portfolio_config()
    assert config.constraints.long_only and config.constraints.leverage_limit == 1.0
    assert config.constraints.maximum_weight is None
    with pytest.raises(ConfigurationError, match="open owner decisions"):
        config.costs.require_explicit()
    assert config.canonical_hash() == config.canonical_hash()
    raw = config.model_dump(mode="python")
    with pytest.raises(ValidationError):
        PortfolioConfig.model_validate({**raw, "minimum_observations": 40, "estimation_window": 20})
    with pytest.raises(ValidationError):
        PortfolioConfig.model_validate(
            {**raw, "constraints": {**raw["constraints"], "long_only": False}}
        )
    invalid = tmp_path / "invalid.yaml"
    invalid.write_text("unknown: true\n", encoding="utf-8")
    with pytest.raises(ConfigurationError):
        load_portfolio_config(invalid)


def test_transparent_allocations_and_constraint_verification() -> None:
    np.testing.assert_allclose(equal_weight(4), np.full(4, 0.25))
    np.testing.assert_allclose(market_cap_weight(np.array([1.0, 2.0, 3.0])), [1 / 6, 2 / 6, 3 / 6])
    with pytest.raises(DataQualityError):
        equal_weight(0)
    with pytest.raises(DataQualityError):
        market_cap_weight(np.array([1.0, 0.0]))
    constraints = ConstraintSet(
        maximum_weight=0.6,
        turnover_limit=0.5,
        sector_limits={"tech": 0.7},
        exposure_limits={"beta": (0.8, 1.2)},
        liquidity_trade_limits={"A": 0.3},
    )
    checks = constraints.verify(
        np.array([0.4, 0.3, 0.3]),
        ("A", "B", "C"),
        previous=np.array([0.3, 0.35, 0.35]),
        sectors=("tech", "tech", "finance"),
        exposures={"beta": np.array([1.0, 1.1, 0.9])},
    )
    assert checks["turnover"] == pytest.approx(0.2)
    with pytest.raises(DataQualityError, match="infeasible"):
        ConstraintSet(maximum_weight=0.2).validate(3)
    with pytest.raises(DataQualityError, match="Sector"):
        constraints.verify(
            np.array([0.5, 0.3, 0.2]),
            ("A", "B", "C"),
            sectors=("tech", "tech", "finance"),
        )


def test_constraint_adversarial_rejections() -> None:
    for invalid in (
        ConstraintSet(long_only=False),
        ConstraintSet(leverage_limit=1.2),
        ConstraintSet(minimum_weight=-0.1),
        ConstraintSet(maximum_weight=2.0),
        ConstraintSet(turnover_limit=3.0),
        ConstraintSet(transaction_cost_limit=-1.0),
        ConstraintSet(sector_limits={"tech": 2.0}),
        ConstraintSet(exposure_limits={"beta": (2.0, 1.0)}),
        ConstraintSet(liquidity_trade_limits={"A": -0.1}),
    ):
        with pytest.raises(DataQualityError):
            invalid.validate(3)
    with pytest.raises(DataQualityError, match="misaligned"):
        ConstraintSet().verify(np.array([1.0]), ("A", "B"))
    with pytest.raises(DataQualityError, match="budget"):
        ConstraintSet().verify(np.array([0.2, 0.2]), ("A", "B"))
    with pytest.raises(DataQualityError, match="maximum"):
        ConstraintSet(maximum_weight=0.6).verify(np.array([0.7, 0.3]), ("A", "B"))
    with pytest.raises(DataQualityError, match="turnover"):
        ConstraintSet(turnover_limit=0.1).verify(
            np.array([0.7, 0.3]), ("A", "B"), previous=np.array([0.5, 0.5])
        )
    with pytest.raises(DataQualityError, match="Liquidity"):
        ConstraintSet(liquidity_trade_limits={"A": 0.1}).verify(
            np.array([0.7, 0.3]), ("A", "B"), previous=np.array([0.5, 0.5])
        )
    with pytest.raises(DataQualityError, match="Exposure"):
        ConstraintSet(exposure_limits={"beta": (0.9, 1.1)}).verify(
            np.array([0.5, 0.5]),
            ("A", "B"),
            exposures={"beta": np.array([2.0, 2.0])},
        )


@pytest.mark.parametrize(
    "method",
    [
        "minimum_variance",
        "mean_variance",
        "maximum_sharpe",
        "maximum_diversification",
        "risk_parity",
        "hrp",
    ],
)
def test_constrained_optimizers_converge(method: str) -> None:
    result = optimize(
        method,  # type: ignore[arg-type]
        np.array([0.08, 0.06, 0.04]),
        _covariance(),
        ConstraintSet(maximum_weight=0.8),
        asset_ids=("A", "B", "C"),
    )
    assert result.converged
    assert result.weights.sum() == pytest.approx(1.0)
    assert (result.weights >= 0).all()
    assert np.isfinite(result.objective_value)


def test_cvar_optimizer_and_infeasible_detection() -> None:
    scenarios = _returns(50).to_numpy()
    result = optimize(
        "cvar",
        scenarios.mean(axis=0),
        np.cov(scenarios, rowvar=False),
        ConstraintSet(maximum_weight=0.8),
        scenarios=scenarios,
    )
    assert result.weights.sum() == pytest.approx(1.0)
    with pytest.raises(DataQualityError, match="scenarios"):
        optimize("cvar", scenarios.mean(axis=0), np.cov(scenarios, rowvar=False), ConstraintSet())
    with pytest.raises(DataQualityError, match="Expected returns"):
        optimize("minimum_variance", np.array([1.0]), _covariance(), ConstraintSet())


def test_covariance_estimators_and_singular_regularization() -> None:
    returns = _returns()
    for method in ("sample", "ledoit_wolf", "robust"):
        matrix = estimate_covariance(returns, method)
        assert validate_covariance(matrix)["minimum_eigenvalue"] >= -1e-10
    singular = np.array([[1.0, 1.0], [1.0, 1.0]])
    repaired = regularize_covariance(singular)
    assert np.linalg.eigvalsh(repaired).min() > 0
    with pytest.raises(DataQualityError, match="positive semidefinite"):
        validate_covariance(np.array([[1.0, 2.0], [2.0, 1.0]]))
    with pytest.raises(DataQualityError, match="Unsupported"):
        estimate_covariance(returns, "unknown")
    with pytest.raises(DataQualityError, match="twice"):
        estimate_covariance(returns.iloc[:5], "robust")
    with pytest.raises(DataQualityError, match="square"):
        regularize_covariance(np.ones((2, 3)))


def test_black_litterman_bayesian_and_hrp() -> None:
    covariance = _covariance()
    posterior, posterior_covariance = black_litterman_posterior(
        covariance,
        np.array([0.5, 0.3, 0.2]),
        2.5,
        np.array([[1.0, -1.0, 0.0]]),
        np.array([0.02]),
        np.array([[0.01]]),
    )
    assert posterior.shape == (3,)
    validate_covariance(posterior_covariance)
    mean, bayes_cov = bayesian_mean(
        np.zeros(3), covariance, np.array([0.01, 0.02, 0.03]), covariance * 2
    )
    assert mean.shape == (3,) and bayes_cov.shape == (3, 3)
    weights = hierarchical_risk_parity(covariance)
    assert weights.sum() == pytest.approx(1.0)
    with pytest.raises(DataQualityError, match="dimensionally"):
        black_litterman_posterior(
            covariance, np.ones(2), 2.0, np.ones((1, 3)), np.ones(1), np.eye(1)
        )


def test_risk_metrics_and_contribution_reconciliation() -> None:
    returns = _returns(40)["A"]
    benchmark = _returns(40)["B"]
    assert volatility(returns) > 0
    assert rolling_volatility(returns, 6).notna().sum() == 35
    beta, alpha = beta_alpha(returns, benchmark)
    assert np.isfinite(beta) and np.isfinite(alpha)
    assert rolling_beta(returns, benchmark, 6).notna().sum() == 35
    assert maximum_drawdown(returns) == pytest.approx(drawdown(returns).min())
    assert value_at_risk(returns) >= 0
    assert value_at_risk(returns, method="parametric") >= 0
    assert expected_shortfall(returns) >= value_at_risk(returns)
    weights = np.array([0.4, 0.3, 0.3])
    marginal, component = risk_contributions(weights, _covariance())
    assert component.sum() == pytest.approx(np.sqrt(weights @ _covariance() @ weights))
    assert len(marginal) == 3 and diversification_ratio(weights, _covariance()) > 1
    summary = risk_summary(returns, benchmark)
    assert {"sharpe", "sortino", "calmar", "omega", "cvar_95"} <= set(summary)
    with pytest.raises(DataQualityError, match="confidence"):
        value_at_risk(returns, confidence=2.0)
    with pytest.raises(DataQualityError, match="window"):
        rolling_volatility(returns, 1)
    with pytest.raises(DataQualityError, match="benchmark"):
        beta_alpha(returns, pd.Series(1.0, index=returns.index))
    with pytest.raises(DataQualityError, match="positive"):
        risk_contributions(np.array([0.5, 0.5]), np.zeros((2, 2)))
    with pytest.raises(DataQualityError, match="aligned"):
        risk_summary(returns, benchmark.iloc[:-1])


def test_scenario_framework_discloses_unmapped_shocks() -> None:
    scenario = Scenario("crash and rates", {"market": -0.2, "rates": 0.01}, "market_crash")
    result = apply_scenario(
        scenario,
        np.array([0.6, 0.4]),
        {"market": np.array([1.1, 0.8])},
    )
    assert result["portfolio_impact"] == pytest.approx(-0.196)
    assert result["unmapped_shocks"] == ["rates"]
    assert result["is_forecast"] is False
    with pytest.raises(DataQualityError):
        Scenario("", {}, "forecast")


def test_transaction_costs_and_backtest_are_reconciled_and_past_only() -> None:
    costs = TransactionCostModel(2.0, 4.0, 1.0, 0.0)
    estimate = costs.estimate(np.array([0.5, -0.5]))
    assert estimate["turnover"] == 1.0
    assert estimate["total_cost"] == pytest.approx(0.0005)
    with pytest.raises(DataQualityError, match="liquidity"):
        TransactionCostModel(0.0, 0.0, 0.0, 0.1).estimate(np.array([0.1]))
    impacted = TransactionCostModel(0.0, 0.0, 0.0, 0.1).estimate(np.array([0.1]), np.array([1.0]))
    assert impacted["market_impact"] > 0
    returns = _returns(30)
    benchmark = returns.mean(axis=1)
    history_ends: list[pd.Timestamp] = []

    def allocator(history: pd.DataFrame, previous: np.ndarray) -> np.ndarray:
        history_ends.append(history.index.max())
        return equal_weight(history.shape[1])

    result = run_backtest(returns, benchmark, allocator, costs, window=8)
    rebalance_dates = list(result.allocations["date"].drop_duplicates())
    assert all(
        history_end < rebalance
        for history_end, rebalance in zip(history_ends, rebalance_dates, strict=True)
    )
    summary = performance_summary(result.returns)
    assert summary["net_cumulative_return"] <= summary["gross_cumulative_return"]
    changed = returns.copy()
    changed.iloc[-1] += 10
    rerun = run_backtest(
        changed, benchmark, lambda history, previous: equal_weight(3), costs, window=8
    )
    pd.testing.assert_frame_equal(result.allocations, rerun.allocations)
    expanding = run_backtest(
        returns,
        benchmark,
        lambda history, previous: equal_weight(3),
        costs,
        window=8,
        mode="expanding",
        rebalance_every=2,
    )
    assert len(expanding.returns) == len(returns) - 8
    with pytest.raises(TemporalIntegrityError):
        run_backtest(
            returns.sort_index(ascending=False),
            benchmark.sort_index(ascending=False),
            lambda h, p: equal_weight(3),
            costs,
            window=8,
        )


def test_optimizer_enforces_sector_exposure_liquidity_and_cost_budget() -> None:
    previous = np.full(3, 1 / 3)
    constraints = ConstraintSet(
        maximum_weight=0.6,
        sector_limits={"tech": 0.7},
        exposure_limits={"beta": (0.8, 1.2)},
        liquidity_trade_limits={"A": 0.15},
        transaction_cost_limit=0.001,
    )
    result = optimize(
        "minimum_variance",
        np.array([0.08, 0.06, 0.04]),
        _covariance(),
        constraints,
        asset_ids=("A", "B", "C"),
        previous_weights=previous,
        sectors=("tech", "finance", "finance"),
        exposures={"beta": np.array([1.1, 1.0, 0.9])},
        transaction_cost_rate=0.001,
    )
    assert result.weights[0] <= previous[0] + 0.15 + 1e-7
    with pytest.raises(DataQualityError, match="previous weights"):
        optimize(
            "minimum_variance",
            np.array([0.08, 0.06, 0.04]),
            _covariance(),
            constraints,
        )
    with pytest.raises(DataQualityError, match="Sector labels"):
        optimize(
            "minimum_variance",
            np.array([0.08, 0.06, 0.04]),
            _covariance(),
            ConstraintSet(sector_limits={"tech": 0.5}),
            sectors=("tech",),
        )


def test_performance_reconciliation_rejects_tampering() -> None:
    frame = pd.DataFrame(
        {
            "gross_return": [0.01, 0.02, -0.01],
            "transaction_cost": [0.001, 0.0, 0.0],
            "net_return": [0.009, 0.02, -0.01],
            "benchmark_return": [0.005, 0.01, -0.005],
            "active_return": [0.004, 0.01, -0.005],
        }
    )
    performance_summary(frame)
    with pytest.raises(DataQualityError, match="Gross"):
        performance_summary(frame.assign(net_return=0.0))
    with pytest.raises(DataQualityError, match="Active"):
        performance_summary(frame.assign(active_return=0.0))


def _factor_portfolios(periods: int = 16) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    start = date(2018, 1, 31)
    for index in range(periods):
        current = start + timedelta(days=31 * index)
        benchmark = 0.004 + 0.003 * np.sin(index / 4)
        for factor_number, factor in enumerate(("value", "momentum"), start=1):
            for quantile in (1, 3):
                rows.append(
                    {
                        "date": current,
                        "factor_id": factor,
                        "quantile": quantile,
                        "value_weighted_return": benchmark
                        + 0.002 * factor_number
                        + 0.001 * quantile * np.cos(index / (factor_number + 1)),
                        "benchmark_return": benchmark,
                    }
                )
    return pd.DataFrame(rows)


class _Factors:
    def __init__(self) -> None:
        self.manifest = SimpleNamespace(publication_id="phase2", content_hash=lambda: "a" * 64)
        portfolio_frame = _factor_portfolios()
        self.table = pa.Table.from_pandas(portfolio_frame, preserve_index=False)
        self.factors = pa.Table.from_pandas(
            pd.DataFrame(
                {
                    "date": portfolio_frame["date"].drop_duplicates(),
                    "factor_id": "risk_free_rate",
                    "raw_value": 0.001,
                }
            ),
            preserve_index=False,
        )

    def authenticate(self, publication_id: str) -> SimpleNamespace:
        assert publication_id == "phase2"
        return self.manifest

    def read_portfolios(self, publication_id: str) -> pa.Table:
        self.authenticate(publication_id)
        return self.table

    def read_table(self, publication_id: str) -> pa.Table:
        self.authenticate(publication_id)
        return self.factors


class _Pricing:
    def authenticate(self, publication_id: str) -> SimpleNamespace:
        assert publication_id == "phase3"
        return SimpleNamespace(
            publication_id="phase3",
            phase2_publication_id="phase2",
            phase2_manifest_hash="a" * 64,
            content_hash=lambda: "b" * 64,
        )


def _service_config() -> PortfolioConfig:
    base = load_portfolio_config()
    return base.model_copy(
        update={
            "estimation_window": 6,
            "minimum_observations": 6,
            "covariance_method": "sample",
            "costs": base.costs.model_copy(
                update={
                    "commission_bps": 1.0,
                    "spread_bps": 2.0,
                    "slippage_bps": 1.0,
                    "market_impact_coefficient": 0.0,
                }
            ),
            "publication": base.publication.model_copy(
                update={"output_root": Path("outputs"), "manifest_root": Path("manifests")}
            ),
        }
    )


def test_authenticated_portfolio_publication_restart_and_tamper(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(service_module, "_git_commit", lambda root: "deadbeef")
    service = PortfolioResearchService(_service_config(), tmp_path, _Factors(), _Pricing())  # type: ignore[arg-type]
    first = service.compute_and_publish("phase3", "equal_weight")
    second = service.compute_and_publish("phase3", "equal_weight")
    assert first.publication_id == second.publication_id
    assert service.repository.list_authenticated() == (first.publication_id,)
    target = next(item for item in first.artifacts if item.name == "allocations")
    path = tmp_path / target.path
    path.write_bytes(path.read_bytes() + b"attack")
    with pytest.raises(EvidenceIntegrityError, match="changed"):
        service.repository.authenticate(first.publication_id)
    assert PortfolioRepository(tmp_path, tmp_path / "manifests").list_authenticated() == ()


def test_authenticated_service_runs_optimized_method(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(service_module, "_git_commit", lambda root: "deadbeef")
    service = PortfolioResearchService(
        _service_config(),
        tmp_path,
        _Factors(),
        _Pricing(),  # type: ignore[arg-type]
    )
    manifest = service.compute_and_publish("phase3", "minimum_variance")
    diagnostics = next(
        item for item in manifest.artifacts if item.name == "optimization_diagnostics"
    )
    assert diagnostics.columns
