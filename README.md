# Institutional Multi-Factor Asset Pricing & Portfolio Analytics Platform

A research-driven framework intended to support reproducible multi-factor asset pricing, portfolio construction, risk attribution, explainable machine learning, and institutional investment decision support.

## Current status

Repository governance and the owner-approved [Project Specification](docs/PROJECT_SPECIFICATION.md) are complete. Phase 1 material defects have been remediated with typed configuration, approved-source adapters, immutable raw and standardized publication, versioned contracts, validation/quarantine, validated-only DuckDB promotion, persisted lineage, canonical mapping evidence, exchange-calendar coverage, operator integrity commands, and offline adversarial tests. Phase 1 remains pending independent re-audit. No Phase 2 analytical model, portfolio engine, backtest, API, dashboard, or empirical result has been implemented.

The governing standard is [docs/DEVELOPMENT_CONSTITUTION.md](docs/DEVELOPMENT_CONSTITUTION.md). Phase 1 evidence is recorded in the [implementation report](docs/PHASE1_IMPLEMENTATION_REPORT.md), preserved [independent audit](docs/PHASE1_AUDIT_REPORT.md), and [remediation report](docs/PHASE1_REMEDIATION_REPORT.md).

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

Future work will use a layered core package separating configuration, data contracts, ingestion, validation, transformations, research models, portfolios, risk, backtesting, reporting, and delivery interfaces. Analytical logic will remain independent of notebooks, APIs, and dashboards. Only the configuration and cross-cutting foundations needed at this stage exist today.

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
```

See [docs/DATA_SOURCE_GUIDE.md](docs/DATA_SOURCE_GUIDE.md) before any live retrieval.

## Results availability

Analytical and empirical results are **not available**. Phase 1 provides data infrastructure only; no live dataset or research output is committed.

## License

This project is licensed under the [MIT License](LICENSE). Copyright (c) 2026 AMIT KUMAR DUDI.
