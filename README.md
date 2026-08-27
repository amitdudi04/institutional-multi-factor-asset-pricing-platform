# Institutional Multi-Factor Asset Pricing & Portfolio Analytics Platform

An auditable public-data research pipeline for point-in-time US-equity factors, asset pricing, portfolio risk, and walk-forward machine learning.

## Overview

This project studies how empirical equity results change when historical identity, filing-time availability, transaction costs, temporal validation, and reproducibility are treated as part of the research design. It connects governed public-source evidence to factor construction, classical asset-pricing tests, constrained portfolios, risk analytics, machine-learning evaluation, and authenticated research delivery.

The purpose is not to advertise persistent alpha. The released study preserves negative and inconclusive findings, distinguishes estimability from zero, and fails closed when available evidence cannot support a result.

> **Key empirical results**
>
> - **Universe:** 822 securities screened; 487 accepted and 335 rejected.
> - **Data:** 715,447 daily market observations and 37,273 point-in-time fundamental observations.
> - **Factors:** 47 of 48 configured definitions were estimable.
> - **Asset pricing:** CAPM mean adjusted R² was 0.063; multifactor specifications ranged from 0.259 to 0.301.
> - **Portfolios:** eight allocation methods were evaluated under one-way 5/10/20-basis-point cost schedules; higher costs reduced every cumulative result.
> - **Machine learning:** eight models completed 17 purged out-of-sample folds; all aggregate bootstrap IC confidence intervals for non-constant models included zero, and stable after-cost incremental value was not established.

## Research Questions

The preregistered hypotheses ask whether:

1. at least one factor spread survives the complete net-cost and multiple-testing decision rule;
2. multifactor models improve on CAPM;
3. factor relationships remain stable across regimes;
4. higher transaction costs reduce portfolio performance;
5. constrained portfolio methods create distinct risk and concentration trade-offs;
6. machine learning adds stable out-of-sample predictive and after-cost economic value; and
7. feature importance is stable across models and explanation methods.

## Key Findings

1. Public and free data support a substantial point-in-time research pipeline, but source-selection, identity, lifecycle, and coverage limitations remain material.
2. Forty-seven of 48 characteristics are constructible under the released evidence rules. `equity_issuance` is not estimable from defensible inputs.
3. Multifactor models provide materially greater in-sample explanatory fit than CAPM on the diagnostic portfolios.
4. Portfolio construction and transaction costs materially affect observed risk-return outcomes; no method is established as persistently superior.
5. More complex machine-learning models do not establish stable incremental out-of-sample predictive or after-cost economic value.

## Research Pipeline

```text
Public-source evidence
        ↓
Point-in-time security identity, market data, and fundamentals
        ↓
Governed universe screening and immutable publications
        ↓
Factor construction and diagnostic portfolios
        ↓
Asset-pricing regressions and robust inference
        ↓
Constrained portfolios, transaction costs, and risk
        ↓
Purged walk-forward machine learning
        ↓
Versioned reports, API, dashboard, and assurance
```

## Data Sources

| Source | Research role | Important limitation |
|---|---|---|
| HF Data Library | Historical US-equity market observations and initial candidate universe | Source-selected universe; pre-2022 survivorship limitations; PiTrading-to-IEX source transition affects volume comparability |
| SEC EDGAR | CIK identity, filings, filing-time fundamentals, shares, and taxonomy evidence | Accounting concepts and filing coverage vary across issuers and time |
| Alpha Vantage `LISTING_STATUS` | Listing and lifecycle evidence used during screening | Coverage does not reconstruct every provider-absent historical security |
| FRED `DGS3MO` | Approved 3-month Treasury-bill risk-free reference | Frequency conversion and release timing must be governed |
| Kenneth French Data Library | Reference factor and methodology evidence | Provider definitions are not automatically identical to project-specific mappings |
| SPY | Broad investable US-equity benchmark proxy | It is not a historical total-market or constituent-membership database |

Raw third-party data and authenticated local publications are not redistributed by this repository.

## Dataset Summary

