# Architecture

## Research Dependencies

The components share authenticated source inputs but **are not one linear chain of model outputs**. The asset-pricing analysis and portfolio evaluation use constructed factor/quantile portfolios; the ML experiment uses its own historical factor-score features, market labels and recorded fee context.

```text
Market bars + lifecycle evidence + SEC filings/XBRL + cash benchmark
                              |
                 Security/issuer mapping
                              |
            Recorded-availability research panels
                              |
               Factor scores and formations
                    /         |          \
                   /          |           \
      Factor/quantile returns  |      ML features + market labels
             |                |                 |
      Asset-pricing tests     |       Purged walk-forward models
             |                |                 |
      Constructed sleeves ----+       One-session economic checks
             |                                  |
      Portfolio allocation and costs            |
                    \                          /
                     Research publications / API / dashboard
```

The diagram depicts analytical dependencies, **not verified real-time data capture or executable orders**. In particular, ML does not consume estimated asset-pricing regression coefficients, and its accepted corrected publications retain their authenticated historical score/label and fee-context parents. The corrected portfolio experiment uses corrected quantile-return inputs. See [Methodology](METHODOLOGY.md), [Results](RESULTS.md), and [Reproducibility](REPRODUCIBILITY.md).

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
