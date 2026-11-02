"""Run from repository root: uv run python outputs/audit/phase1/reproduce_numerical_evidence.py."""

import csv
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd

from institutional_factor_platform.backtest.costs import TransactionCostModel
from institutional_factor_platform.factors.config import load_factor_config
from institutional_factor_platform.factors.definitions import FACTOR_DEFINITIONS
from institutional_factor_platform.risk.metrics import maximum_drawdown

ROOT = Path(__file__).resolve().parent


def write_csv(name: str, rows: list[dict]) -> None:
    with (ROOT / name).open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


rows = []
for label, values in {
    "first_loss_rebound": [-0.2, 0.1],
    "falling": [-0.1, -0.1, -0.1],
    "recovery": [-0.2, 0.25, -0.1],
    "constant_positive": [0.02, 0.02],
    "constant_negative": [-0.02, -0.02],
    "flat": [0.0, 0.0],
    "later_loss": [0.1, -0.2, 0.3],
}.items():
    wealth = pd.Series(np.cumprod(1 + np.array(values)))
    old = float((wealth / wealth.cummax() - 1).min())
    capital = peak = 1.0
    expected = 0.0
    for value in values:
        capital *= 1 + value
        peak = max(peak, capital)
        expected = min(expected, capital / peak - 1)
    actual = maximum_drawdown(pd.Series(values))
    assert abs(actual - expected) < 1e-14
    rows.append(
        dict(
            issue_id="P1",
            evidence_type="SYNTHETIC",
            case=label,
            input_json=json.dumps(values),
            input_sha256=hashlib.sha256(json.dumps(values).encode()).hexdigest(),
            original_value=old,
            corrected_value=actual,
            reference_value=expected,
            difference=actual - old,
            unit="decimal_NAV_drawdown",
            note="initial NAV=1",
        )
    )

for rate in [5, 10, 20]:
    half_spread, slippage, fixed_allowance = {5: (2, 1, 2), 10: (5, 2, 3), 20: (10, 4, 6)}[rate]
    for label, trades in {
        "buy_deploy": [1.0, 0.0],
        "sell": [-1.0, 0.0],
        "switch": [-1.0, 1.0],
        "drift": [-0.1, 0.1],
    }.items():
        fee = TransactionCostModel(0, 2 * half_spread, slippage + fixed_allowance, 0).estimate(
            np.array(trades)
        )
        reference = sum(abs(value) * rate / 10000 for value in trades)
        assert abs(fee["total_cost"] - reference) < 1e-14
        assert abs(fee["spread"] - fee["turnover"] * half_spread / 10000) < 1e-14
        assert abs(fee["slippage"] - fee["turnover"] * (slippage + fixed_allowance) / 10000) < 1e-14
        rows.append(
            dict(
                issue_id="P2",
                evidence_type="SYNTHETIC",
                case=f"{rate}bps_{label}",
                input_json=json.dumps(trades),
                input_sha256=hashlib.sha256(json.dumps(trades).encode()).hexdigest(),
                original_value=fee["total_cost"],
                corrected_value=fee["total_cost"],
                reference_value=reference,
                difference=0,
                unit="NAV_fraction",
                note=f"L1={fee['turnover']}; half_L1={fee['turnover'] / 2}; "
                f"full_spread_bps={2 * half_spread}; "
                f"bundled_slippage_bps={slippage + fixed_allowance}; nonlinear_impact=0; "
                "documentary decomposition PDF Table8, not frozen ledger",
            )
        )

for method in [
    "equal_weight",
    "minimum_variance",
    "mean_variance",
    "maximum_sharpe",
    "maximum_diversification",
    "risk_parity",
    "hierarchical_risk_parity",
    "cvar",
]:
    rows.append(
        dict(
            issue_id="P1",
            evidence_type="HISTORICAL_SOURCE_BLOCKED",
            case=method,
            input_json="UNAVAILABLE frozen net-return path",
            input_sha256="UNAVAILABLE",
            original_value={
                "equal_weight": -0.0857,
                "minimum_variance": -0.0669,
                "mean_variance": -0.1781,
                "maximum_sharpe": -0.0751,
                "maximum_diversification": -0.0543,
                "risk_parity": -0.0833,
                "hierarchical_risk_parity": -0.0813,
                "cvar": -0.0855,
            }[method],
            corrected_value="",
            reference_value="",
            difference="",
            unit="decimal_NAV_drawdown",
            note="reported PDF Table9 p13/Table11 p15, ref868baa9; not recomputed from returns",
        )
    )
