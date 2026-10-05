# Research Results

This document is the public numerical record for the current research repository. The values below correspond to the frozen empirical release identified in [REPRODUCIBILITY.md](REPRODUCIBILITY.md). The repository does not store a manuscript PDF; the empirical results remain documented here without personal-profile metadata.

## 1. Universe and Data

| Measure | Result |
|---|---:|
| Candidate securities screened | 822 |
| Accepted securities | 487 (59.25%) |
| Rejected securities | 335 (40.75%) |
| Daily market observations | 715,447 |
| Market sample | 2018-02-14 to 2026-08-04 |
| Point-in-time fundamental observations | 37,273 |
| Fundamental availability sample | 2019-02-23 to 2026-08-15 |

### Screening outcomes

| Rejection reason | Count |
|---|---:|
| Attribution | 114 |
| Source splice | 56 |
| Identity | 68 |
| Shares | 70 |
| Terminal event | 16 |
| Split basis | 7 |
| Asset type | 2 |
| Non-US / venue | 1 |
| Fundamentals | 1 |
| **Total rejected** | **335** |

The panel is selected by source availability and research eligibility. It is not a reconstruction of CRSP, Compustat, the historical S&P 500, or the Russell 1000.

## 2. Factor Research

| Measure | Result |
|---|---:|
| Configured factor definitions | 48 |
| Estimable definitions | 47 |
| Non-estimable definition | `equity_issuance` |
| Long-form factor rows | 34,341,456 |
| Factor-portfolio observations | 11,545 |
| Factor sample | 2018-02-14 to 2026-08-04 |

`equity_issuance` remains non-estimable because the required issuance and shareholders' equity inputs cannot be reconciled consistently from the accepted point-in-time SEC evidence without unsupported imputation.

## 3. Asset-Pricing Results

Each configured model is evaluated on 123 diagnostic portfolios. Intercept inference uses the released HAC/Newey-West covariance. The p<0.05 share below is descriptive and unadjusted; it is not a multiple-testing decision rule.

| Model | N | Mean adj. R² | Median adj. R² | Mean monthly alpha | Median monthly alpha | Mean HAC t | p<0.05 share | Mean market beta |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| CAPM | 123 | 0.063 | 0.061 | 0.01187 | 0.01128 | 2.467 | 85.4% | 1.402 |
| Fama-French 3 | 123 | 0.259 | 0.247 | 0.00923 | 0.00937 | 2.146 | 58.5% | 1.421 |
| Carhart 4 | 123 | 0.277 | 0.261 | 0.00899 | 0.00910 | 2.048 | 52.8% | 1.408 |
| Fama-French 5 | 123 | 0.301 | 0.281 | 0.01056 | 0.01026 | 2.569 | 92.7% | 1.284 |
| Configured q mapping | 123 | 0.296 | 0.295 | 0.00875 | 0.00876 | 2.090 | 58.5% | 1.291 |

Fama-French 5 exceeds CAPM by 0.238 in mean adjusted R² (0.301 - 0.063). This supports greater in-sample explanatory fit, not persistent alpha, causality, or future performance.

## 4. Portfolio, Cost and Risk Results

Eight long-only, fully invested, unlevered methods are evaluated over the factor-portfolio window from 2024-01-31 to 2026-08-04.

### Transaction-cost assumptions

| Component | LOW | BASE | HIGH |
|---|---:|---:|---:|
| Commission | 0 bps | 0 bps | 0 bps |
| Spread | 2 bps | 5 bps | 10 bps |
| Slippage | 1 bps | 2 bps | 4 bps |
| Fixed-impact allowance | 2 bps | 3 bps | 6 bps |
| **Total one-way cost** | **5 bps** | **10 bps** | **20 bps** |

These are ex-ante sensitivity assumptions, not observed broker executions. Nonlinear market impact is not independently estimated.

### BASE performance

