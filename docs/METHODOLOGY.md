# Methodology

## 1. Research Design

The project follows a one-way research sequence:

```text
source data
  → point-in-time security and issuer identity
  → universe screening
  → factor construction
  → asset-pricing estimation
  → portfolio construction and cost analysis
  → walk-forward machine learning
  → research reporting
```

Later stages consume earlier outputs but do not change the historical data used to create them. Analytical settings that materially affect interpretation—such as transaction-cost cases and temporal ML splits—are fixed before the corresponding results are compared.

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

The design does not backfill present-day identities, shares, or company names into earlier periods.

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

Cross-sectional preprocessing and portfolio formation use information available at the relevant date. Factor portfolios are formed from project characteristics rather than relabelled as official provider factors.

Forty-seven definitions are estimable in the current study.

## 5. Asset Pricing

Five model families are compared:

1. CAPM
2. Fama-French 3
3. Carhart 4
4. Fama-French 5
5. configured q-factor mapping

The dependent variable is portfolio excess return. The implementation supports OLS and related diagnostic tools; the reported study uses the configured publication estimator with heteroskedasticity/autocorrelation-aware inference where specified.

Model comparison emphasizes adjusted R², coefficients, uncertainty, residual diagnostics, and stability. Higher in-sample fit is not interpreted as proof of persistent alpha.

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

Portfolios are long-only, fully invested, and unlevered for the reported comparison.

The codebase also contains reusable covariance, Black-Litterman/Bayesian, scenario, and risk-analysis components. Black-Litterman is a supported framework in the software but is not claimed as one of the eight standalone empirical portfolio publications in the reported study.

## 7. Transaction Costs

One-way cost assumptions are evaluated at:

- LOW: 5 bps
- BASE: 10 bps
- HIGH: 20 bps

The reported BASE total decomposes to 5 bps spread, 2 bps slippage, and a 3 bps fixed-impact allowance. In the current engine configuration, the 2 bps slippage and 3 bps fixed-impact allowance are bundled into the configured slippage field; nonlinear market impact remains disabled because consistent liquidity evidence is not available at the required standard across the research panel.

Portfolio accounting reconciles holdings, trades, turnover, gross returns, costs, and net returns.

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
- 60-month training;
- 12-month validation;
- 1-month test windows;
- label purging;
- a 1-month embargo;
- monthly retraining;
- training-only preprocessing;
- bounded model search.

Random financial train/test splitting is not used.

Eight models are compared: zero baseline, historical-mean baseline, factor composite, linear regression, Ridge, Elastic Net, Random Forest, and XGBoost.

## 10. Predictive and Economic Evaluation

Predictive evaluation includes rank correlation/information coefficient, regression or classification metrics where applicable, calibration diagnostics, and bootstrap uncertainty.

The economic layer applies model signals through the same portfolio accounting and transaction-cost framework rather than evaluating prediction scores alone.

Feature explanations are treated as model diagnostics. Coefficients, permutation importance, and SHAP values are not interpreted as causal effects.

## 11. Interpretation Rule

The project separates three different questions:

1. Does the software produce the intended calculation?
2. Is the statistical result distinguishable from noise?
3. Is the effect economically meaningful after costs?

A positive answer to the first question is not treated as evidence for the second or third.
