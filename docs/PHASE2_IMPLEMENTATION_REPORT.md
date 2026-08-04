# Phase 2 Implementation Report

## Executive summary

Phase 2 implements a typed, configuration-driven, point-in-time factor research layer on branch `phase/2-factor-engine`, starting from Phase 1 closeout commit `def6422c4a34bfa2fc76ea345895f7ac289d71b1`. It adds 48 versioned factor outputs across the authorized market, size, value, momentum, quality, investment, low-volatility, liquidity, and risk families; direction-aligned scores; monthly next-period diagnostic portfolios; diagnostics; immutable authenticated storage; and CLI workflows. No Phase 3 or later functionality was created.

No live provider data was downloaded and no empirical factor output was committed. Tests use isolated synthetic software fixtures that cannot enter research-ready storage without the same contracts and evidence gates.

## Architecture delivered

- Strict `config/factors.yaml` with daily research frequency, monthly rebalancing, windows, annualization, plausibility limits, preprocessing, optional sector/industry neutralization, NYSE breakpoints, portfolio diagnostics, and relative output paths.
- Data-layer `factor_market_input` and `factor_fundamental_input` contracts, owner-input unit rules, and mapping-authority enforcement.
- Factor service that reads only exact bytes from authenticated finalized Phase 1 handles and binds parent checksum, units, mapping, lineage, promotion, run, temporal policy, configuration, and Git identity.
- Point-in-time universe, classification, market, and fundamental validation with backward as-of joins and propagated availability.
- Raw, winsorized, normalized, and direction-aligned score values for every factor.
- Monthly ascending terciles for continuous characteristics, formation-date value weights, following-period returns, benchmark and active returns, and no same-period execution.
- Coverage, outlier, correlation, top-tercile turnover, group return, descriptive t-statistic, monotonicity, and rolling-performance diagnostics with plot-data hooks.
- Staged immutable Parquet/JSON publication, atomic envelope activation, idempotent restart, checksum/schema/identity authentication, and byte-bound read-time isolation.
- CLI commands for strict owner factor-input ingestion, configuration validation, factor computation, publication listing, and publication verification.

## Factor families

The complete formula catalog is in `docs/PHASE2_FACTOR_METHODOLOGY.md`. Runtime manifests repeat each definition, formula, rationale, required inputs, unit, preferred direction, transformation chain, dependencies, version, research notes, validation state, configuration hash, and Git commit.

## Phase boundaries

Not implemented: CAPM or multifactor regressions, alpha/inference, portfolio optimization, institutional backtesting, risk engine, attribution, machine learning, explainability, API, dashboard, or reporting UI. Factor-quantile returns are descriptive Phase 2 validation artifacts, not Phase 4 backtests or investment recommendations.

## Reproducibility and recovery

Publication identity hashes complete authenticated parent evidence, factor configuration, factor version, and code commit. Configuration, validation, diagnostics, lineage, characteristic Parquet, and portfolio Parquet are content-bound by the manifest and final envelope. The exact bytes parsed on parent and factor reads are the bytes hashed. A crash before atomic activation leaves no discoverable publication; a retry reuses identical immutable artifacts and activates one valid envelope.

## Owner decisions

No Owner Decision Register status was changed. Monthly rebalancing is applied. The configurable robust-z/1st–99th percentile settings are disclosed implementation defaults while preprocessing thresholds remain open. No cost or significance threshold is invented. Historical eligibility, classification, total-return, shares, benchmark, RF, and filing availability must arrive as authenticated evidence; missing evidence fails.

## Non-fabrication confirmation

The implementation contains no embedded market history, factor result, coefficient, chart, portfolio claim, or provider response. Missing and undefined values remain null. The repository contains no tracked runtime dataset, Parquet output, database, cache, credential, or generated research artifact.
