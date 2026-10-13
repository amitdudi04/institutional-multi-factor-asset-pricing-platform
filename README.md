# Multi-Factor Asset Pricing & Portfolio Research Platform

An independent US-equity research project combining point-in-time public data, factor construction, classical asset pricing, portfolio allocation, transaction-cost analysis, risk analytics, and walk-forward machine learning.

## Empirical Result Status

The numerical tables in this repository describe the previous empirical release; they are not regenerated outputs from the corrected calculations now under review. The code review identified a frequency mismatch between holding-period portfolio returns and daily market/risk-free factors, daily rather than holding-period risk-free returns in portfolio metrics, a Jensen-alpha calculation that omitted risk-free adjustment, and a constant-score ML baseline that could select securities by row order.

The audit branch corrects these calculations and adds targeted regression tests. The raw provider data required for the full empirical pipeline are not included in Git, so the corrected numerical results have not yet been regenerated. Treat the values below and in [docs/RESULTS.md](docs/RESULTS.md) as historical pre-correction snapshots only—not as validated results from the corrected implementation. See [the results reconciliation](docs/RESULTS_RECONCILIATION.md) for reviewer-facing notes on limitations, suspiciously similar ML summaries, hypothesis decisions, and the evidence still required. The linked paper should be revised after the corrected pipeline is run and its outputs are reconciled.

## Overview

This project studies how point-in-time data quality, factor construction, asset-pricing models, portfolio costs, and temporal validation affect empirical U.S. equity research results.

The previous release screens a broad public-data equity universe, constructs observable characteristics, compares conventional asset-pricing model forms with project-specific factor proxies, evaluates constrained portfolio methods, and tests whether simple machine-learning models add stable out-of-sample information. The results are mixed rather than uniformly positive: multifactor models fit the project portfolios better than CAPM in-sample, transaction costs matter, portfolio methods produce different risk-return trade-offs, and the machine-learning study does not establish stable incremental value.

## Previous Release Summary

| Area | Previously reported result |
|---|---|
| Universe | 822 securities screened; 487 accepted and 335 rejected |
| Market data | 715,447 daily observations |
| Point-in-time fundamentals | 37,273 observations |
| Factors | 48 definitions; 47 estimable |
| Asset pricing | Previously reported mean adjusted R²: CAPM 0.063; FF3-style project factors 0.259; Carhart-style project factors 0.277; FF5-style project factors 0.301; q-style project mapping 0.296 |
| Portfolios | 8 long-only methods tested under 5/10/20 bps one-way cost assumptions |
| ML design | 27,640 monthly decision observations across 91 months; 17 complete OOS folds |
| ML conclusion | All aggregate IC confidence intervals include zero; stable after-cost incremental value is not established |

For the complete numerical summary and interpretation, see [docs/RESULTS.md](docs/RESULTS.md).

## Research Questions

The pre-specified hypotheses evaluate whether:

1. at least one factor spread survives the complete pre-specified cost and multiplicity rule;
2. multifactor models improve explanatory fit relative to CAPM and that improvement extends to stable out-of-sample economic evidence;
3. estimated relations remain stable through time under the original rule;
4. higher transaction-cost assumptions reduce cumulative outcomes;
5. constrained portfolio methods alter risk-return trade-offs and any apparent superiority is stable out of sample;
6. machine learning adds stable out-of-sample predictive and after-cost value; and
7. explanation rankings remain stable across methods.

Hypotheses are classified as supported, partially supported, unsupported, or inconclusive according to the pre-specified evaluation criteria.

## Data and Universe

| Source | Role |
|---|---|
| HF Data Library | Historical US-equity market observations and initial candidate universe |
| SEC EDGAR | Filing identity, point-in-time fundamentals, shares, and XBRL evidence |
| Alpha Vantage | Listing and lifecycle evidence used in universe screening |
| FRED | 3-month constant-maturity Treasury yield reference (DGS3MO) |
| Kenneth French Data Library | Reference factor datasets and methodology comparison |
| SPY | Broad investable US-equity benchmark proxy |

The final panel is source-availability selected. It is not presented as a reconstruction of CRSP, Compustat, the historical S&P 500, or the Russell 1000. Raw third-party data are not redistributed through this repository.

More detail is in [docs/DATA_AND_SOURCES.md](docs/DATA_AND_SOURCES.md).

## Research Design

```text
Historical market data + listing/lifecycle evidence + SEC filings
                              ↓
              point-in-time security and issuer mapping
                              ↓
                    822 candidates screened
                         487 accepted
                              ↓
                    factor construction
                   48 defined / 47 estimable
                              ↓
          CAPM / FF3-style / Carhart-style / FF5-style / q-style project mapping
                              ↓
             8 constrained portfolio methods
                  + 5/10/20 bps costs
                              ↓
              purged monthly walk-forward ML
                              ↓
                 results, risk and reporting
```

The analytical design and formulas are summarized in [docs/METHODOLOGY.md](docs/METHODOLOGY.md).

## Factor Research

The factor engine contains 48 configured definitions spanning market, size, value, momentum, profitability, investment/leverage, and risk/liquidity characteristics. Forty-seven were estimable in the previous empirical release.

