# Phase 4 Portfolio and Risk Methodology

## Allocations and estimators

Implemented allocation methods are equal weight, market-cap weight, minimum variance, mean-variance, maximum Sharpe, maximum diversification, risk parity, HRP, and historical-scenario CVaR. Black-Litterman combines equilibrium excess-return priors with explicit `P`, `Q`, `Ω`, `τ`, risk aversion, market weights, and covariance. The modular Bayesian framework combines prior and sample means through precision weighting. Black-Litterman/Bayesian posteriors feed the general constrained optimizer rather than creating an untraceable special path.

Covariance methods are sample, Ledoit-Wolf shrinkage, and minimum-covariance-determinant robust estimation. Matrices must be finite, symmetric, and positive semidefinite. Eigenvalue regularization is explicit and separately callable; it is never a silent optimizer fallback.

## Constraints and costs

The approved operational baseline is long-only, fully invested, and unlevered. Minimum/maximum weights, turnover, sector, exposure, liquidity-trade, and transaction-cost budgets are supported. Optimizers return failure on infeasibility or convergence failure and never relax a constraint. Exact concentration/capacity/cost numbers remain open owner decisions. The repository configuration leaves those values `null`; a research run must explicitly provide commission, spread, slippage, and impact values.

Turnover is the sum of absolute target-minus-current weights. Commission and slippage apply in basis points to turnover; half-spread is charged per trade side. Simplified market impact is modular and requires explicit positive liquidity. Per-asset transaction rows reconcile to the portfolio cost charged to net return.

## Backtest timing and accounting

Rolling windows use exactly the configured observations preceding a rebalance; expanding windows begin at the first observation and add only past rows. Target weights apply to the next return. After each return, weights drift by relative asset growth before the next rebalance. Gross return minus explicit transaction cost equals net return; net minus benchmark equals active return. Dates must be unique, increasing, complete, and exactly benchmark-aligned.

## Risk and scenarios

Risk outputs include annualized and rolling volatility, beta/alpha, rolling beta, tracking error, information ratio, Sharpe, Sortino, Calmar, Omega, drawdown, downside deviation, historical/parametric VaR, expected shortfall/CVaR, marginal/component risk, and diversification ratio. VaR/ES use a positive-loss convention. Undefined ratios are unavailable (`null`), not zero or infinity. Component risk reconciles to portfolio volatility.

Scenario kinds cover market crash, interest-rate, volatility, inflation, liquidity, and custom shocks. Impacts equal portfolio-weighted mapped exposure times the explicit shock; unmapped shocks are disclosed. Scenarios are instantaneous sensitivities, not forecasts.

## Limitations

The engine has no live empirical validation, predictive signal, execution venue model, order book, tax model, corporate-action ledger, or capacity claim. The service can enforce sector/exposure constraints only after authenticated classifications/exposure vectors become available; it rejects their use otherwise. Market-cap allocation requires explicit positive aligned capitalization evidence and is available as a domain primitive, not inferred from Phase 2 quantile portfolios.
