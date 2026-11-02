# Research Results

This is the corrected current numerical summary. Numerical authority: [accepted correction commit f22f5cb](https://github.com/amitdudi04/institutional-multi-factor-asset-pricing-platform/tree/f22f5cbe365e98c8d5fef6b5308ff765703df173/outputs/audit), with the [Phase 3 reconciliation](https://github.com/amitdudi04/institutional-multi-factor-asset-pricing-platform/tree/f22f5cbe365e98c8d5fef6b5308ff765703df173/outputs/audit/phase3/PHASE3_COMPLETE_VALIDATION.md) and [Phase 2C matched-sample checks](https://github.com/amitdudi04/institutional-multi-factor-asset-pricing-platform/tree/f22f5cbe365e98c8d5fef6b5308ff765703df173/outputs/audit/phase2c/PHASE2C_REGRESSION_VERIFICATION.md). The [final documentation candidate](https://github.com/amitdudi04/institutional-multi-factor-asset-pricing-platform/tree/research/institutional-final-documentation-corrections) is a research branch; corrected claims do not describe unmerged historical `main`. Historical original results remain preserved in [the Phase 4 baseline version](https://github.com/amitdudi04/institutional-multi-factor-asset-pricing-platform/blob/7726cec06fc75ea0a1858842d0f6a761c162fe12/docs/RESULTS.md), explicitly separate from the current tables.

## 1. Universe and Data

| Measure | Result |
|---|---:|
| Candidate securities screened | 822 |
| Accepted securities | 487 (59.25%) |
| Rejected securities | 335 (40.75%) |
| Daily market observations | 715,447 |
| Market sample | 2018-02-14 to 2026-08-04 |
| SEC-derived fundamental observations | 37,273; recorded availability, exhaustive capture chronology unresolved |
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

| Measure | Corrected result |
|---|---:|
| Configured names | 48 |
| Definitions with nonmissing raw values | 47 |
| Non-estimable definition | `equity_issuance` |
| Physical long-form rows | 34,341,456 |
| Nonmissing raw observations | 28,550,589 |
| Nonmissing scores | 24,255,559 |
| Quantile characteristics | 41 |
| Dependent portfolio IDs | 123 |
| Complete quantile-cycle rows | 11,352 |
| Singleton quantile-cycle observations | 956 / 11,352 |

Counts have different denominators; 48 names are not independent exposures. Singleton rows are single-stock quantile exposures, not diversified portfolios or 956 unique securities. The corrected factor publication is `factor-4ddee9ac6fb45cedfd62a2cc68676b58`. Its delayed-close endpoint experiment replaces the historical original 11,545 rows; 195 of 265 flagged historical groups have valid interior-gap chains, while 70 lack old intended endpoints. Those unavailable observations are not claimed repaired. `equity_issuance` remains missing rather than imputed.

## 3. Asset-Pricing Results

| Model | Mean adjusted R² | Alpha (decimal return per full trading cycle) | Nominal HAC p < 0.05 |
|---|---:|---:|---:|
| CAPM | 0.760818 | -0.001658 | 8/123 |
| Fama-French 3 | 0.802438 | -0.001967 | 12/123 |
| Carhart 4 | 0.811021 | -0.001879 | 14/123 |
| Fama-French 5 | 0.817658 | -0.002008 | 8/123 |
| Study-specific q-style | 0.814361 | -0.002227 | 9/123 |

All five models use 123 dependent portfolios with matched per-asset observations: 67–77 cycles per asset, 9,441 asset-cycle observations per model and 615 primary fits. OLS with three-lag Newey–West HAC is retained. No intercept survives supplementary Holm adjustment. Negative mean alpha and high fit can coexist; non-rejection is not proof of zero true alpha or market efficiency.

Factors are internal proxies, not official FF/HXZ reproductions; earnings yield is not accounting ROE. Shared constituents, correlated residuals and six duplicate return-series pairs preclude treating 123 portfolios as independent assets. The accepted 109-asset constituent-exclusion sensitivity excludes 14 assets. On 67 all-asset common dates, the centered residual matrix has rank 66 for 123 columns; covariance is singular. A full conventional inverse-covariance GRS test is not available or claimed. No new joint test or external-factor experiment was added.

## 4. Portfolio, Cost and Risk Results

Eight methods allocate to 123 constructed long-only quantile sleeves over 31 complete monthly cycles, exit labels 2024-02-01 through 2026-08-03. The 36-cycle training history, constraints and objectives are unchanged. Prior array rows feed decisions, but actual historical pre-close information and executable fills remain unverified.

### Modeled transaction costs

Rates are bps per absolute-traded-weight unit. L1 = sum of absolute target-minus-pretrade weights; half-L1 is one-way turnover. Initial cash deployment has L1 = 1; a complete invested switch has L1 = 2.

| Component | LOW | BASE | HIGH |
|---|---:|---:|---:|
| Full quoted spread (not charged in full) | 4 | 10 | 20 |
| Charged half-spread | 2 | 5 | 10 |
| Slippage component | 1 | 2 | 4 |
| Fixed allowance bundled in total slippage | 2 | 3 | 6 |
| Commission | 0 | 0 | 0 |
| Total charged rate | 5 | 10 | 20 |

These are assumptions, not order-book calibration. Outer-sleeve fees are validated; constituent execution, financing, capacity and full market impact remain omitted or unverified. Net cycle return is gross less modeled fees. Performance cash is compounded over the exact holding interval.

### Corrected BASE performance

| Method | Annualized geometric net return (%) | Annualized volatility (%) | Sharpe ratio | Maximum drawdown (%) | Cumulative net return (%) |
|---|---:|---:|---:|---:|---:|
| Equal Weight | 15.8726% | 10.7432% | 1.023067 | -8.2915% | 46.3133% |
| Minimum Variance | 15.4976% | 9.9505% | 1.065607 | -6.4993% | 45.0930% |
| Mean Variance | 10.4507% | 14.6465% | 0.455591 | -16.1138% | 29.2761% |
| Maximum Sharpe | 21.8340% | 12.0472% | 1.346360 | -6.1601% | 66.5591% |
| Maximum Diversification | 19.6363% | 10.6378% | 1.334355 | -4.8279% | 58.9082% |
| Risk Parity | 15.5997% | 10.4332% | 1.027799 | -7.9894% | 45.4247% |
| Hierarchical Risk Parity | 15.1108% | 10.1920% | 1.008019 | -7.7200% | 43.8413% |
| CVaR | 23.8256% | 14.4950% | 1.252327 | -7.0821% | 73.6842% |

Annualized net return is geometric, `(ending wealth)^(12/31) - 1`, not 12 times the arithmetic cycle mean. Volatility uses sample SD times sqrt(12); Sharpe uses mean interval-matched excess return divided by its SD, times sqrt(12). Cumulative net return compounds the actual 31-cycle net path from NAV = 1.

### Corrected cumulative fee sensitivity

| Method | Gross (%) | LOW net (%) | BASE net (%) | HIGH net (%) |
|---|---:|---:|---:|---:|
| Equal Weight | 46.5311% | 46.4222% | 46.3133% | 46.0958% |
| Minimum Variance | 46.3406% | 45.7155% | 45.0930% | 43.8555% |
| Mean Variance | 32.8133% | 31.0333% | 29.2761% | 25.8288% |
| Maximum Sharpe | 68.7003% | 67.6265% | 66.5591% | 64.4435% |
| Maximum Diversification | 60.1584% | 59.5321% | 58.9082% | 57.6673% |
| Risk Parity | 45.6739% | 45.5492% | 45.4247% | 45.1758% |
| Hierarchical Risk Parity | 44.4303% | 44.1355% | 43.8413% | 43.2544% |
| CVaR | 74.8292% | 74.2559% | 73.6842% | 72.5457% |

All 24 scenario identities are retained in the Phase 3 source manifest. Within a method, scenario weights are identical and larger costs mechanically reduce wealth; this is not empirical execution calibration.

### Corrected cycle loss measures

| Method | VaR 95% (monthly-cycle positive loss, decimal) | ES 95% (monthly-cycle positive loss, decimal) | Tail observations |
|---|---:|---:|---:|
| Equal Weight | 0.046573 | 0.052968 | 2 |
| Minimum Variance | 0.043372 | 0.058957 | 2 |
| Mean Variance | 0.050949 | 0.086623 | 2 |
| Maximum Sharpe | 0.048164 | 0.050826 | 2 |
| Maximum Diversification | 0.039148 | 0.047911 | 2 |
| Risk Parity | 0.046095 | 0.053231 | 2 |
| Hierarchical Risk Parity | 0.045725 | 0.053749 | 2 |
| CVaR | 0.049515 | 0.066329 | 2 |

VaR uses the interpolated 5th return percentile; ES is the inclusive below-threshold mean converted to a positive loss. Only two observations enter either historical 32-cycle or corrected 31-cycle tail. These unannualized descriptive estimates are not precise tail-risk calibration and differ from the CVaR optimizer's fractional 36-scenario tail.

**Historical original:** CVaR 83.1737% cumulative net / Sharpe 1.666657 and maximum-diversification drawdown -5.4323% reproduce on their old paths. **Current corrected:** CVaR 73.6842% / 1.252327; maximum-diversification drawdown -4.8279%. Cash alignment alone gives old-path CVaR Sharpe 1.378572. Remaining changes combine holding-input and sample changes, not an initial-NAV-only effect. Short-sample rankings are descriptive, with no established persistence. Obsolete scenario impacts and old-path-only risk cells remain in the linked historical record, not current tables.

## 5. Walk-Forward Machine Learning

The two features are book-to-market and 12-minus-1 momentum. Targets are security-minus-SPY proxy returns over 21 complete common market sessions. The panel has 27,632 rows, 89 common month ends, 15 completed dependent test folds and 7,286 held-out observations per family. Training expands from 60 to 74 months; validation has 12 months, one test month and the original one-month embargo at both boundaries. Purging partition overlaps does not eliminate test-test dependence: five of 14 adjacent corrected target pairs overlap. Tests run from 2025-04-30 to 2026-06-30.

Training-only transformations and recorded-day gates are verified; exhaustive SEC capture and same-close availability are not. Predictions are retrospective held-out reconstructions, not timestamped historical live forecasts. Factor composite and linear are the same LinearRegression estimator, not independent confirmations.

### Corrected forecast results

| Model | Mean IC (rank correlation) | Median IC | Exploratory 95% mean-IC interval |
|---|---:|---:|---|
| Zero baseline | Undefined | Undefined | Undefined |
| Historical mean | Undefined | Undefined | Undefined |
| Factor composite | 0.034430 | 0.016341 | [0.010731, 0.084270] |
| Linear | 0.034430 | 0.016341 | [0.010731, 0.084270] |
| Ridge | 0.034434 | 0.016336 | [0.010735, 0.084272] |
| Elastic Net | 0.044609 | 0.059116 | [0.016324, 0.096766] |
| Random Forest | -0.002641 | -0.011912 | [-0.017721, 0.015985] |
| XGBoost | -0.023285 | -0.041750 | [-0.038821, -0.005015] |

Intervals use 100 moving-block resamples, block length 3, seed 17. Only six named rows have finite IC intervals, including the duplicate linear/composite estimator; the two constant baselines are undefined. Linear-family intervals are nominally positive, RF crosses zero and XGBoost is nominally negative. Few dependent folds, multiple comparisons and a small resampling budget limit precision. These are exploratory intervals, not robust discoveries. Old linear predictions evaluated on the corrected test keys have IC 0.037238 versus corrected 0.034430, so the higher whole-sample IC is not isolated improvement.

### One-session economic checks

| Model | Mean net one-session return (%) | Positive economic folds |
|---|---:|---:|
| Zero baseline | -0.0604% | 7/15 |
| Historical mean | -0.0604% | 7/15 |
| Factor composite | 0.0559% | 7/15 |
| Linear | 0.0559% | 7/15 |
| Ridge | 0.0559% | 7/15 |
| Elastic Net | 0.0551% | 7/15 |
| Random Forest | 0.1410% | 8/15 |
| XGBoost | 0.1554% | 10/15 |

Each fold starts at unit NAV, resets to cash, selects the top-ranked 20% of equities with equal weights and holds for one subsequent common session, paying a 10-bps initial L1 fee. Full liquidation costs and a continuous capital chain are absent. These means are not a 21-session investment backtest or multi-year compounded wealth. Stable incremental after-cost economic value has not been established. SHAP/permutation importance use different targets/samples and remain noncausal diagnostics.

## 6. Hypothesis Outcomes

| Hypothesis | Classification | Basis |
|---|---|---|
| H1 | Inconclusive | Complete factor-level cost and multiplicity decision is not persisted |
| H2 | Partially supported | Multifactor models improve in-sample adjusted R²; stable out-of-sample economic improvement is not established |
| H3 | Inconclusive | Rolling evidence exists, but the complete original temporal-stability decision is absent |
| H4 | Supported within the fixed simulation | Higher costs mechanically reduce cumulative results at identical weights |
| H5 | Partially supported | Methods alter observed risk-return profiles; durable superiority is not established |
| H6 | Stable joint proposition unestablished | Some nominal positive forecast IC evidence exists, but stable incremental after-cost economic value is unestablished |
| H7 | Not supported | Attribution rankings vary across methods and are noncausal |

## 7. Software Validation

The accepted Phase 3 checkpoint recorded 372 passing full-suite tests, 90.62% coverage and 91 targeted tests. Its type, lint, format and lock checks passed. Those prior checks were not rerun for a documentation-only pass. Current document, table, equation, link and integrity checks are recorded separately in the final-correction evidence. Software assurance is not proof of complete PIT data, causality, dividend treatment or live investability. Historical original 301/90.52% assurance belongs to the archived release only.

## 8. Overall Conclusion

The evidence supports a mixed conclusion:

- the selected panel supports characteristic construction under recorded-day availability gates, with source selection, early breadth and unresolved historical capture/execution limitations;
- multifactor specifications provide greater in-sample explanatory fit than CAPM on the project diagnostic portfolios;
- portfolio methods materially alter observed risk and return characteristics;
- higher assumed transaction costs reduce every cumulative portfolio result;
- stable factor significance under H1 and temporal stability under H3 are not established under the original rules;
- the ML experiment has qualified nominal forecast evidence but does not establish stable predictability or stable incremental after-cost economic value.

The repository therefore reports bounded empirical evidence rather than a persistent-alpha claim.