| Method | Annualized net return | Volatility | Sharpe | Maximum drawdown | Net cumulative return |
|---|---:|---:|---:|---:|---:|
| Equal Weight | 16.10% | 11.14% | 1.383 | -8.57% | 48.89% |
| Minimum Variance | 13.95% | 10.00% | 1.341 | -6.69% | 41.64% |
| Mean Variance | 12.72% | 16.04% | 0.818 | -17.81% | 37.60% |
| Maximum Sharpe | 20.55% | 12.30% | 1.575 | -7.51% | 64.61% |
| Maximum Diversification | 17.31% | 10.97% | 1.499 | -5.43% | 53.08% |
| Risk Parity | 15.76% | 10.79% | 1.397 | -8.33% | 47.72% |
| Hierarchical Risk Parity | 15.48% | 10.56% | 1.403 | -8.13% | 46.79% |
| CVaR | 25.48% | 14.21% | 1.667 | -8.55% | 83.17% |

### Cumulative-return cost sensitivity

| Method | Gross | LOW net | BASE net | HIGH net |
|---|---:|---:|---:|---:|
| Equal Weight | 49.12% | 49.01% | 48.89% | 48.66% |
| Minimum Variance | 42.96% | 42.30% | 41.64% | 40.34% |
| Mean Variance | 41.45% | 39.52% | 37.60% | 33.85% |
| Maximum Sharpe | 66.66% | 65.63% | 64.61% | 62.59% |
| Maximum Diversification | 54.13% | 53.60% | 53.08% | 52.03% |
| Risk Parity | 47.98% | 47.85% | 47.72% | 47.47% |
| Hierarchical Risk Parity | 47.42% | 47.10% | 46.79% | 46.17% |
| CVaR | 84.30% | 83.73% | 83.17% | 82.06% |

Higher costs reduce every cumulative result.

### BASE risk metrics

| Method | Net cum. | Gross cum. | Vol. | Sharpe | Sortino | MDD | VaR95 | CVaR95 | Tracking error | Information ratio | Beta |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Equal Weight | 48.89% | 49.12% | 11.14% | 1.383 | 2.441 | -8.57% | 4.92% | 5.38% | 5.20% | -0.850 | 0.833 |
| Minimum Variance | 41.64% | 42.96% | 10.00% | 1.341 | 2.136 | -6.69% | 4.55% | 6.09% | 10.03% | -0.641 | 0.498 |
| Mean Variance | 37.60% | 41.45% | 16.04% | 0.818 | 1.153 | -17.81% | 4.53% | 10.65% | 13.55% | -0.495 | 0.753 |
| Maximum Sharpe | 64.61% | 66.66% | 12.30% | 1.575 | 2.967 | -7.51% | 4.65% | 5.85% | 10.67% | -0.044 | 0.628 |
| Maximum Diversification | 53.08% | 54.13% | 10.97% | 1.499 | 2.935 | -5.43% | 4.28% | 4.94% | 9.30% | -0.364 | 0.616 |
| Risk Parity | 47.72% | 47.98% | 10.79% | 1.397 | 2.408 | -8.33% | 4.89% | 5.39% | 5.41% | -0.879 | 0.799 |
| Hierarchical Risk Parity | 46.79% | 47.42% | 10.56% | 1.403 | 2.382 | -8.13% | 4.84% | 5.43% | 5.68% | -0.884 | 0.772 |
| CVaR | 83.17% | 84.30% | 14.21% | 1.667 | 3.163 | -8.55% | 5.05% | 7.58% | 12.90% | 0.298 | 0.622 |

VaR95 and CVaR95 are positive loss magnitudes under the project loss convention. Maximum drawdown is negative peak-to-trough return.

### Scenario mappings

| Scenario family | Instantaneous impact |
|---|---:|
| Market | -0.244% |
| Rates | -0.073% |
| Volatility | -0.122% |
| Inflation | -0.061% |
| Liquidity | -0.037% |

A sixth project-specific custom mapping exists in the frozen empirical output, but it is not given a generic interpretation because its shock definition is not stated in this public numerical record. Scenario impacts are sensitivity mappings, not forecasts.

## 5. Walk-Forward Machine Learning

### Design

| Item | Setting |
|---|---|
| Features | Book-to-market; 12-minus-1 momentum |
| Target | 21-trading-session security return minus SPY return |
| Decision frequency | Monthly |
| Training window | 60 months |
| Validation window | 12 months |
| Test window | 1 month |
| Purging | Overlapping label horizons removed |
| Embargo | 1 month |
| Retraining | Monthly |
| Decision observations | 27,640 |
| Monthly dates | 91 |
| Complete OOS folds | 17 |
| OOS fold period | 2025-02-28 to 2026-06-30 |
| Bootstrap | 1,000 resamples; 95% intervals; seed 17 |