| Measure | Frozen result |
|---|---:|
| Candidate securities screened | 822 |
| Accepted / rejected | 487 / 335 |
| Tier A / Tier B accepted securities | 372 / 115 |
| Daily market observations | 715,447 |
| Market sample | 2018-02-14 to 2026-08-04 |
| Point-in-time fundamental observations | 37,273 |
| Fundamental availability sample | 2019-02-23 to 2026-08-15 |

The frozen universe is not a reconstruction of CRSP, Compustat, the historical S&P 500, or the Russell 1000.

## Factor Research

The factor engine contains 48 configured definitions across market, size, value, momentum, profitability, investment/leverage, and risk/liquidity families. Forty-seven were estimable in the frozen release, producing 34,341,456 long-form factor rows and 11,545 factor-portfolio rows.

`equity_issuance` remains **not estimable from defensible inputs** because the approved point-in-time SEC concepts do not support a consistent calculation without unsupported imputation. Non-estimable does not mean zero.

## Asset-Pricing Results

Mean adjusted R² across 123 diagnostic portfolios per configured model:

| Model | Mean adjusted R² |
|---|---:|
| CAPM | 0.063 |
| Fama-French 3 | 0.259 |
| Carhart 4 | 0.277 |
| Fama-French 5 | 0.301 |
| Configured q mapping | 0.296 |

The configured q mapping is project-specific and is not claimed as an exact Hou-Xue-Zhang replication. Higher in-sample explanatory fit does not establish persistent alpha, causality, forecast accuracy, or investable performance.

## Portfolio Construction

The released study compares eight long-only, fully invested, unlevered methods:

- Equal Weight
- Minimum Variance
- Mean Variance
- Maximum Sharpe
- Maximum Diversification
- Risk Parity
- Hierarchical Risk Parity
- CVaR

## Transaction Costs

The one-way cost schedules were frozen before portfolio performance was inspected:

| Schedule | One-way assumption |
|---|---:|
| LOW | 5 bps |
| BASE | 10 bps |
| HIGH | 20 bps |

Higher assumed costs reduced cumulative results for every portfolio method. Nonlinear market impact was not estimated because no authenticated liquidity input supported it.

## Selected Portfolio Results

Selected frozen BASE results from the approximately 32-month factor-portfolio test window:

| Method | Observed result |
|---|---:|
| Minimum Variance | Lowest annualized volatility: 10.00% |
| Maximum Diversification | Smallest maximum drawdown: -5.43% |
| Maximum Sharpe | Sharpe ratio: 1.575 |
| CVaR | Highest cumulative return: 83.17%; Sharpe ratio: 1.667 |

These are descriptive results on factor-portfolio test assets. CVaR led observed cumulative return, while other methods led on different risk measures; persistent strategy superiority is not established.

## Machine Learning

The ML study uses two authenticated features: book-to-market and 12-minus-1 momentum. The target is the next 21-trading-session security return minus SPY's return over the same interval.

The walk-forward design uses 60 monthly training periods, 12 validation periods, one test month, monthly retraining, label purging, a one-month embargo, seed 17, and single-thread estimators. The real decision panel contains 27,640 observations across 91 monthly dates and 17 complete out-of-sample folds.

Eight models were evaluated: zero and historical-mean baselines, factor composite, linear regression, Ridge, Elastic Net, Random Forest, and XGBoost.

## ML Results

All aggregate bootstrap information-coefficient confidence intervals for non-constant models include zero.

- **Stable predictive information:** not established.
- **Stable after-cost incremental value:** not established.

Random Forest's small positive mean after-cost fold result was positive in only 9 of 17 folds. This is a legitimate negative empirical result, not evidence that the software failed.

## Hypothesis Outcomes

| Hypothesis | Outcome |
|---|---|
| H1 | Inconclusive |
| H2 | Partially supported |
| H3 | Inconclusive |
| H4 | Supported |
| H5 | Partially supported |
| H6 | Not supported |
| H7 | Not supported |

## Why the Negative Results Matter

Universe admission, transaction costs, feature families, model grids, temporal splits, and hypothesis rules were fixed before the relevant results were inspected. Preserving weak, negative, and inconclusive outcomes limits researcher degrees of freedom and is more informative than repeatedly tuning the study until a favorable result appears.

