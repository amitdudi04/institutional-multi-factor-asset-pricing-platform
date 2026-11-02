# Multi-Factor Asset Pricing & Portfolio Research Platform

An independent US-equity research project combining source-selected public data and point-in-time-oriented controls, factor construction, classical asset pricing, portfolio allocation, transaction-cost analysis, risk analytics, and walk-forward machine learning.

## Overview

This project studies how point-in-time data quality, factor construction, asset-pricing models, portfolio costs, and temporal validation affect empirical U.S. equity research results.

The current study screens a broad public-data equity universe, constructs observable characteristics, compares standard asset-pricing specifications, evaluates constrained portfolio methods, and tests whether simple machine-learning models add stable out-of-sample information. The results are mixed rather than uniformly positive: multifactor models fit the project portfolios better than CAPM in-sample, transaction costs matter, portfolio methods produce different risk-return trade-offs, and the machine-learning study does not establish stable incremental value.

## Research Paper and Audit Trail

The [final candidate working paper](outputs/audit/final_correction/FINAL_CANDIDATE_MANUSCRIPT.pdf) is the accepted manuscript revision for author review, not a claim of journal acceptance. Its editable DOCX is controlled locally. [Author declarations remain pending](outputs/audit/final_correction/DEFERRED_AUTHOR_REVIEW.md).

For review, start with the [methodology](docs/METHODOLOGY.md), [corrected results](docs/RESULTS.md), [permanent 50-issue tracker](docs/research_audit/MASTER_AUDIT_TRACKER.md), [final correction evidence](outputs/audit/final_correction/FINAL_CORRECTION_REPORT.md) and [repository release review](outputs/audit/final_release/FINAL_RELEASE_REVIEW.md).

## Main Results

