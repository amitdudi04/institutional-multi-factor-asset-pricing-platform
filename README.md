# Institutional Multi-Factor Asset Pricing & Portfolio Analytics Platform

A research-driven framework intended to support reproducible multi-factor asset pricing, portfolio construction, risk attribution, explainable machine learning, and institutional investment decision support.

## Current status

Repository governance and the owner-approved [Project Specification](docs/PROJECT_SPECIFICATION.md) are complete. Phase 1 is independently assured. Phases 2–5 are implemented and internally assured. Phase 5 adds authenticated point-in-time ML datasets, purged temporal validation, baseline/linear/forest/XGBoost research models, calibration, SHAP/permutation explanations, drift, model cards, Phase 4 economic-evaluation integration, and immutable publications. Phase 6 is authorized as the next phase but has not started. No API, dashboard, deployment, live model, or empirical investment claim has been implemented.

The governing standard is [docs/DEVELOPMENT_CONSTITUTION.md](docs/DEVELOPMENT_CONSTITUTION.md). Phase 5 architecture and methods are documented in [docs/PHASE5_ARCHITECTURE.md](docs/PHASE5_ARCHITECTURE.md) and [docs/PHASE5_METHODOLOGY.md](docs/PHASE5_METHODOLOGY.md). Implementation, model-validation, model-card, and internal-audit evidence is retained in the corresponding Phase 5 reports. Historical Phase 1–4 evidence remains unchanged.

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

The package separates configuration, authenticated data access, factors, asset pricing, constraints, optimization, portfolios, risk, scenarios, costs, backtesting, performance, machine learning, explainability, immutable research outputs, and CLI orchestration. Analytical logic remains independent of notebooks, APIs, and dashboards. The Phase 6 delivery layer does not exist.

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
uv run institutional-factor-platform validate-ml-config
uv run institutional-factor-platform list-ml-publications
```

See [docs/DATA_SOURCE_GUIDE.md](docs/DATA_SOURCE_GUIDE.md) before any live retrieval and [docs/PHASE2_INPUT_GUIDE.md](docs/PHASE2_INPUT_GUIDE.md) before preparing factor inputs.

## Results availability

Empirical results are **not available**. Phase 2–5 tests use isolated synthetic software fixtures only; no live dataset, factor return, regression result, portfolio result, model artifact, explanation, chart, or investment conclusion is committed. Runtime Phase 5 outputs are ignored local artifacts and require connected authenticated publications plus explicit target, horizon, cost, and other open-decision inputs. `LIVE EMPIRICAL ML VALIDATION PENDING`.

## License

This project is licensed under the [MIT License](LICENSE). Copyright (c) 2026 AMIT KUMAR DUDI.