for case in ["first", "last", "all", "null"]:
    rows.append(
        dict(
            issue_id="D8",
            evidence_type="SYNTHETIC",
            case=f"missing_{case}",
            input_json="tests/test_research_phase1_audit.py fixture",
            input_sha256=hashlib.sha256(
                Path("tests/test_research_phase1_audit.py").read_bytes()
            ).hexdigest(),
            original_value="accepted incomplete evidence",
            corrected_value="DataQualityError",
            reference_value="reject incomplete evidence",
            difference="not numeric",
            unit="publication_gate",
            note="no missing return fabricated; empirical impact unknown",
        )
    )
write_csv("PHASE1_NUMERICAL_RECONCILIATION.csv", rows)

config = load_factor_config()
inventory = []
lookbacks = {
    "momentum_1m": "21 sessions, min20, no skip",
    "momentum_3m": "63 sessions, min20, no skip",
    "momentum_6m": "126 sessions, min20, no skip",
    "momentum_12m": "252 sessions, min20, no skip",
    "momentum_24m": "504 sessions, min20, no skip",
    "momentum_12_1m": "231 sessions, min20, shift21 sessions",
    "residual_momentum": "231 residual sessions, min20, shift21; beta trailing252 min20",
    "rolling_market_beta": "252 sessions, min20, sample covariance/variance",
    "beta": "252 sessions, min20, sample covariance/variance",
    "rolling_beta": "252 sessions, min20, sample covariance/variance",
    "rolling_correlation": "252 sessions, min20",
    "rolling_volatility": "252 sessions, min20, sample std times sqrt252",
    "downside_volatility": (
        "252 sessions, min20 negative returns, conditional sample std times sqrt252"
    ),
    "semi_variance": "252 sessions, min20 negative returns, conditional mean square times252",
    "downside_beta": "252 sessions, min20 negative-market pairs",
    "idiosyncratic_volatility": "252 residual sessions, min20, sample std times sqrt252",
    "tracking_error": "252 active-return sessions, min20, sample std times sqrt252",
    "average_dollar_volume": "21 sessions, min20",
    "turnover": "current session volume / latest available shares; no rolling average",
    "amihud_illiquidity": "current session abs(return) / dollar volume; no rolling average",
    "bid_ask_proxy": "current session high-low divided by midpoint; no quoted-spread input",
    "market_return": "current approved daily market return",
    "excess_return": "current approved daily market and cash returns",
    "risk_free_rate": "current approved daily cash return",
}
for definition in FACTOR_DEFINITIONS:
    inventory.append(
        dict(
            factor_id=definition.factor_id,
            formula=definition.formula,
            unit=definition.unit,
            required_inputs=";".join(definition.required_inputs),
            direction=definition.direction,
            timing="as-of end-of-UTC-day; decision-time validity source blocked",
            lookback_policy=lookbacks.get(
                definition.factor_id,
                "current price/latest as-of shares or annual accounting facts; "
                "prior/average fields use eligible annual observations where required; "
                "size indicators use current NYSE breakpoints",
            ),
            availability_lag="source available_at, no additional fixed SEC-day lag; "
            "join cutoff UTC day end; strictly-before-trade timing unverified",
            duplicate_exposure=(
                "identical raw beta: rolling_market_beta/beta/rolling_beta; beta score sign differs"
                if definition.factor_id in {"rolling_market_beta", "beta", "rolling_beta"}
                else "economic correlation possible; not asserted independent"
            ),
            valid_dates="SOURCE_EVIDENCE_BLOCKED",
            research_notes=definition.research_notes,
            configured_cross_section=config.preprocessing.minimum_cross_section,
        )
    )
assert len(inventory) == 48
write_csv("PHASE1_FACTOR_DEFINITION_INVENTORY.csv", inventory)
print(f"Wrote {len(rows)} reconciliation rows and {len(inventory)} factor definitions")
