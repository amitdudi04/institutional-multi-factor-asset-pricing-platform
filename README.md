# Institutional Multi-Factor Asset Pricing & Portfolio Analytics Platform

A research-driven framework intended to support reproducible multi-factor asset pricing, portfolio construction, risk attribution, explainable machine learning, and institutional investment decision support.

## Current status

Repository governance is complete, the [Project Specification](docs/PROJECT_SPECIFICATION.md) is owner approved, and Phase 1 is authorized. Implementation has not started. The repository currently provides only governance/specification documents, validated base-configuration loading, project-root discovery, structured logging initialization, and tests for that foundation. No financial data pipeline, analytical model, portfolio engine, backtest, API, dashboard, or empirical result has been implemented.

The governing standard is [docs/DEVELOPMENT_CONSTITUTION.md](docs/DEVELOPMENT_CONSTITUTION.md). The initial repository assessment is recorded in [docs/REPOSITORY_INITIALIZATION_REPORT.md](docs/REPOSITORY_INITIALIZATION_REPORT.md). Phase 1 implementation must follow the approved specification and owner decisions.

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

The default configuration is `config/base.yaml`. It contains no investment assumptions or credentials. Copy `.env.example` to an untracked `.env` only when a future approved integration requires credentials; the current package does not automatically load `.env` files.

## Results availability

Analytical and empirical results are **not yet available**. Phase 1 is authorized but has not been implemented.

## License

This project is licensed under the [MIT License](LICENSE). Copyright (c) 2026 AMIT KUMAR DUDI.
