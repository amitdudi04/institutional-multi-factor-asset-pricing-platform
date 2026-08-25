# Project Case Study

## 1. Problem

Many equity-research prototypes begin with a clean panel and end with an attractive backtest. This project began earlier: could a reproducible US-equity research platform assemble defensible historical evidence, preserve what was knowable at each date, and carry that evidence through factors, asset pricing, portfolios, machine learning, and delivery without silently filling gaps?

## 2. Why the problem is difficult

A ticker is not a permanent security identifier. Firms change tickers, listings, share classes, capital structures, and reporting conventions. SEC facts become available after period end, market sources can splice histories with incompatible adjustment bases, and delisted firms can disappear from convenient datasets. Downstream models add further risks: transaction costs can be chosen after results, cross-validation can leak future labels, and explanations can be mistaken for causes.

## 3. Original research objective

The objective was to evaluate governed factor, asset-pricing, portfolio, and ML hypotheses on a broad US-equity panel while making unsupported results impossible to publish through the normal research interface. Research success meant a defensible answer—including a negative or inconclusive answer—not a predetermined alpha result.

## 4. Architecture

The platform uses an immutable publication chain:

```text
Phase 1 governed evidence
  -> Phase 2 point-in-time factors
  -> Phase 3 asset-pricing tests
  -> Phase 4 constrained portfolios and costs
  -> Phase 5 purged walk-forward ML
  -> Phase 6 authenticated API, dashboard, and reports
  -> Phase 7 independent assurance
  -> Phase 8 research and portfolio communication
```

Each publication binds configuration, checksums, code identity, lineage, lifecycle state, and upstream parents. Reads re-authenticate evidence rather than trusting a database row or filename.

## 5. Data engineering

All 822 HF Data Library candidates entered the same cheap-to-expensive screening waterfall before performance was examined. The final frozen universe contains 487 equities: 372 Tier A, 115 Tier B, and no Tier C. The real panel contains 715,447 market rows and 37,273 point-in-time fundamental rows across 18 fields. Raw data and generated artifacts remain local and untracked because source licences do not permit redistribution through the MIT repository.

## 6. Survivorship and point-in-time controls

Admission required source attribution, splice compatibility, instrument and venue eligibility, exact ticker/CIK evidence, singular listing-to-issuer mapping, share-basis compatibility, filing-time availability, and resolved terminal treatment. Present-day mappings were not backfilled. Fundamentals retain accession, taxonomy, concept, unit, period end, and availability date. Rejected candidates remained rejected even if later analytical results would have benefited from their inclusion.

## 7. Factor research

The engine defines 48 factors and estimates 47. `equity_issuance` remains non-estimable because net-equity-issuance and shareholder-equity evidence cannot be reconciled defensibly from the available SEC inputs without zero-filling or fabrication. The factor service produces authenticated portfolio and diagnostic evidence while preserving heterogeneous coverage and a common benchmark calendar.

## 8. Asset-pricing tests

Five governed model families were estimated: CAPM, Fama-French 3, Carhart 4, Fama-French 5, and the configured q-factor mapping. Mean adjusted R-squared increased from 0.063 for CAPM to 0.259–0.301 for the multifactor models. That is evidence of improved in-sample fit on project-specific diagnostic portfolios, not causal pricing success or deployable alpha. No custom model was invented because no custom equation was approved.

## 9. Portfolio construction

Before inspecting performance, one-way transaction-cost assumptions were frozen at LOW 5 bps, BASE 10 bps, and HIGH 20 bps. Eight long-only methods were evaluated: equal weight, minimum variance, mean variance, maximum Sharpe, maximum diversification, risk parity/ERC, HRP, and CVaR. BASE annualized descriptive returns range from 12.72% to 25.48%, with volatility from 10.00% to 16.04%. Every result declines as costs rise. The 32-month factor-portfolio window is too short to establish persistent investable performance.

## 10. Machine learning

Phase 5 uses only book-to-market and 12-minus-1 momentum to predict 21-trading-session forward total return relative to SPY. The design contains 27,640 monthly decision observations, a 60-month training window, 12-month validation window, one-month tests, purging, a one-month embargo, monthly retraining, and 17 complete folds. Eight models range from zero and historical-mean baselines to regularized linear models, Random Forest, and XGBoost.

## 11. Main findings

- A broad free/public-data cross-section can be made auditable when identity and filing-time evidence are explicit.
- Multifactor models fit the diagnostic portfolios better than CAPM in-sample.
- Frozen transaction costs reduce all portfolio results and matter most for turnover-intensive allocations.
- Constraints and portfolio methods create observable risk, drawdown, concentration, and tracking trade-offs.
- Authenticated delivery can expose results without bypassing publication integrity.

## 12. Negative findings

The study did not establish stable out-of-sample ML predictability. All aggregate IC bootstrap intervals include zero. Random Forest produced only a very small positive mean after-cost fold return and was positive in 9 of 17 folds; the other model families had negative mean after-cost returns. Feature rankings also changed across model and explanation methods. These are substantive research results, not implementation failures to be tuned away.

## 13. Defects discovered through real data

Real evidence exposed sparse formation-date and rolling-window failures, security-specific benchmark compounding, baseline explainability misrouting, an allocation assumption that all assets had predictions, incomplete Phase 4 identity binding in ML manifests, and daily pseudo-replication in a monthly ML design. Each defect received focused regression coverage; no formula, owner threshold, or missing observation was relaxed.

## 14. Research-integrity decisions

The universe was frozen before performance, costs were frozen before portfolio inspection, missing factors were not zero-filled, the Custom asset-pricing slot was not invented, ML used purging and embargo, and weak results were retained. Publication reads fail closed on checksum, mapping, lineage, configuration, lifecycle, or parent-identity failure.

## 15. Limitations

The universe is source-availability selected rather than CRSP/Compustat or historical-index replication. Early point-in-time coverage is sparse. Terminal-event and split-basis uncertainty caused exclusions. Phase 4 covers 32 months and factor portfolios rather than directly investable security portfolios. Phase 5 has two approved features and 17 folds. Explanations and scenarios are not causal, and the platform has no brokerage, execution, or production-cloud claim.

## 16. What this demonstrates technically

The work demonstrates typed Python architecture, immutable data contracts, effective-dated identity, SEC/XBRL processing, temporal validation, optimization, ML evaluation, API/dashboard delivery, deterministic manifests, fail-closed authentication, adversarial testing, and disciplined release engineering. Final assurance passed 300 tests with 90.59% branch-aware coverage.

## 17. What this demonstrates financially

The project connects asset-pricing theory, factor construction, robust regression, portfolio constraints, turnover and costs, downside risk, benchmark-relative evaluation, and model-risk governance. More importantly, it shows the ability to distinguish improved statistical fit from economic value and to defend an inconclusive or negative result rather than converting it into an unsupported investment claim.
