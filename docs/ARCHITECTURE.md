# Architecture

## Research Flow

```text
HF market data + Alpha Vantage lifecycle + SEC filings/XBRL + FRED/French
                                   ↓
                     security and issuer mapping
                                   ↓
                      point-in-time data panel
                                   ↓
                         factor construction
                                   ↓
                       asset-pricing models
                                   ↓
             portfolio construction + costs + risk
                                   ↓
                   purged walk-forward machine learning
                                   ↓
                       API / dashboard / reports
```

## Package Responsibilities

| Area | Responsibility |
|---|---|
| `data/` | Acquisition adapters, security identity, SEC processing, contracts, storage, validation and point-in-time access |
| `factors/` | Characteristic definitions, temporal joins, preprocessing, factor portfolios and diagnostics |
| `asset_pricing/` | Model configuration, research-panel construction and model publication |
| `regression/` | OLS/WLS, rolling/expanding, panel and Fama-MacBeth estimation |
| `portfolio/` | Portfolio research service and configuration |
| `optimization/` | Mean-variance, maximum-Sharpe, risk-parity, HRP, CVaR, covariance and Black-Litterman/Bayesian components |
| `backtest/` | Past-only portfolio accounting and transaction costs |
| `risk/` | Volatility, beta, drawdown, VaR, Expected Shortfall and risk contribution |
| `scenarios/` | Exposure-based scenario analysis |
| `ml/` | Features, targets, temporal splits, preprocessing, models, evaluation, explanations and economic testing |
| `delivery/` | Research-result catalog and report generation |
| `api/` | FastAPI research interface |
| `dashboard/` | Streamlit presentation layer |

## Data Direction

The design is intentionally one-way: source data are transformed into research inputs, then factors, models, portfolios and reports. Presentation layers consume stored research outputs rather than reimplementing finance calculations independently.

## Reproducibility Boundary

Research outputs record configuration and code identity so that a result can be associated with the inputs and settings that produced it. Raw third-party evidence remains outside the public Git repository because redistribution rights are source-specific.

## Delivery Boundary

The API and dashboard are research interfaces. They expose the project outputs and provenance; they are not brokerage, order-routing, live execution, or production trading infrastructure.
