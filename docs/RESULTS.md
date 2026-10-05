# Research Results

This document provides the compact numerical record for the current public research release. Numerical claims in the README are intended to match this file and the public research manuscript.

## 1. Universe and Data

| Measure | Result |
|---|---:|
| Candidate securities screened | 822 |
| Accepted securities | 487 |
| Rejected securities | 335 |
| Tier A accepted | 372 |
| Tier B accepted | 115 |
| Daily market observations | 715,447 |
| Market sample | 2018-02-14 to 2026-08-04 |
| Point-in-time fundamental observations | 37,273 |
| Fundamental availability sample | 2019-02-23 to 2026-08-15 |
| Fundamental fields | 18 |

The panel is selected by source availability and research eligibility. It is not a reconstruction of CRSP, Compustat, the historical S&P 500, or the Russell 1000.

## 2. Factor Research

| Measure | Result |
|---|---:|
| Configured factor definitions | 48 |
| Estimable definitions | 47 |
| Long-form factor rows | 34,341,456 |
| Factor-portfolio rows | 11,545 |

`equity_issuance` is the only configured characteristic that remains non-estimable. The available point-in-time SEC inputs do not support a consistent calculation without unsupported imputation, so the missing factor is not replaced with zero.

## 3. Asset-Pricing Results

Each configured model is evaluated on 123 project diagnostic portfolios.

| Model | Mean adjusted R² |
|---|---:|
| CAPM | 0.063 |
| Fama-French 3 | 0.259 |
| Carhart 4 | 0.277 |
| Fama-French 5 | 0.301 |
| Configured q mapping | 0.296 |

Mean monthly intercepts across the model families range from 0.00875 to 0.01187.

### Interpretation

The multifactor models explain substantially more in-sample variation than CAPM on the project portfolios. The highest mean adjusted R² is observed for Fama-French 5. These are descriptive in-sample model-comparison results, not proof of persistent alpha or causal factor effects.

## 4. Portfolio Results

Eight long-only, fully invested, unlevered methods are evaluated:

1. Equal Weight
2. Minimum Variance
3. Mean Variance
4. Maximum Sharpe
5. Maximum Diversification
6. Risk Parity
7. Hierarchical Risk Parity
8. CVaR

The one-way transaction-cost assumptions are:

| Cost case | Assumption |
|---|---:|
| LOW | 5 bps |
| BASE | 10 bps |
| HIGH | 20 bps |

The available factor-portfolio evaluation window is approximately 32 months.

Across the eight BASE portfolio publications:

| Metric | Observed range |
|---|---:|
| Annualized net return | 12.72% to 25.48% |
| Annualized volatility | 10.00% to 16.04% |
| Net cumulative return | 37.60% to 83.17% |

Selected outcomes:

| Method | Observed result |
|---|---:|
| Minimum Variance | Lowest annualized volatility: 10.00% |
| Maximum Diversification | Smallest maximum drawdown: -5.43% |
| Maximum Sharpe | Sharpe ratio: 1.575 |
| CVaR | Highest cumulative return: 83.17%; Sharpe ratio: 1.667; information ratio: 0.299 |

### Cost Sensitivity

Higher transaction costs reduce cumulative performance for every method.

Examples:

| Method | LOW | BASE | HIGH |
|---|---:|---:|---:|
| CVaR cumulative return | 83.73% | 83.17% | 82.06% |
| Mean Variance cumulative return | 39.52% | 37.60% | 33.85% |

### Interpretation

Portfolio construction materially changes volatility, drawdown, concentration, tracking, and return outcomes. CVaR leads observed cumulative return in this sample, while other methods lead on different risk measures. The short window does not support a claim that one allocator is persistently superior.

## 5. Walk-Forward Machine-Learning Results

### Design

| Item | Setting |
|---|---|
| Features | Book-to-market; 12-minus-1 momentum |
| Target | 21-session security return minus SPY return |
| Decision frequency | Monthly |
| Training window | 60 months |
| Validation window | 12 months |
| Test window | 1 month |
| Purging | Yes |
| Embargo | 1 month |
| Retraining | Monthly |
| Complete OOS folds | 17 |
| Decision observations | 27,640 |
| Monthly dates | 91 |

The eight models are zero baseline, historical-mean baseline, factor composite, linear regression, Ridge, Elastic Net, Random Forest, and XGBoost.

### Predictive Results

Mean fold Spearman IC for selected models:

| Model | Mean fold Spearman IC |
|---|---:|
| Linear | ~0.0174 |
| Ridge | ~0.0174 |
| Elastic Net | ~0.0275 |
| Random Forest | ~0.0096 |
| XGBoost | ~-0.0091 |

Every aggregate bootstrap IC confidence interval for the non-constant models includes zero.

### Economic Results

At the 10 bps cost setting, mean fold economic return is negative for every method except Random Forest. Random Forest's mean is approximately +0.0074%, and it is positive in 9 of 17 folds.

### Interpretation

The evidence does not establish stable incremental predictive information or stable after-cost economic value from the ML models. The negative result is retained rather than selecting a model based on a favorable subset of folds.

Feature rankings also vary across models and explanation methods, so no stable or causal feature-importance claim is made.

## 6. Hypothesis Outcomes

| Hypothesis | Outcome | Interpretation |
|---|---|---|
| H1 | Inconclusive | The factor publication does not provide the complete net-cost/multiple-testing decision needed for the original directional-spread claim |
| H2 | Partially supported | Multifactor models improve in-sample explanatory fit; stable OOS economic improvement is not established |
| H3 | Inconclusive | Rolling evidence exists, but the complete corrected regime/break decision is unavailable |
| H4 | Supported | Higher frozen transaction costs reduce every portfolio's net result |
| H5 | Partially supported | Portfolio methods show different risk and concentration trade-offs; persistent superiority is not established |
| H6 | Not supported | ML IC intervals include zero and after-cost gains are not stable across folds |
| H7 | Not supported | Feature rankings vary by model and explanation method |

## 7. Software Validation

The research release passed:

- 301 tests;
- 90.52% branch-aware coverage;
- Ruff formatting and lint checks;
- strict Mypy checks;
- dependency-lock verification;
- catalog and delivery checks.

These checks validate software behavior and reproducibility controls. They do not substitute for statistical or economic evidence.

## 8. Overall Conclusion

The main empirical conclusions are:

- a large point-in-time public-data research panel can be constructed, but source-selection limitations remain;
- multifactor models provide greater in-sample explanatory fit than CAPM on the project portfolios;
- transaction costs materially reduce portfolio results;
- different constrained allocators produce different risk-return trade-offs;
- the current ML experiment does not establish stable incremental predictive or after-cost value.

The project therefore supports a mixed research conclusion rather than a persistent-alpha claim.