## Architecture

```text
config/   Frozen research and delivery configuration
src/      Data, factors, asset pricing, portfolios, risk, ML, and delivery code
tests/    Unit, connected, restart, tamper, and deployment assurance
docs/     Methodology, governance, architecture, results, and user guides
data/     Public structure guide; empirical data remain local and ignored
paper/    Canonical public research manuscript
```

See the [repository manifest](docs/REPOSITORY_MANIFEST.md) and [system architecture](docs/FINAL_SYSTEM_ARCHITECTURE.md).

## Quick Start

Python 3.11 or newer and [uv](https://docs.astral.sh/uv/) are required.

```shell
uv sync --all-groups
uv run institutional-factor-platform validate-config
uv run institutional-factor-platform validate-delivery-config
uv run institutional-factor-platform verify-delivery-platform
```

Credentials are read only from environment variables. Copy `.env.example` to an untracked `.env` when local bearer protection is required.

## Running Tests

```shell
uv run pytest
uv run coverage report --fail-under=90
uv run ruff check .
uv run ruff format --check .
uv run mypy src
uv lock --check
```

The final verified counts are recorded in the [cleanup report](outputs/repository-cleanup/FINAL_REPOSITORY_CLEANUP_REPORT.md) after the post-packaging checks run.

## Running the API and Dashboard

```shell
uv run institutional-factor-platform serve-api
uv run institutional-factor-platform serve-dashboard
```

The API defaults to `127.0.0.1:8000` under `/api/v1`; the Streamlit dashboard defaults to `127.0.0.1:8501`. Empty empirical state is represented explicitly and is never replaced with fabricated examples.

## Reproducibility

- Empirical release tag: `project-complete-public-data-v1`
- Parallel empirical tag: `research-empirical-public-v1`
- Frozen empirical commit: `5a3e930665756fa7aaedeceb5f9ab90792bcf849`

Both tags resolve to the frozen commit. Repository cleanup occurs above that record and does not move the tags or alter Phase 1-5 empirical results. Reproduction requires lawful acquisition of the source evidence described in [data/README.md](data/README.md) and the [reproducibility guide](docs/FINAL_REPRODUCIBILITY_GUIDE.md).

## Research Paper

The canonical public manuscript is available as [Institutional Multi-Factor Asset Pricing Research Paper](paper/Institutional_Multi_Factor_Asset_Pricing_Research_Paper.pdf). It is an independent research manuscript and is not represented as peer reviewed or formally published on SSRN.

## Limitations

- The universe is selected by public-source availability and is not CRSP/Compustat or historical-index replication.
- The HF Data Library universe has pre-2022 survivorship limitations; provider-absent delisted securities cannot be reconstructed.
- The PiTrading-to-IEX source transition limits historical volume and liquidity comparability.
- Early cross-sectional coverage is sparse.
- SEC accounting concepts and issuer reporting practices are heterogeneous.
- Equity issuance is non-estimable under the released evidence rules.
- Phase 4 spans only about 32 months and uses factor portfolios rather than direct-security portfolios.
- Transaction costs are modeled sensitivity assumptions; nonlinear market impact is not estimated.
- Phase 5 uses two features and 17 complete test folds.
- H1 and H3 remain inconclusive because the complete preregistered multiplicity and regime decisions are unavailable.
- Feature importance and SHAP values are non-causal.

## Citation

Primary market-data citation:

> Elkassabgi, Ahmed. (2026). *HF Data Library: High-Frequency U.S. Equity Data* (Version 1.0) [Dataset]. Zenodo. https://doi.org/10.5281/zenodo.19501605

For the software and research repository, use the metadata in [`CITATION.cff`](CITATION.cff) and cite the frozen empirical release and commit above. Cite each upstream provider separately and comply with its terms.

## License

Repository code and original documentation are licensed under the [MIT License](LICENSE), copyright © 2026 Amit Kumar Dudi. Third-party datasets, provider archives, and derived materials remain subject to their own licenses and terms. The MIT License does not grant permission to redistribute HF Data Library, IEX, Alpha Vantage, SEC, FRED, Kenneth French, or other third-party source data.
