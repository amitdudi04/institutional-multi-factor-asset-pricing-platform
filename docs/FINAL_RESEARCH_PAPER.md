# Final Local Empirical Study

## Abstract

This preregistered local study screened all 822 HF Data Library stock candidates before analytical performance was examined and froze 487 defensibly bounded US equities (372 Tier A, 115 Tier B). The authenticated panel contains 715,447 daily market rows and 37,273 point-in-time fundamental rows. It supports 47 of 48 configured factors, five configured asset-pricing model families, eight long-only portfolio methods under a frozen transaction-cost schedule, and eight walk-forward machine-learning challengers. Results are research evidence, not investment advice, a trading recommendation, or proprietary-data equivalence.

## Data and universe

The admission waterfall required HF attribution and source-transition integrity, Alpha lifecycle evidence, exact SEC ticker/CIK evidence, tagged annual filing covers, point-in-time shares, governed US-GAAP concepts, and bounded identity intervals. Present identity, shares, or names were never backfilled historically. Final dispositions were 487 accepted and 335 rejected: 114 attribution, 56 splice, 68 identity, 70 shares, 16 unresolved terminal event, 7 split basis, 2 asset type, 1 venue/non-US, and 1 fundamental projection. Detailed source evidence remains in ignored local runtime storage.

Daily breadth has minimum 1, median 428, mean 336.206, and maximum 487. Monthly breadth has minimum 3, median 428, mean 339, and maximum 487. The source-availability-selected panel is not CRSP/Compustat or historical-index replication.

## Phase 2 factor evidence

Publication `factor-5a73616f131fca2102fa2ca4141ad64f` contains 34,341,456 factor rows, 11,545 portfolio rows, and all 48 configured definitions. Forty-seven are estimable. `equity_issuance` has zero observations and remains `NOT ESTIMABLE FROM DEFENSIBLE INPUTS`: the governed SEC registry does not permit fabrication or zero-filling of the required issuance and equity inputs. A corrected benchmark-calendar implementation reconciles cross-portfolio benchmark compounds to `8.33e-17`, numeric roundoff.

## Phase 3 asset-pricing evidence

Publication `asset-pricing-c0a72fae5349f1048e18557250da1927` covers 123 diagnostic portfolios per configured model. Mean adjusted R-squared is 0.063 for CAPM, 0.259 for Fama-French 3, 0.277 for Carhart 4, 0.301 for Fama-French 5, and 0.296 for the configured q mapping. Mean monthly intercepts range from 0.00875 to 0.01187. These are descriptive in-sample estimates on project-specific diagnostic portfolios, not causal alpha or deployable performance. No custom model was estimated because no custom equation is approved or configured.

## Phase 4 portfolio evidence

The cost schedule was frozen before portfolio performance was read. One-way LOW, BASE, and HIGH totals are 5, 10, and 20 basis points. The engine represents BASE as 5 bps half-spread plus 5 bps slippage/fixed-impact allowance; nonlinear impact is zero because no authenticated liquidity input exists. This preserves the approved total without fabricating liquidity.

All eight configured methods produced authenticated BASE publications: equal weight, minimum variance, mean variance, maximum Sharpe, maximum diversification, risk parity, hierarchical risk parity, and CVaR. Over the available 32-month test window, annualized BASE net returns range from 12.72% to 25.48%, annualized volatility from 10.00% to 16.04%, and net cumulative return from 37.60% to 83.17%. The CVaR method has the highest observed net cumulative return and information ratio (0.299), while minimum variance has the lowest volatility. These short-window, factor-portfolio results are descriptive and do not establish persistence.

Cost sensitivity is monotonic for every method. For example, CVaR net cumulative return declines from 83.73% at LOW to 83.17% at BASE and 82.06% at HIGH; mean variance declines from 39.52% to 37.60% and 33.85%. The scenario publication covers market, rates, volatility, inflation, liquidity, and custom families; instantaneous impacts range from -0.244% to +0.024%. Scenarios are exposure mappings, not forecasts. Black-Litterman/Bayesian components exist as domain frameworks but are not configured standalone authenticated Phase 4 publication methods and were not claimed as estimated.

## Phase 5 machine-learning evidence

The frozen design binds the corrected Phase 2 and Phase 3 publications and BASE equal-weight Phase 4 publication. It uses only book-to-market and 12-minus-1 momentum, a 21-trading-session future excess-return target over SPY, monthly decisions, 60-month training, 12-month validation, one-month tests, purging, a one-month embargo, seed 17, and single-thread execution. The real decision dataset contains 27,640 rows across 91 months; each model completes 17 folds.

The eight authenticated models are zero and historical-mean baselines, factor composite, linear, ridge, elastic net, Random Forest, and XGBoost. Mean fold Spearman IC is approximately 0.0174 for linear/ridge, 0.0275 for elastic net, 0.0096 for Random Forest, and -0.0091 for XGBoost. Every aggregate bootstrap IC interval includes zero. After 10 bps costs, mean fold economic return is negative for every method except Random Forest, whose +0.0074% is economically tiny and positive in only 9 of 17 folds. Stable incremental predictive or economic value is therefore not established.

Coefficient, permutation, and SHAP evidence is non-causal. Linear-family models rank book-to-market above momentum. Random Forest permutation ranks book-to-market first while SHAP ranks momentum first; XGBoost ranks book-to-market first under both. This variation prevents a claim of stable cross-method explanation.

## Preregistered hypothesis assessment

| Hypothesis | Conclusion | Evidence |
|---|---|---|
| H1 | `INCONCLUSIVE` | 47 factors are estimable, but the configured factor publication does not provide a complete preregistered net-cost/FDR decision for “at least one” directional spread. |
| H2 | `PARTIALLY SUPPORTED` | Multifactor adjusted R-squared exceeds CAPM in-sample; stable OOS economic improvement is not established. |
| H3 | `INCONCLUSIVE` | Rolling evidence exists, but a complete corrected regime/break multiplicity decision was not produced. |
| H4 | `SUPPORTED` | Higher frozen costs reduce every portfolio's net return and materially reduce turnover-heavy results. |
| H5 | `PARTIALLY SUPPORTED` | Constrained methods produce different volatility, drawdown, concentration, and tracking trade-offs, but superiority is not stable over a sufficiently long OOS period. |
| H6 | `NOT SUPPORTED` | IC confidence intervals include zero and after-cost gains are not stable across folds. |
| H7 | `NOT SUPPORTED` | Feature rankings vary by model and explanation method; no causal claim is made. |

## Conclusion

The local free/public-data chain is empirically complete for the configured Phase 1-6 scope and closes the Phase 7 research questions with explicit uncertainty. It demonstrates authenticated, temporally controlled research and exposes limited evidence for investment performance: model fit improves in-sample, costs matter, and ML does not show stable incremental value. The honest result is a completed study with mostly inconclusive or negative investment hypotheses, not a promise of alpha.
