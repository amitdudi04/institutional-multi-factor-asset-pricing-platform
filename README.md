# Institutional Multi-Factor Asset Pricing & Portfolio Analytics Platform

A research-driven framework intended to support reproducible multi-factor asset pricing, portfolio construction, risk attribution, explainable machine learning, and institutional investment decision support.

## Current status

Repository governance and the owner-approved [Project Specification](docs/PROJECT_SPECIFICATION.md) are complete. Phase 1 is independently assured. Phase 2 is implemented and internally assured: authenticated parent artifacts feed versioned point-in-time characteristics, date-local preprocessing, next-period factor-quantile diagnostics, and checksum-bound immutable publications. Phase 3 is authorized as the next phase but has not started. No asset-pricing model, optimizer, backtest, machine-learning model, API, dashboard, or empirical investment claim has been implemented.

The governing standard is [docs/DEVELOPMENT_CONSTITUTION.md](docs/DEVELOPMENT_CONSTITUTION.md). Phase 2 methods are documented in [docs/PHASE2_FACTOR_METHODOLOGY.md](docs/PHASE2_FACTOR_METHODOLOGY.md); implementation, validation, and internal-audit evidence is retained in the corresponding Phase 2 reports. All Phase 1 audit and remediation reports remain preserved as historical evidence.

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

The package separates configuration, authenticated data access, factor contracts, temporal alignment, factor definitions, preprocessing, diagnostics, validation, immutable persistence, and CLI orchestration. Analytical logic remains independent of notebooks, APIs, and dashboards. Later-phase model, optimization, risk, and delivery layers do not exist.

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
```

See [docs/DATA_SOURCE_GUIDE.md](docs/DATA_SOURCE_GUIDE.md) before any live retrieval and [docs/PHASE2_INPUT_GUIDE.md](docs/PHASE2_INPUT_GUIDE.md) before preparing factor inputs.

## Results availability

Empirical results are **not available**. Phase 2 software tests use isolated synthetic fixtures only; no live dataset, factor return, chart, or investment conclusion is committed. Runtime factor outputs are ignored local artifacts and require authenticated Phase 1 parent publications.

## License

This project is licensed under the [MIT License](LICENSE). Copyright (c) 2026 AMIT KUMAR DUDI.
