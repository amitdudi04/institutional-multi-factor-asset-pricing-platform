# Phase 2 Factor Methodology

## Interpretation

These are project-specific observable characteristics and diagnostic portfolios, not official provider factors and not asset-pricing conclusions. Version 1.0.0 operates at daily frequency using information available by each date’s UTC cutoff. The default production windows are 21, 63, 126, 252, and 504 observations with 20 minimum observations and 252-period annualization.

## Definitions

| Family | Factor | Formula and direction |
|---|---|---|
| Market | `market_return` | Approved broad-market total return; descriptive |
| Market | `excess_return` | broad-market simple total return − frequency-matched RF |
| Market | `risk_free_rate` | frequency-matched approved risk-free simple return |
| Market | `rolling_market_beta` | rolling cov(security, market) / var(market) |
| Size | `market_cap` | split-adjusted price × point-in-time shares |
| Size | `log_market_cap` | ln(market cap) |
| Size | `size_small`, `size_mid`, `size_large` | membership from same-date XNYS 30th/70th market-cap breakpoints |
| Value | `book_to_market` | book equity / market cap; higher is cheaper |
| Value | `price_to_book` | market cap / book equity; lower is cheaper |
| Value | `earnings_yield` | net income / market cap |
| Value | `cash_flow_yield` | operating cash flow / market cap |
| Value | `dividend_yield` | dividends / market cap |
| Momentum | `momentum_1m`, `momentum_3m`, `momentum_6m` | compounded simple return over 21/63/126 observations |
| Momentum | `momentum_12_1m` | compounded return over the prior 12 months excluding the most recent month |
| Momentum | `momentum_12m`, `momentum_24m` | compounded simple return over 252/504 observations |
| Momentum | `residual_momentum` | 12–1 compounded residual after rolling market beta |
| Quality | `roe` | net income / shareholder equity |
| Quality | `roa` | net income / total assets |
| Quality | `gross_profitability` | gross profit / total assets |
| Quality | `operating_margin` | operating income / revenue |
| Quality | `net_margin` | net income / revenue |
| Quality | `asset_turnover` | revenue / average assets |
| Quality | `accruals` | total accruals / total assets; lower conventionally preferred |
| Quality | `leverage` | total debt / total assets; lower conventionally preferred |
| Quality | `debt_to_equity` | total debt / shareholder equity; lower conventionally preferred |
| Quality | `interest_coverage` | operating income / interest expense |
| Investment | `asset_growth` | total assets / prior total assets − 1; lower conventionally preferred |
| Investment | `capex_growth` | capex / prior capex − 1; lower conventionally preferred |
| Investment | `equity_issuance` | net equity issuance / shareholder equity; lower conventionally preferred |
| Investment | `working_capital_growth` | working capital / prior working capital − 1; lower conventionally preferred |
| Low volatility | `rolling_volatility` | annualized rolling standard deviation |
| Low volatility | `downside_volatility` | annualized rolling standard deviation of negative returns |
| Low volatility | `semi_variance` | annualized rolling mean squared negative return |
| Low volatility | `beta` | rolling market beta; lower is the low-beta direction |
| Low volatility | `idiosyncratic_volatility` | annualized rolling standard deviation of market residual |
| Liquidity | `average_dollar_volume` | rolling mean of price × volume |
| Liquidity | `turnover` | volume / shares outstanding |
| Liquidity | `amihud_illiquidity` | abs(return) / dollar volume; lower is more liquid |
| Liquidity | `bid_ask_proxy` | (high − low) / midpoint; lower is more liquid |
| Risk | `rolling_beta` | rolling cov(security, market) / var(market) |
| Risk | `rolling_correlation` | rolling correlation with the market |
| Risk | `tracking_error` | annualized volatility of security return − benchmark return |
| Risk | `downside_beta` | rolling beta estimated on negative-market observations |

Every persisted manifest repeats the complete definition, rationale, inputs, unit, direction, transformation chain, dependencies, version, and research limitation for each factor.

## Timing and bias controls

Universe eligibility and sector/industry classifications are explicit point-in-time fields; absent histories are not reconstructed from current membership. Accounting values use backward as-of joins on actual availability timestamps. Market, eligibility, classification, and accounting availability all propagate to output availability. Future timestamps, duplicate keys, invalid identifiers, unauthenticated parents, invalid returns, and unit contradictions block computation.

Characteristics formed on date `t` are assigned to quantiles on `t`; diagnostic returns are realized only from the security’s next available observation `t+1`. This prevents same-close execution. No forward-filled return, constituent, accounting, or classification value is invented. Delisting-return completeness remains a parent-data limitation and must be disclosed by the applicable Phase 1 dataset.

## Missingness, outliers, transforms, and neutralization

Missing values remain missing. Ratios with zero denominators and undefined rolling statistics become null rather than infinity. Winsorization is cross-sectional and date-local. The configured default is 1st/99th percentile winsorization followed by robust z-score scaling; raw, winsorized, normalized, and direction-aligned score values are all retained. A higher score always represents the documented preferred direction. Rank, percentile, conventional z-score, min–max, winsorized-only, and no-transform modes are supported. Optional sector or industry neutralization performs the same date-local operation within the point-in-time classification; the default is `none`.

These thresholds are implementation defaults, not a change to the open Owner Decision Register. Coverage and changed-value counts are emitted so an owner can evaluate later approval.

## Quantile portfolios and diagnostics

Version 1 forms ascending terciles for cross-sectionally meaningful continuous characteristics at each month end and calculates the following holding-period value-weighted simple return using formation-date market capitalization. Common market/RF series and already-discrete size indicators are excluded from arbitrary tied-rank portfolios. It persists security count, benchmark return, and active return. Diagnostics include coverage, winsorized-value counts, pairwise characteristic correlations, top-tercile membership turnover, quantile returns, descriptive active-return t-statistics, quantile monotonicity, rolling active returns, and stable plot-data hooks.

No trading cost is deducted because the cost model is not approved until Phase 4. No significance threshold is used to label success because the significance decision remains proposed. Portfolio diagnostics are therefore descriptive, gross, and explicitly not a backtest or asset-pricing test.

## Numerical and research limitations

Free or owner-supplied source limitations flow through parent manifests. A broad S&P 500 total-return proxy is not relabeled as an official index series. XNYS breakpoints require adequate authenticated XNYS coverage. Small cross-sections yield missing standardized values. Accounting ratios may be economically unstable near zero denominators. Rolling estimates require configured history. Corporate actions, delistings, historical membership, and filing timestamps are only as defensible as the authenticated Phase 1 parents. No empirical factor premium, investability, or performance claim is made by software-test fixtures.
