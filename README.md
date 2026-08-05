# Institutional Multi-Factor Asset Pricing & Portfolio Analytics Platform

A research-driven framework intended to support reproducible multi-factor asset pricing, portfolio construction, risk attribution, explainable machine learning, and institutional investment decision support.

## Current status

Repository governance and the owner-approved [Project Specification](docs/PROJECT_SPECIFICATION.md) are complete. Phase 1 is independently assured. Phases 2–4 are implemented and internally assured. Phase 4 adds constrained allocation and optimization, covariance estimation, portfolio/risk/performance analytics, non-forecasting scenarios, transaction costs, past-only backtest infrastructure, and authenticated immutable publications. Phase 5 is authorized as the next phase but has not started. No machine-learning model, API, dashboard, or empirical investment claim has been implemented.

The governing standard is [docs/DEVELOPMENT_CONSTITUTION.md](docs/DEVELOPMENT_CONSTITUTION.md). Phase 4 architecture and methods are documented in [docs/PHASE4_ARCHITECTURE.md](docs/PHASE4_ARCHITECTURE.md) and [docs/PHASE4_METHODOLOGY.md](docs/PHASE4_METHODOLOGY.md). Implementation, validation, and internal-audit evidence is retained in the corresponding Phase 4 reports. Historical Phase 1–3 evidence remains unchanged.

## Planned phases

1. Institutional Data Platform
2. Multi-Factor Research Engine
3. Asset-Pricing Research Platform
4. Portfolio Construction and Institutional Backtesting
5. Risk Analytics and Explainable Machine Learning
6. API, Dashboard, and Research Workspace
7. Production Hardening and Research Publication

These phases are scope boundaries, not claims of implemented functionality. See [docs/PROJECT_ROADMAP.md](docs/PROJECT_ROADMAP.md).

## Research and data integrity

The platform will not fabricate financial data, model outputs, portfolio results, or research conclusions. Owner-provided raw data is authoritative and will remain immutable. Missing inputs must cause an explicit, actionable failure rather than silent substitution. Every future empirical result must be traceable to its source data, configuration, code version, environment, and execution metadata.

## Intended architecture

The package separates configuration, authenticated data access, factors, asset pricing, constraints, optimization, portfolios, risk, scenarios, costs, backtesting, performance, immutable research outputs, and CLI orchestration. Analytical logic remains independent of notebooks, APIs, and dashboards. Later-phase machine-learning and delivery layers do not exist.

## Development setup

Python 3.11 or newer and [uv](https://docs.astral.sh/uv/) are recommended.

```shell
uv sync --all-groups
uv run pytest
uv run ruff check .
uv run ruff format --check .
uv run mypy src
```

The default configuration is `config/base.yaml`; secrets are supplied only through documented environment variables. Copy `.env.example` to an untracked `.env` if needed, but the package does not automatically load `.env` files. Validate configuration and create ignored local storage with:

```shell
uv run institutional-factor-platform validate-config
uv run institutional-factor-platform init-storage
uv run institutional-factor-platform validate-factor-config
uv run institutional-factor-platform list-factor-publications
uv run institutional-factor-platform validate-asset-pricing-config
uv run institutional-factor-platform list-asset-pricing-publications
uv run institutional-factor-platform validate-portfolio-config
uv run institutional-factor-platform list-portfolio-publications
```

See [docs/DATA_SOURCE_GUIDE.md](docs/DATA_SOURCE_GUIDE.md) before any live retrieval and [docs/PHASE2_INPUT_GUIDE.md](docs/PHASE2_INPUT_GUIDE.md) before preparing factor inputs.

## Results availability

Empirical results are **not available**. Phase 2–4 tests use isolated synthetic software fixtures only; no live dataset, factor return, regression result, portfolio result, chart, or investment conclusion is committed. Runtime Phase 4 outputs are ignored local artifacts and require connected authenticated Phase 2 and Phase 3 publications plus explicit open-decision inputs.

## License

This project is licensed under the [MIT License](LICENSE). Copyright (c) 2026 AMIT KUMAR DUDI.