Eight rows are evaluated: zero baseline, historical mean, factor composite, linear, Ridge, Elastic Net, Random Forest, and XGBoost. Constant predictions have undefined rank correlation, so the two constant baselines report IC as N/A rather than zero.

### Predictive results

| Model | Mean IC | 95% bootstrap CI | Positive IC folds | Positive rate |
|---|---:|---:|---:|---:|
| Zero baseline | N/A | N/A | N/A | N/A |
| Historical mean | N/A | N/A | N/A | N/A |
| Factor composite | 0.017412 | [-0.026401, 0.110608] | 10/17 | 58.8% |
| Linear | 0.017412 | [-0.026401, 0.110608] | 10/17 | 58.8% |
| Ridge | 0.017414 | [-0.026410, 0.110637] | 10/17 | 58.8% |
| Elastic Net | 0.027535 | [-0.024701, 0.151649] | 11/17 | 64.7% |
| Random Forest | 0.009558 | [-0.074074, 0.131357] | 10/17 | 58.8% |
| XGBoost | -0.009069 | [-0.049268, 0.055085] | 8/17 | 47.1% |

Every non-constant model interval includes zero; stable predictive information is not established.

### After-cost economic fold results

| Model | Mean net fold return | Median net fold return | Positive economic folds |
|---|---:|---:|---:|
| Zero baseline | -0.1415% | -0.1376% | 8/17 |
| Historical mean | -0.1415% | -0.1376% | 8/17 |
| Factor composite | -0.0973% | -0.0849% | 7/17 |
| Linear | -0.0973% | -0.0849% | 7/17 |
| Ridge | -0.0973% | -0.0849% | 7/17 |
| Elastic Net | -0.1039% | -0.0333% | 7/17 |
| Random Forest | +0.0074% | +0.0942% | 9/17 |
| XGBoost | -0.0044% | +0.1838% | 11/17 |

Random Forest has a small positive mean and 9 positive folds, while XGBoost has a positive median but a negative mean. Neither pattern establishes stable after-cost incremental value.

Feature-attribution rankings also vary across methods. Coefficients, permutation importance, and SHAP summaries are model diagnostics, not causal estimates.

## 6. Hypothesis Outcomes

| Hypothesis | Classification | Basis |
|---|---|---|
| H1 | Inconclusive | Complete factor-level cost and multiplicity decision is not persisted |
| H2 | Partially supported | Multifactor models improve in-sample adjusted R²; stable out-of-sample economic improvement is not established |
| H3 | Inconclusive | Rolling evidence exists, but the complete original temporal-stability decision is absent |
| H4 | Supported | Every higher cost setting reduces cumulative results |
| H5 | Partially supported | Methods alter observed risk-return profiles; durable superiority is not established |
| H6 | Not supported | All non-constant IC intervals include zero and economic gains are unstable |
| H7 | Not supported | Attribution rankings vary across methods and are noncausal |

## 7. Software Validation

The current verified repository release records:

- 301 passing tests;
- 90.52% branch-aware coverage;
- Ruff lint and formatting checks;
- strict Mypy checks;
- dependency-lock verification;
- catalog/delivery validation;
- Docker build verification;
- dependency vulnerability audit.

These checks support software correctness and reproducibility. They are not empirical evidence of investment performance.

## 8. Overall Conclusion

The evidence supports a mixed conclusion:

- the selected public-data panel supports broad point-in-time characteristic construction, subject to source-selection and early-breadth limitations;
- multifactor specifications provide greater in-sample explanatory fit than CAPM on the project diagnostic portfolios;
- portfolio methods materially alter observed risk and return characteristics;
- higher assumed transaction costs reduce every cumulative portfolio result;
- stable factor significance under H1 and temporal stability under H3 are not established under the original rules;
- the current ML experiment does not establish stable predictive information or stable after-cost incremental value.

The repository therefore reports bounded empirical evidence rather than a persistent-alpha claim.
