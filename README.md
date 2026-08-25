# Institutional Multi-Factor Asset Pricing & Portfolio Analytics Platform

An authenticated, reproducible institutional-style quantitative research platform spanning governed data, factor research, classical asset pricing, constrained portfolios, risk, explainable machine learning, and non-advisory research delivery.

## Project at a glance

This independent research project asks what remains of a multi-factor US-equity research pipeline when historical identity, filing-time availability, transaction costs, out-of-sample evaluation, and reproducibility are treated as first-class constraints. It connects effective-dated market and SEC evidence to factor construction, asset-pricing tests, constrained portfolios, walk-forward machine learning, and authenticated research delivery.

The difficult part was not producing another backtest. It was preventing present-day tickers, late-filed fundamentals, unavailable securities, inconsistent adjustment bases, or future outcomes from silently entering earlier decisions. The system therefore fails closed when evidence cannot support a claim. That design produced an important negative result: multifactor models improved in-sample fit, but the study did not establish stable machine-learning predictability or after-cost incremental value.

| Verified project evidence | Result |
|---|---:|
| Securities screened / accepted | 822 / 487 |
| Market / fundamental observations | 715,447 / 37,273 |
| Factor definitions / estimable | 48 / 47 |
| Configured asset-pricing models | 5 |
| Portfolio methods / ML models | 8 / 8 |
| Walk-forward ML folds | 17 |
| Tests / branch-aware coverage | 300 / 90.59% |

For a rapid review, read the [case study](docs/PROJECT_CASE_STUDY.md), [research paper](docs/FINAL_RESEARCH_PAPER.md), and [final assurance report](docs/FINAL_PROJECT_ASSURANCE_REPORT.md). The project demonstrates combined finance, econometrics, software architecture, data engineering, and model-risk judgment; it does not claim professional investment experience or persistent alpha.

## Status

The software implementation spans Phases 1-6, and the final local empirical study spans Phases 1-8. All 822 HF Data Library stock candidates were screened before performance analysis, producing 487 defensibly bounded equities (372 Tier A, 115 Tier B). Raw, processed, and generated empirical artifacts remain local and untracked.

Authenticated publications now cover expanded Phase 1, all 48 configured Phase 2 factors (47 estimable; `equity_issuance` non-estimable), five Phase 3 asset-pricing families, eight Phase 4 portfolio methods under transaction costs frozen before performance, eight Phase 5 purged walk-forward models, and Phase 6 API/dashboard/report delivery. The empirical results do not establish stable alpha or ML value: multifactor fit improves in-sample, costs are material, and ML IC intervals include zero. These are free/public-data research findings, not an investment mandate or trading claim.

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

The release gate requires the complete test suite, at least 90% branch-aware coverage, strict source typing, lint/format, dependency and repository-integrity checks, plus restart and tamper assurance.

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
- The free/public-data universe is source-availability selected and is not CRSP, Compustat, Russell 1000, or historical S&P 500 membership replication.
- Effective coverage is bounded: annual security breadth rises from 4 in 2018 to 487 in 2024–2026; missing early PIT evidence is not backfilled.
- Phase 4 evidence spans only 32 months and uses factor-portfolio test assets; its observed performance is not evidence of persistence.
- Phase 5 does not establish stable incremental predictive or after-cost economic value; explanation metrics are non-causal.
- The authenticated research release is tagged, but GitHub Actions remain subject to an external account/billing limitation; Docker was outside the empirical assurance scope.
- See the [Final Research Paper](docs/FINAL_RESEARCH_PAPER.md) and [Final Project Assurance Report](docs/FINAL_PROJECT_ASSURANCE_REPORT.md).

## Reproducibility and academic use

Results must bind approved source evidence, configuration, code revision, dependencies, timestamps, seeds, validation, and limitations. Academic users must cite original data and methodology sources, respect source licenses, disclose survivorship and availability limitations, and must not present software fixtures as research findings.

## License

Licensed under the [MIT License](LICENSE). Copyright (c) 2026 AMIT KUMAR DUDI.
