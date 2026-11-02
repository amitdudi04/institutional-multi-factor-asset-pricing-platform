# Methodology

## 1. Research Design

Numerical authority: [accepted correction commit f22f5cb](https://github.com/amitdudi04/institutional-multi-factor-asset-pricing-platform/tree/f22f5cbe365e98c8d5fef6b5308ff765703df173/outputs/audit), with the [Phase 3 reconciliation](https://github.com/amitdudi04/institutional-multi-factor-asset-pricing-platform/tree/f22f5cbe365e98c8d5fef6b5308ff765703df173/outputs/audit/phase3/PHASE3_COMPLETE_VALIDATION.md) and [Phase 2C matched-sample checks](https://github.com/amitdudi04/institutional-multi-factor-asset-pricing-platform/tree/f22f5cbe365e98c8d5fef6b5308ff765703df173/outputs/audit/phase2c/PHASE2C_REGRESSION_VERIFICATION.md). The [accepted documentation and candidate manuscript](https://github.com/amitdudi04/institutional-multi-factor-asset-pricing-platform/tree/028dfd9cd18bcd6ef8114d829cc789d5bffacc61) preserve the interpretation of these results. Original releases are historical records.

The project follows a one-way research sequence:

```text
source data
  → recorded-day security and issuer identity controls
  → universe screening
  → factor construction
  → asset-pricing estimation
  → portfolio construction and cost analysis
  → walk-forward machine learning
  → research reporting
```

Later stages consume earlier outputs but do not change the historical data used to create them. Reported settings, including transaction-cost cases and temporal ML splits, are bound to their publication versions. Missing original H1/H3 approval and decision records do not establish preregistration.

## 2. Universe Construction

The initial candidate set contains 822 HF Data Library stocks. Screening combines:

- source attribution and source-transition checks;
- listing/lifecycle evidence;
- exact ticker/CIK and issuer/listing mapping evidence;
- point-in-time shares;
- SEC filing availability;
- fundamental concept coverage;
- split-basis consistency;
- terminal-event treatment.

The accepted research universe contains 487 equities.

The design rejects unsupported present-day identity/share substitutions; this control does not certify every original filing capture or issuer/share-class assignment. The supplied panel is source selected, not an exhaustive historical market.

## 3. Point-in-Time Fundamentals

SEC facts are used according to their filing availability rather than only their fiscal period end. Fundamental values join the market panel through effective-dated issuer-to-listing mappings.

Where a required input is unavailable or ambiguous, the related characteristic remains missing. This is important for variables such as `equity_issuance`, which is not estimable under the current evidence.

## 4. Factor Construction

The factor engine contains 48 definitions spanning:

- market;
- size;
- value;
- momentum;
- profitability/quality;
- investment and leverage;
- volatility and downside risk;
- liquidity-related characteristics.

Cross-sectional preprocessing and portfolio formation enforce recorded-day information gates; exhaustive historical capture and execution-time availability are not certified. Factor portfolios are formed from project characteristics rather than relabelled as official provider factors.

Forty-seven names have nonmissing raw values: 34,341,456 physical rows contain 28,550,589 nonmissing raw values and 24,255,559 scores. Forty-one characteristics yield 123 dependent sleeve IDs and 11,352 complete quantile-cycle rows; 956 of those rows are single-stock quantiles. Named factors need not be independent exposures. Corrected cycles use month-end UTC-day signals, next-XNYS-session modeled close entry and the following monthly entry-close exit. Genuine endpoints are required; missing old endpoints are not claimed recovered. Returns use frozen provider-vintage adjusted quotes; complete dividend-inclusive comparability is unverified.

## 5. Asset Pricing

Five model families are compared:

1. CAPM
2. Fama-French 3
3. Carhart 4
4. Fama-French 5
5. study-specific q-style mapping

The dependent variable is portfolio excess return. The implementation supports OLS and related diagnostic tools; the reported study uses the configured publication estimator with heteroskedasticity/autocorrelation-aware inference where specified.

The primary comparison uses matched 67–77 full monthly trading cycles per asset, 123 correlated portfolios and 615 OLS fits with three-lag Newey–West HAC. Alpha is decimal return per full cycle, not annualized. Factors are internal proxies; earnings yield in the q-style mapping is not accounting ROE or exact HXZ replication. Six duplicate return pairs and shared constituents limit interpretation. The joint residual matrix has 67 common dates, 123 columns and centered rank 66; its singular covariance does not support a conventional full GRS test. The accepted constituent-exclusion sensitivity retains 109 assets with 14 attrition cases. No new external-factor or joint-pricing test is implied.

## 6. Portfolio Construction

The portfolio study evaluates:

- Equal Weight
- Minimum Variance
- Mean Variance
- Maximum Sharpe
- Maximum Diversification
- Risk Parity
- Hierarchical Risk Parity
- CVaR

The eight methods are long-only, fully invested and unlevered allocations to 123 constructed quantile sleeves, using 36 prior training cycles and 31 complete evaluation cycles. Excluding the evaluated future row is verified; real historical pre-close availability and executable fills are not. Inner-sleeve costs, financing and capacity remain unverified.

The codebase also contains reusable covariance, Black-Litterman/Bayesian, scenario, and risk-analysis components. Black-Litterman is a supported framework in the software but is not claimed as one of the eight standalone empirical portfolio publications in the reported study.

## 7. Transaction Costs

Modeled per-side rates per absolute L1 traded-weight unit are:

- LOW: 5 bps
- BASE: 10 bps
- HIGH: 20 bps

The BASE quoted full spread is 10 bps, of which the 5-bps half-spread is charged, plus 2 bps slippage and a 3-bps fixed allowance. In the current engine configuration, the 2 bps slippage and 3 bps fixed-impact allowance are bundled into the configured slippage field; nonlinear market impact remains disabled because consistent liquidity evidence is not available at the required standard across the research panel.

L1 is sum(abs(target minus drifted pretrade weights)); one-way turnover is half L1. Fee = L1 × per-side rate, so BASE initial deployment costs 10 bps and a full switch costs 20 bps. Net return is gross less the fee. Interval cash is compounded on the same holding window. Annualized net return is geometric wealth^(12/31)-1; arithmetic mean excess divided by its SD times sqrt(12) defines reported Sharpe. Monthly-cycle VaR/ES are positive-loss decimals, unannualized, with two tail observations; this is descriptive rather than reliable tail calibration.

## 8. Risk and Scenario Analysis

The risk layer includes:

- annualized volatility;
- beta and alpha diagnostics;
- drawdown and maximum drawdown;
- downside deviation;
- Value at Risk;
- Expected Shortfall;
- risk contribution;
- diversification ratio.

Scenario analysis supports market, rates, volatility, inflation, liquidity, and custom exposure mappings. Scenario outputs are sensitivity mappings, not forecasts.

## 9. Machine-Learning Experiment

The empirical ML study deliberately uses a small feature set:

- book-to-market;
- 12-minus-1 momentum.

The target is the next 21-trading-session security return minus SPY's return over the same interval.

The temporal design uses:

- monthly decisions;
- expanding training from 60 to 74 calendar months;
- 12-month validation;
- 1-month test windows;
- label purging;
- a 1-month embargo;
- monthly retraining;
- training-only preprocessing;
- bounded model search.

The corrected panel has 27,632 rows, 89 common month ends, 15 dependent folds and 7,286 held-out observations per family. Five of 14 adjacent test-label pairs overlap despite valid partition purging and embargo. Recorded-day feature gates and training-only transforms pass; exhaustive real filing capture is not verified. Forecasts are retrospective reconstructions rather than documented historical live predictions.

Eight models are compared: zero baseline, historical-mean baseline, factor composite, linear regression, Ridge, Elastic Net, Random Forest, and XGBoost.

## 10. Predictive and Economic Evaluation

Predictive evaluation includes rank correlation/information coefficient, regression or classification metrics where applicable, calibration diagnostics, and bootstrap uncertainty.

IC is date-level cross-sectional rank correlation; its exploratory bootstrap uses 100 moving-block resamples of length 3 and seed 17. Linear and factor composite share the same estimator. Constant IC is undefined. The economic check ranks held-out signals, equal weights the selected top 20%, resets to cash/unit NAV each fold and evaluates one subsequent session with initial fees; it is not the 21-session forecast horizon or a continuous investment backtest. Stable incremental after-cost value remains unestablished.

Feature explanations are treated as model diagnostics. Coefficients, permutation importance, and SHAP values are not interpreted as causal effects.

## 11. Interpretation Rule

The project separates three different questions:

1. Does the software produce the intended calculation?
2. Is the statistical result distinguishable from noise?
3. Is the effect economically meaningful after costs?

A positive answer to the first question is not treated as evidence for the second or third.
