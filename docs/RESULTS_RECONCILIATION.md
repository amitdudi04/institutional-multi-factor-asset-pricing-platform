# Results Reconciliation and Reviewer Notes

**Status: historical result tables preserved; corrected empirical outputs have not been regenerated.**

This repository's README and docs/RESULTS.md contain the prior empirical release. The audit branch corrects calculation logic in asset-pricing inputs, portfolio risk metrics and ML baseline handling, but the required raw provider data are not present in Git. Therefore, historical numerical values are retained as a record of what was previously reported; they must not be described as outputs from the corrected implementation.

## Source-of-truth rules

- docs/RESULTS.md is the detailed record of the prior reported tables.
- The README contains a concise summary of those same historical findings.
- The old release identifiers in docs/REPRODUCIBILITY.md identify the historical empirical state, not the current corrected calculations.
- No numerical result should be replaced until the data-backed pipeline is rerun with documented source inputs and output manifests.
- A software test passing verifies the tested software behavior; it does not independently validate a historical empirical table.

## Findings and reviewer-facing notes

| Area | Historical reported result | Challenge / interpretation note | Status |
|---|---|---|---|
| Universe | 822 screened; 487 accepted; 335 rejected | Source-availability-selected sample; not a reconstruction of CRSP, Compustat, the historical S&P 500 or Russell 1000. | Historical counts; data-backed rerun pending |
| Factors | 48 defined; 47 estimable | equity_issuance remains non-estimable rather than being imputed without evidence. Factor definitions are project characteristics, not all canonical academic factors. | Historical counts; definitions documented |
| Asset pricing | Adjusted R²: CAPM 0.063; FF5-style project model 0.301 | The 0.238 difference is an in-sample fit difference, not proof of causal pricing, persistent alpha or future returns. Factor returns and risk-free returns were corrected on the audit branch, so the old values require recalculation. | Not validated under corrected calculations |
| Alpha inference | Mean monthly alpha and unadjusted p<0.05 shares reported for 123 diagnostic portfolios per model | High significance shares, including 85.4% for CAPM and 92.7% for the FF5-style project model, should not be interpreted as multiplicity-adjusted discoveries. The released p<0.05 share is explicitly descriptive and unadjusted. | Historical; full correction rerun pending |
| Portfolio performance | CVaR cumulative net return 83.17%, Sharpe 1.667; Maximum Sharpe Sharpe 1.575 | The factor-portfolio evaluation spans about 32 months. These are sample-specific backtest results under modeled costs, not evidence of persistent superiority or measured real-world execution performance. | Historical; not a live or validated forecast |
| Cost sensitivity | 5, 10 and 20 bps one-way assumptions; higher cost lowers each cumulative result | These are ex-ante assumptions, not broker fills. Nonlinear market impact, taxes, financing, borrow constraints and capacity are not independently estimated. | Historical sensitivity analysis |
| ML predictive IC | Every non-constant model's reported aggregate bootstrap interval includes zero | The previous release does not establish stable predictive information. Linear and factor-composite summaries are identical to displayed precision, and Ridge is nearly identical; this may be legitimate but should be checked against model-level prediction artifacts on a future data-backed rerun rather than treated as independent confirmation. | Historical; rerun pending |
| ML economic results | Random Forest mean net fold return +0.0074%, positive in 9/17 folds; XGBoost mean -0.0044%, positive in 11/17 folds | Mixed fold outcomes and small samples do not establish stable after-cost incremental value. The README's negative/inconclusive conclusion is appropriately cautious. | Historical; no stable value established |
| Hypotheses | H1 and H3 inconclusive; H2 and H5 partially supported; H6/H7 not supported | H1's complete factor-level cost/multiplicity decision and H3's full original temporal-stability decision are not persisted. Do not upgrade these classifications without recovering the pre-specified decision rules. | Decision evidence incomplete |
| Software validation | Previous release: 301 tests, 90.52% branch-aware coverage | These are historical software-validation figures. They do not certify that the corrected empirical tables have been regenerated. Current branch CI/test status should be reported separately from historical release metrics. | Historical software record |

## Calculation changes that require result regeneration

The audit branch documents and tests corrections involving:

1. aligning portfolio holding-period returns with market and risk-free inputs over the same formation-to-realization interval;
2. compounding daily risk-free returns to the matching holding period;
3. computing Jensen's alpha from portfolio and market excess returns;
4. avoiding row-order-based selection when an ML baseline emits a constant score;
5. aligning risk metrics with the intended return interval and definitions.

The direction or size of the effect on historical tables cannot be inferred safely without rerunning the pipeline. Do not assume every historical number moves in a particular direction.

## Reviewer-facing conclusion

The prior empirical release contains useful descriptive results, but the audit branch changes calculation logic that affects downstream results. Until lawful source data are restored or reacquired and the full dependency pipeline is rerun, the correct claim is: **the repository documents the prior empirical release and contains tested calculation corrections; the corrected empirical findings remain pending regeneration.**

No result values in docs/RESULTS.md are silently replaced by estimates or manually adjusted to agree with an expected narrative.
