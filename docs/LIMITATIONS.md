# Limitations

The project is explicit about what the accepted corrected evidence can support. Numerical authority: [accepted correction commit f22f5cb](https://github.com/amitdudi04/institutional-multi-factor-asset-pricing-platform/tree/f22f5cbe365e98c8d5fef6b5308ff765703df173/outputs/audit), with the [Phase 3 reconciliation](https://github.com/amitdudi04/institutional-multi-factor-asset-pricing-platform/tree/f22f5cbe365e98c8d5fef6b5308ff765703df173/outputs/audit/phase3/PHASE3_COMPLETE_VALIDATION.md) and [Phase 2C matched-sample checks](https://github.com/amitdudi04/institutional-multi-factor-asset-pricing-platform/tree/f22f5cbe365e98c8d5fef6b5308ff765703df173/outputs/audit/phase2c/PHASE2C_REGRESSION_VERIFICATION.md). The [final documentation candidate](https://github.com/amitdudi04/institutional-multi-factor-asset-pricing-platform/tree/research/institutional-final-documentation-corrections) is a research branch; corrected claims do not describe unmerged historical `main`.

## Universe and Data

- Frozen provider-vintage adjusted-quote returns are preserved; dividend-inclusive total-return comparability is unverified (V1). Current provider files/documentation cannot certify the original vintage.

- The universe is selected by public-source availability and research screening rules; it is not a reconstruction of CRSP, Compustat, the historical S&P 500, or the Russell 1000.
- HF Data Library coverage creates survivorship and source-selection limitations, particularly in earlier periods.
- The PiTrading-to-IEX source transition limits direct comparability of historical volume and liquidity measures.
- Early cross-sectional coverage is sparse relative to later periods.
- Candidates with unresolved identity, terminal-event, source-splice, or share-basis evidence are excluded, which can create residual selection effects.

## Fundamentals

- SEC accounting concepts and reporting practices differ across issuers and time.
- Recorded-day availability gates and representative joins are verified, but exhaustive SEC acceptance/local-capture chronology and issuer/share-class attribution are not (D4/ML4).
- `equity_issuance` is not estimable from the currently accepted evidence.
- Multi-class issuers can remain non-estimable for share-based variables when exact class allocation is unavailable.

## Factor and Asset-Pricing Research

- Forty-eight names/47 nonmissing definitions/41 quantile characteristics are not independent exposures; 956 of 11,352 quantile-cycle rows are single-stock exposures.
- Six duplicate series, shared constituents and correlated residuals limit internal pricing fit. The 109-asset sensitivity has 14 attrition cases.
- The common residual matrix has 67 dates, 123 columns and centered rank 66; covariance is singular, so no full conventional GRS test or joint zero-alpha proof is claimed.
- q-style uses an earnings-yield proxy, not accounting ROE; official FF/HXZ or external-factor replication remains untested.

- Project characteristic portfolios are not claimed to be exact replications of every published academic factor construction.
- Higher adjusted R² in the multifactor regressions is an in-sample explanatory result, not evidence of causal pricing or future alpha.
- H1 remains inconclusive because the complete factor-level cost and multiplicity decision is not persisted.
- H3 remains inconclusive because rolling evidence exists but the complete original temporal-stability decision is absent.

## Portfolio Research

- The corrected portfolio evaluation has only 31 full monthly trading cycles; pricing uses different matched 67–77-cycle per-asset samples.
- Allocations use 123 synthetic long-only quantile sleeves. Outer modeled fees are validated; constituent execution, financing and capacity are not.
- Prior training array observations are verified, but original historical pre-close information/fills remain unverified (P8).
- Transaction costs are sensitivity assumptions rather than measured executions.
- Nonlinear market impact and capacity are not estimated because the required liquidity evidence is unavailable at the necessary standard.
- Observed ranking over a short sample does not establish persistent superiority of CVaR, maximum Sharpe, or any other allocator.

## Machine Learning

- The reported ML study uses only book-to-market and 12-minus-1 momentum.
- It has 27,632 rows, 89 common month ends, 15 dependent OOS folds and 7,286 held-out observations per family; five of 14 adjacent target pairs overlap.
- Linear-family mean-IC intervals are nominally positive, RF crosses zero and XGBoost is negative. The 100 block-resamples (block 3, seed 17), model multiplicity and dependence limit inference.
- Linear and factor composite are the same estimator. Predictions are retrospective, not authenticated live historical forecasts (ML5).
- Economic checks reset to cash and hold for one subsequent session, rather than the 21-session prediction horizon or continuous wealth.
- Stable after-cost incremental value is not established.
- Feature rankings vary across models and explanation methods.
- SHAP, permutation importance and coefficients are model diagnostics, not causal effects.

## Scenarios and Risk

- Scenario shocks are sensitivity mappings, not forecasts.
- Monthly-cycle positive-loss VaR/ES estimates use only two tail observations from either 31 corrected or 32 historical cycles; descriptive estimates are not reliable risk calibration.
- The project does not estimate live execution slippage, taxes, financing, borrow constraints, or strategy capacity.

## Software and Deployment

- The API and dashboard are research interfaces, not a production trading system.
- No brokerage, live order execution, streaming-market SLA, or fiduciary investment service is provided.
- Exact reproduction of the empirical study requires lawful access to the same third-party data that are not redistributed in Git.

These limitations bound the claims in the README and [RESULTS.md](RESULTS.md); they are not reasons to replace weak or inconclusive findings with stronger language.