`equity_issuance` remains non-estimable because the available point-in-time SEC evidence does not support a consistent calculation without unsupported imputation. Missing evidence is therefore left missing rather than converted to zero.

## Previously Reported Asset-Pricing Results

Previously reported mean adjusted R² across 123 diagnostic portfolios per model:

| Model | Mean adjusted R² |
|---|---:|
| CAPM | 0.063 |
| FF3-style project factors | 0.259 |
| Carhart-style project factors | 0.277 |
| FF5-style project factors | 0.301 |
| q-style project mapping | 0.296 |

The previous release reported higher in-sample explanatory fit for its multifactor project specifications than for CAPM; these figures have not been recalculated after the methodology corrections. That result is not interpreted as proof of persistent alpha, causality, or future performance.

## Portfolio Research

Eight long-only, fully invested methods are compared:

- Equal Weight
- Minimum Variance
- Mean Variance
- Maximum Sharpe
- Maximum Diversification
- Risk Parity
- Hierarchical Risk Parity
- CVaR

The prior release used one-way transaction-cost assumptions of 5, 10, and 20 basis points over an approximately 32-month factor-portfolio window. Its cost comparisons are historical snapshots pending recalculation.

Previously reported 10 bps BASE results:

| Method | Observed result |
|---|---:|
| Minimum Variance | Lowest annualized volatility: 10.00% |
| Maximum Diversification | Smallest maximum drawdown: -5.43% |
| Maximum Sharpe | Sharpe ratio: 1.575 |
| CVaR | Highest cumulative return: 83.17%; Sharpe ratio: 1.667 |

These are descriptive results from a short factor-portfolio window. They do not establish persistent strategy superiority.

## Walk-Forward Machine Learning

The ML study uses book-to-market and 12-minus-1 momentum to predict the next 21-trading-session security return relative to SPY.

The evaluation uses:

- monthly decisions;
- 60 monthly training periods;
- 12 validation periods;
- one test month per fold;
- label purging;
- a one-month embargo;
- monthly retraining;
- 17 complete out-of-sample folds.

Eight models are evaluated: zero and historical-mean baselines, factor composite, linear regression, Ridge, Elastic Net, Random Forest, and XGBoost.

In the previous release, all aggregate bootstrap information-coefficient confidence intervals for non-constant models included zero. The previous release's Random Forest had a very small positive mean after-cost fold return, but it was positive in only 9 of 17 folds. The study therefore does not establish stable incremental predictive or economic value from the ML models.

## Repository Structure

```text
config/     Research and delivery configuration
src/        Data, factors, asset pricing, portfolios, risk, ML, API and dashboard code
tests/      Methodology, temporal-integrity, accounting and software tests
docs/       Research methodology, results, limitations and reproducibility
data/       Public data-access notes; empirical source files remain local
examples/   Small redistributable templates
```

## Quick Start

Python 3.11 or newer and `uv` are required.

```shell
uv sync --all-groups
uv run institutional-factor-platform validate-config
uv run institutional-factor-platform validate-delivery-config
uv run institutional-factor-platform verify-delivery-platform
```

Run the test suite:

```shell
uv run pytest
uv run coverage report --fail-under=90
uv run ruff check .
uv run ruff format --check .
uv run mypy src
uv lock --check
```

The previous verified research release recorded 301 tests passing with 90.52% branch-aware coverage. These historical software checks support reproducibility; they are not empirical evidence of investment performance or proof that corrected empirical tables have been regenerated.

## API and Dashboard

```shell
uv run institutional-factor-platform serve-api
uv run institutional-factor-platform serve-dashboard
```

The API and Streamlit dashboard expose stored research outputs. They are research interfaces, not brokerage or live-trading infrastructure. See [docs/SOFTWARE_USAGE.md](docs/SOFTWARE_USAGE.md).

## Reproducibility

The empirical release is identified by:

- tag: `project-complete-public-data-v1`
- parallel research tag: `research-empirical-public-v1`
- commit: `5a3e930665756fa7aaedeceb5f9ab90792bcf849`

Exact empirical reproduction requires lawful access to the same third-party source data, mappings, configuration, and locked environment. See [docs/REPRODUCIBILITY.md](docs/REPRODUCIBILITY.md).

## Limitations

The principal limitations are:

- source-availability selection and incomplete historical-universe coverage;
- limited early cross-sectional breadth;
- heterogeneous SEC accounting concepts and issuer reporting;
- a roughly 32-month portfolio test window using factor portfolios rather than directly investable security portfolios;
- transaction costs modeled as sensitivity assumptions rather than measured executions;
- two ML characteristics and 17 complete test folds;
- no stable after-cost ML improvement;
- non-causal feature-importance and scenario outputs.

See [docs/LIMITATIONS.md](docs/LIMITATIONS.md) for the full discussion.

## License and Citation

Original code and documentation are licensed under the [MIT License](LICENSE). Third-party datasets remain subject to their own licenses and terms.

Repository citation metadata are provided in [CITATION.cff](CITATION.cff). Upstream datasets should be cited separately.
