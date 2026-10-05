# Limitations

The project is intentionally explicit about what the available evidence can and cannot support.

## Universe and Data

- The universe is selected by public-source availability and research screening rules; it is not a reconstruction of CRSP, Compustat, the historical S&P 500, or the Russell 1000.
- HF Data Library coverage creates survivorship and source-selection limitations, particularly in earlier periods.
- The PiTrading-to-IEX source transition limits direct comparability of historical volume and liquidity measures.
- Early cross-sectional coverage is sparse relative to later periods.
- Candidates with unresolved identity, terminal-event, source-splice, or share-basis evidence are excluded, which can create residual selection effects.

## Fundamentals

- SEC accounting concepts and reporting practices differ across issuers and time.
- Point-in-time concept projection is traceable but less standardized than a commercial Compustat-style dataset.
- `equity_issuance` is not estimable from the currently accepted evidence.
- Multi-class issuers can remain non-estimable for share-based variables when exact class allocation is unavailable.

## Factor and Asset-Pricing Research

- Project characteristic portfolios are not claimed to be exact replications of every published academic factor construction.
- Higher adjusted R² in the multifactor regressions is an in-sample explanatory result, not evidence of causal pricing or future alpha.
- H1 remains inconclusive because the complete net-cost/multiple-testing decision for the original directional-spread hypothesis is unavailable.
- H3 remains inconclusive because the complete corrected regime/break decision is unavailable.

## Portfolio Research

- The reported portfolio evidence spans only about 32 months.
- Test assets are factor portfolios rather than directly investable individual-security portfolios.
- Transaction costs are sensitivity assumptions rather than measured executions.
- Nonlinear market impact and capacity are not estimated because the required liquidity evidence is unavailable at the necessary standard.
- Observed ranking over a short sample does not establish persistent superiority of CVaR, maximum Sharpe, or any other allocator.

## Machine Learning

- The reported ML study uses only book-to-market and 12-minus-1 momentum.
- It contains 17 complete out-of-sample folds.
- All aggregate IC confidence intervals include zero.
- Stable after-cost incremental value is not established.
- Feature rankings vary across models and explanation methods.
- SHAP, permutation importance and coefficients are model diagnostics, not causal effects.

## Scenarios and Risk

- Scenario shocks are sensitivity mappings, not forecasts.
- VaR and Expected Shortfall estimates depend on the chosen historical/statistical assumptions.
- The project does not estimate live execution slippage, taxes, financing, borrow constraints, or strategy capacity.

## Software and Deployment

- The API and dashboard are research interfaces, not a production trading system.
- No brokerage, live order execution, streaming-market SLA, or fiduciary investment service is provided.
- Exact reproduction of the empirical study requires lawful access to the same third-party data that are not redistributed in Git.

These limitations bound the claims in the README and [RESULTS.md](RESULTS.md); they are not reasons to replace weak or inconclusive findings with stronger language.