Numerical authority: [accepted correction commit f22f5cb](https://github.com/amitdudi04/institutional-multi-factor-asset-pricing-platform/tree/f22f5cbe365e98c8d5fef6b5308ff765703df173/outputs/audit), with the [Phase 3 reconciliation](https://github.com/amitdudi04/institutional-multi-factor-asset-pricing-platform/tree/f22f5cbe365e98c8d5fef6b5308ff765703df173/outputs/audit/phase3/PHASE3_COMPLETE_VALIDATION.md) and [Phase 2C matched-sample checks](https://github.com/amitdudi04/institutional-multi-factor-asset-pricing-platform/tree/f22f5cbe365e98c8d5fef6b5308ff765703df173/outputs/audit/phase2c/PHASE2C_REGRESSION_VERIFICATION.md). The [accepted documentation and candidate manuscript](https://github.com/amitdudi04/institutional-multi-factor-asset-pricing-platform/tree/028dfd9cd18bcd6ef8114d829cc789d5bffacc61) preserve the interpretation of these results. Original releases are historical records.

| Area | Current result |
|---|---|
| Universe | 822 securities screened; 487 accepted and 335 rejected |
| Market data | 715,447 daily observations |
| SEC-derived fundamentals | 37,273 observations; recorded availability controls, not exhaustive historical capture certification |
| Factors | 48 names; 47 with nonmissing raw values; 41 quantile characteristics; 11,352 corrected quantile-cycle rows |
| Asset pricing | Matched mean adjusted R²: CAPM 0.760818; FF3 0.802438; Carhart 4 0.811021; FF5 0.817658; q-style 0.814361 |
| Portfolios | 8 long-only sleeve allocations; 31 complete cycles; 5/10/20 bps per absolute-traded-weight unit |
| ML design | 27,632 rows; 89 common month ends; 15 dependent OOS folds; 7,286 held-out observations per family |
| ML conclusion | Linear-family intervals nominally positive, RF crosses zero, XGBoost negative; stable incremental after-cost economic value remains unestablished |

For the complete numerical summary and interpretation, see [docs/RESULTS.md](docs/RESULTS.md).

## Research Questions

The hypotheses as worded in the supplied manuscript evaluate whether:

1. at least one factor spread survives the complete pre-specified cost and multiplicity rule;
2. multifactor models improve explanatory fit relative to CAPM and that improvement extends to stable out-of-sample economic evidence;
3. estimated relations remain stable through time under the original rule;
4. higher transaction-cost assumptions reduce cumulative outcomes;
5. constrained portfolio methods alter risk-return trade-offs and any apparent superiority is stable out of sample;
6. machine learning adds stable out-of-sample predictive and after-cost value; and
7. explanation rankings remain stable across methods.

These are bounded historical propositions, not newly authenticated preregistration. H1/H3 remain inconclusive because original approval/direction and complete decision evidence are unavailable.

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
              recorded-day security and issuer mapping
                              ↓
                    822 candidates screened
                         487 accepted
                              ↓
                    factor construction
                   48 defined / 47 estimable
                              ↓
          CAPM / FF3 / Carhart 4 / FF5 / q mapping
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

The factor engine contains 48 configured definitions spanning market, size, value, momentum, profitability, investment/leverage, and risk/liquidity characteristics. Forty-seven are estimable in the current empirical release.

`equity_issuance` remains non-estimable because the available point-in-time SEC evidence does not support a consistent calculation without unsupported imputation. Missing evidence is therefore left missing rather than converted to zero.

## Asset-Pricing Results

Matched per-asset comparison: 123 correlated dependent portfolios, 67–77 full trading cycles per asset and 615 primary regressions.

| Model | Mean adjusted R² | Alpha (decimal return per full trading cycle) | Nominal HAC p < 0.05 |
|---|---:|---:|---:|
| CAPM | 0.760818 | -0.001658 | 8/123 |
| Fama-French 3 | 0.802438 | -0.001967 | 12/123 |
| Carhart 4 | 0.811021 | -0.001879 | 14/123 |
| Fama-French 5 | 0.817658 | -0.002008 | 8/123 |
| Study-specific q-style | 0.814361 | -0.002227 | 9/123 |

Mean alphas are negative cycle returns, not annualized investment alpha. No primary intercept survives supplementary Holm adjustment; non-rejection does not establish exactly zero alpha. Internal proxies and six duplicate return-series pairs limit external pricing interpretation.

The multifactor specifications provide greater in-sample explanatory fit than CAPM on these project portfolios. That result is not interpreted as proof of persistent alpha, causality, or future performance.

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

The modeled per-side rates are 5, 10 and 20 bps per unit of absolute L1 traded weight. Half-L1 one-way turnover is a separate quantity. Initial BASE deployment costs 10 bps; a full invested switch costs 20 bps. The evaluation spans 31 complete monthly trading cycles (exit labels 2024-02-01 to 2026-08-03), allocating to 123 constructed long-only quantile sleeves. Inner-sleeve execution and full market impact are not established.

Selected 10 bps BASE results:

| Method | Observed result |
|---|---:|
| Minimum Variance | Annualized volatility: 9.9505% |
| Maximum Diversification | Corrected-path maximum drawdown: -4.8279% |
| Maximum Sharpe | Sharpe ratio: 1.346360 |
| CVaR | Cumulative net return: 73.6842%; Sharpe ratio: 1.252327 |

These are descriptive results from a short factor-portfolio window. They do not establish persistent strategy superiority.

## Walk-Forward Machine Learning

The ML study uses book-to-market and 12-minus-1 momentum to predict the next 21-trading-session security return relative to SPY.

The evaluation uses:

- monthly decisions;
- expanding training starting at 60 calendar months and reaching 74;
- 12 validation periods;
- one test month per fold;
- label purging;
- a one-month embargo;
- monthly retraining;
- 15 dependent complete out-of-sample folds; five of 14 adjacent test-target pairs overlap.

Eight models are evaluated: zero and historical-mean baselines, factor composite, linear regression, Ridge, Elastic Net, Random Forest, and XGBoost.

Factor composite and linear use the same LinearRegression estimator and yield identical predictions. Their mean IC is 0.034430; Ridge 0.034434; Elastic Net 0.044609; Random Forest -0.002641; XGBoost -0.023285. Constant-baseline IC is undefined. Block-bootstrap intervals (100 resamples, block 3, seed 17) are exploratory: linear families are nominally positive, RF crosses zero and XGBoost is negative. These dependent, multiple-model comparisons do not establish stable predictability. The economic check selects 20% of equities, equal weights them and resets to cash for one subsequent session with initial fees; it is not a continuous 21-session investment strategy. Stable incremental after-cost economic value has not been established.

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

Fresh release tests and CI are recorded in the [release validation record](outputs/audit/final_release/FINAL_TEST_AND_CI_RESULTS.txt). The historical Phase 3 checkpoint passed 372 tests with 90.62% coverage, plus a 91-test targeted run. Software assurance does not certify empirical validity, source vintage or investability.

## API and Dashboard

```shell
uv run institutional-factor-platform serve-api
uv run institutional-factor-platform serve-dashboard
```

The API and Streamlit dashboard expose stored research outputs. They are research interfaces, not brokerage or live-trading infrastructure. See [docs/SOFTWARE_USAGE.md](docs/SOFTWARE_USAGE.md).

## Reproducibility

The **historical original** empirical release is identified by:

- tag: `project-complete-public-data-v1`
- parallel research tag: `research-empirical-public-v1`
- commit: `5a3e930665756fa7aaedeceb5f9ab90792bcf849`

Exact empirical reproduction requires lawful access to the same third-party source data, mappings, configuration, and locked environment. See [docs/REPRODUCIBILITY.md](docs/REPRODUCIBILITY.md).

## Limitations

The principal limitations are:

- source-availability selection and incomplete historical-universe coverage;
- limited early cross-sectional breadth;
- incomplete exhaustive SEC capture chronology and issuer/share-class attribution;
- frozen provider-vintage adjusted-quote returns with unverified complete dividend-inclusive comparability;
- modeled close decisions and retrospective forecasts rather than verified historical fills or live timestamps;
- 31 complete portfolio cycles using 123 synthetic sleeves rather than directly executable equity portfolios;
- transaction costs modeled as sensitivity assumptions rather than measured executions;
- two ML characteristics and 15 dependent test folds;
- no stable after-cost ML improvement;
- non-causal feature-importance and scenario outputs.

See [docs/LIMITATIONS.md](docs/LIMITATIONS.md) for the full discussion.

## Finance-Professor Review: Interpretation and Boundaries

These points address common methodological questions about the **existing** experiment; they are not claims of new robustness tests.

- **Security selection and historical data.** The 487 accepted securities are from 822 provider-supplied candidates, not the entire historical US market. Missing delisted firms, incomplete SEC capture chronology, listing/share-class mapping, and unverified complete dividend-inclusive adjustments limit generalization. The system enforces recorded-day availability checks; it does not certify same-close tradability or live fills.
- **Pricing fit and factor independence.** FF5's mean adjusted R² of 0.817658 is a matched-sample *internal explanatory-fit* statistic on constructed test portfolios. Six return-series pairs are duplicated, constituent exposures overlap, and some quantiles contain one security. The 109-asset constituent-exclusion diagnostic helps inspect self-inclusion but does not supply an independent external validation. The study-specific q-style earnings-yield proxy is not accounting ROE or an exact Hou–Xue–Zhang factor replication. Negative mean regression intercepts are compatible with high adjusted R²; no tested intercept survives supplementary Holm adjustment, which is not proof of zero true alpha.
- **Portfolio accounting and generalization.** Eight methods allocate to 123 constructed sleeves, rather than directly trading 487 stocks. The verified 5/10/20 bps assumptions apply per **absolute traded-weight (L1) unit**: one-way turnover is half L1, initial BASE deployment costs 10 bps, and a fully invested switch costs 20 bps. The 73.6842% CVaR cumulative net result and 31-cycle strategy rankings are descriptive; underlying constituent trading costs, capacity and actual execution remain unverified. Historical 95% VaR/expected-shortfall summaries use only two tail observations.
- **Forecasts versus investment tests.** The statistical ML target spans 21 complete sessions, but the economic comparison selects the top-ranked 20% and holds for **one subsequent session**, resetting capital each fold. Fifteen test folds have dependent future labels; five adjacent test-target pairs overlap. Linear and factor-composite predictions coincide because they use the same estimator. XGBoost has negative mean rank IC despite a positive one-session selected-portfolio mean: these measure different outcomes and do not imply a contradiction. The 100-resample IC intervals are exploratory, not evidence of stable economic alpha.
- **Hypotheses and reproducibility.** H1/H3 remain inconclusive because complete original decision authority is absent. Exact empirical reproduction requires lawfully held frozen input data and source manifests that cannot all be redistributed. Corrected values supersede historical numerical interpretations without retroactively changing historical evidence.

For derivations, sources and limitations, use [Methodology](docs/METHODOLOGY.md), [Results](docs/RESULTS.md), [Data and Sources](docs/DATA_AND_SOURCES.md), [Limitations](docs/LIMITATIONS.md), and [Research Architecture](docs/ARCHITECTURE.md).

## Release and Software Citation Context

The `CITATION.cff` release date of **2026-08-27** identifies the *historical software-release metadata*; it is not the date of the November 2026 corrected working-paper candidate. The current manuscript revision and its separate content hash are documented in the [final correction manifest](outputs/audit/final_correction/FINAL_DOCUMENT_CHECKSUMS.json). No new software release or tag is implied.

The last inspected PR [#9](https://github.com/amitdudi04/institutional-multi-factor-asset-pricing-platform/pull/9) was **not merged** because the dependency security audit reported advisories for locked `certifi` and Pillow. Resolve and validate the lockfile using the existing dependency resolver and security gate before merging; do not suppress advisories or change finance results. The authoritative status is the live PR/CI, not this dated note.

## License and Citation

Original code and documentation are licensed under the [MIT License](LICENSE). Third-party datasets remain subject to their own licenses and terms.

Repository citation metadata are provided in [CITATION.cff](CITATION.cff). Upstream datasets should be cited separately.
