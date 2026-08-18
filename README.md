# Institutional Multi-Factor Asset Pricing & Portfolio Analytics Platform

An authenticated, reproducible institutional-style quantitative research platform spanning governed data, factor research, classical asset pricing, constrained portfolios, risk, explainable machine learning, and non-advisory research delivery.

## Status

Phases 1-6 are implemented and exhaustively reconciled in v1.0.2. Immutable Phase 1 evidence flows through connected Phase 2-5 publications into the versioned FastAPI service, institutional Streamlit workspace, deterministic reporting, secure local Docker foundation, and CI gates. Authenticated synthetic assurance covers all 48 factors, six asset-pricing specifications, every supported ML target, the connected API/dashboard/report surfaces, restart authentication, and cross-phase tamper rejection.

A defensibly bounded real Phase 1 runtime publication now exists for AAPL and MSFT; raw and processed empirical data remain untracked. The preregistered Phase 2 study is not estimable because maximum authenticated breadth is two versus the approved minimum of three. No empirical factor premium, regression result, portfolio performance, model output, or investment conclusion is claimed.

## Architecture

1. Phase 1 - immutable data ingestion, validation, lifecycle evidence, lineage, and authenticated research access.
2. Phase 2 - point-in-time factors, portfolios, diagnostics, and immutable publications.
3. Phase 3 - asset-pricing models, robust inference, diagnostics, comparisons, and authenticated outputs.
4. Phase 4 - constrained allocations, portfolio accounting, transaction costs, risk, scenarios, and backtests.
5. Phase 5 - temporally safe ML, challengers, calibration, explanation, drift, cards, and economic evaluation.
6. Phase 6 - FastAPI, Streamlit, reports/exports, observability, security, Docker, CI, and final assurance.

The [Development Constitution](docs/DEVELOPMENT_CONSTITUTION.md) and [Project Specification](docs/PROJECT_SPECIFICATION.md) govern all phases. See [Final Platform Architecture](docs/FINAL_PLATFORM_ARCHITECTURE.md) and [Final Repository Assurance](docs/FINAL_REPOSITORY_ASSURANCE.md).

## Installation

Python 3.11 or newer and [uv](https://docs.astral.sh/uv/) are required.

```shell
uv sync --all-groups
uv run institutional-factor-platform validate-config
uv run institutional-factor-platform validate-delivery-config
uv run institutional-factor-platform verify-delivery-platform
```

Configuration is strict and stored under `config/`. Credentials are never stored in YAML. Copy `.env.example` to an untracked `.env` only when local Docker or bearer protection requires it.

## CLI

Core commands validate and operate each governed phase. Delivery commands are:

```shell
uv run institutional-factor-platform validate-delivery-config
uv run institutional-factor-platform verify-delivery-platform
uv run institutional-factor-platform serve-api
uv run institutional-factor-platform serve-dashboard
```

Run `uv run institutional-factor-platform --help` for the complete command surface.

## API and dashboard

The API listens on `127.0.0.1:8000` by default under `/api/v1`. The dashboard listens on `127.0.0.1:8501`. It contains overview, lineage, factor, asset-pricing, portfolio, risk, ML, validation/audit, and report-builder workspaces.

```shell
uv run institutional-factor-platform serve-api
uv run institutional-factor-platform serve-dashboard
```

Empty empirical state is supported explicitly. The applications do not substitute test fixtures or fabricate charts. See the [API Guide](docs/PHASE6_API_GUIDE.md) and [Dashboard Guide](docs/PHASE6_DASHBOARD_GUIDE.md).

## Docker

Set a strong `IFP_API_TOKEN` in an untracked `.env`, then:

```shell
docker compose up --build
```

The containers run non-root, expose host-loopback ports, mount authenticated data read-only, use a separate writable report volume, and drop capabilities. Docker is a local deployment foundation, not a cloud production SLA. See the [Deployment Guide](docs/PHASE6_DEPLOYMENT_GUIDE.md).

## Testing

```shell
uv run pytest
uv run coverage report --fail-under=90
uv run ruff check .
uv run ruff format --check .
uv run mypy src
uv lock --check
```

The v1.0.2 gate requires the complete test suite, at least 90% branch-aware coverage, strict source typing, lint/format, dependency and repository-integrity checks, plus clean-root connected assurance. CI repeats the governed suite, configuration/import smoke checks, dependency audit, and Docker build.

## Security and data policy

Raw data is immutable. Research reads authenticate manifests, checksums, lifecycle state, schema, configuration, Git identity, and lineage. API/dashboard clients cannot supply local paths, SQL, Python expressions, model files, or templates. Loopback is the default; optional bearer tokens come only from environment variables. See [SECURITY.md](SECURITY.md) and [Phase 6 Security](docs/PHASE6_SECURITY.md).

Empirical data, databases, generated reports, model artifacts, caches, secrets, and local environments are ignored. Source licenses remain source-specific; the MIT project license does not grant rights to redistribute third-party data.

## Supported research methods

The platform includes point-in-time factor construction; CAPM and multifactor regression; robust and rolling inference; long-only unlevered allocation methods; covariance, constraints, costs, risk, scenarios, and reconciled backtesting; baseline, regularized-linear, Random Forest, and XGBoost research models; calibration, permutation/SHAP explanation, drift, model cards, and deterministic reports.

## Limitations

- Research outputs are not financial advice or investment recommendations.
- Test fixtures validate software only and are not empirical evidence.
- SHAP and feature importance are not causal.
- Model performance is not guaranteed.
- Local bearer protection is not enterprise identity management.
- No brokerage, live execution, streaming prices, automatic retraining, or cloud SLA exists.
- Docker was unavailable on the final local audit host; static validation passed and CI contains an image-build gate.
- The bounded free/public-data intersection has only two securities with defensible identity, market continuity, and compatible PIT evidence. Phase 2 requires at least three, so Phases 2–6 empirical execution and final research release remain unauthorized. See [Phase 7 Empirical Data Readiness](docs/PHASE7_EMPIRICAL_DATA_READINESS_REPORT.md).

## Reproducibility and academic use

Results must bind approved source evidence, configuration, code revision, dependencies, timestamps, seeds, validation, and limitations. Academic users must cite original data and methodology sources, respect source licenses, disclose survivorship and availability limitations, and must not present software fixtures as research findings.

## License

Licensed under the [MIT License](LICENSE). Copyright (c) 2026 AMIT KUMAR DUDI.
