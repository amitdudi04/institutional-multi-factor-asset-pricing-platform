# Institutional Project Specification

## 1. Document Control

| Field | Value |
|---|---|
| Document | Project Specification (“Project Bible”) |
| Project | Institutional Multi-Factor Asset Pricing & Portfolio Analytics Platform |
| Status/version | Owner Approved; Phases 1–3 Complete; Phase 4 Authorized / 0.4.0 |
| Updated/owner | 2026-08-04 / Repository Owner |
| Approval | Owner Approved; Phases 1–3 Assured; Phase 4 Authorized |
| Audience | Owner, researchers, engineers, validators, reviewers, future agents |
| Authority | Owner instructions; `DEVELOPMENT_CONSTITUTION.md`; this document; approved phase specifications; validated configuration |

Revision requires Section 50 change control. Future agents must not silently change approved decisions or implement proposals/open items as defaults.

| Status | Meaning |
|---|---|
| `APPROVED BASELINE` | Authorized conceptual direction; implementation still requires the active phase. |
| `PROPOSED — OWNER APPROVAL REQUIRED` | Recommended v1 choice, not operational until approved. |
| `OPEN — OWNER DECISION REQUIRED` | Depends on owner, data, license, budget, law, or deployment context. |
| `DEFERRED` | Postponed pending evidence or a later phase. |
| `OUT OF SCOPE` | Excluded from v1 and not promised. |

## 2. Executive Summary

The platform will support a reproducible empirical equity research chain: provenance-controlled data, point-in-time factors, classical asset-pricing tests, constrained portfolios, realistic walk-forward evaluation, risk/attribution, interpretable ML, and research delivery. It joins financial economics with research engineering; it is not a model collection or dashboard demonstration.

“Institutional-style” must be earned through immutable inputs, explicit rights and assumptions, temporal correctness, robust inference, reconciled accounting, model-risk controls, reproducible runs, interface/domain separation, and limitation disclosure. It does not imply licensed institutional data or fiduciary readiness. Phase 1 passed post-remediation independent assurance; Phase 2 factor software and Phase 3 asset-pricing software passed their internal assurance gates without producing live empirical results. Phase 4 is authorized, but no Phase 4–7 output exists. Success is regeneration of defensible answers from approved inputs without fabrication or silent substitution.

## 3. Project Vision

`APPROVED BASELINE`

```text
Source Data -> Immutable Raw Storage -> Validation/Standardization
-> Point-in-Time Features -> Factors -> Asset-Pricing Estimation
-> Scoring/Forecasting -> Optimization -> Walk-Forward Backtesting
-> Risk/Attribution -> Explainability -> API/Dashboard/Reports
```

Sources establish provenance; raw storage preserves evidence; validation blocks defective inputs; standardization creates contracts; point-in-time features encode knowability; factors test theory; asset pricing evaluates explanation; scoring supports decisions; optimization maps views to constrained holdings; backtesting reconstructs execution/accounting; risk and attribution explain outcomes; explainability tests model behavior; interfaces expose approved services without recalculation.

## 4. Project Objectives

### 4.1 Research objectives

Evaluate net factor premia; compare CAPM/FF3/Carhart/FF5; test factor stability across regimes/sectors; compare constrained portfolios with transparent benchmarks; test incremental ML value; reconcile security/sector/factor/cost attribution; and quantify sensitivity to data, estimation, costs, and model uncertainty.

### 4.2 Engineering objectives

Provide configuration control, modularity, typed interfaces, testability, observability, deterministic behavior where practical, data/run lineage, transparent errors, auditable artifacts, and UI-independent research logic.

### 4.3 Admissions and research-portfolio objectives

Demonstrate financial theory, empirical design, statistics, portfolio/risk practice, restrained ML, software engineering, validation, and communication. This is evidence for review, not a guarantee of admission, employment, or investment performance.

## 5. Research Questions

| ID | Question/motivation | Unit, dependent variable, test | Metric/limits | Phase |
|---|---|---|---|---|
| RQ1 | Do approved characteristics earn persistent premia? | Security-period future excess returns; point-in-time spreads/ranks | Net spread/CI/rank IC; data, microcap, multiplicity bias | 2 |
| RQ2 | Do multifactor models explain returns better than CAPM? | Test-asset excess returns; aligned regression comparison | Adjusted R², alpha CI, AIC/BIC; source/test-asset dependence | 3 |
| RQ3 | Are premia/loadings stable? | Rolling returns/loadings; breaks, regimes, subperiods | Parameter/CI drift; regime uncertainty | 2–3 |
| RQ4 | Do constrained factor portfolios improve outcomes? | Walk-forward portfolio/benchmark paths | Net Sharpe CI, drawdown, concentration; estimator dependence | 4 |
| RQ5 | How sensitive are conclusions to costs? | Gross/net returns from turnover and cost grids | Cost drag and ranking changes; approximate costs | 4 |
| RQ6 | How does behavior vary by regime? | Conditional factor/portfolio returns; ex ante states | Conditional return/risk CI; small samples | 2–5 |
| RQ7 | Does ML add information beyond factor/linear challengers? | Next-period rank/probability/volatility target | Rank IC/AUC/loss plus net outcome; overfit/noise | 5 |
| RQ8 | Where is risk concentrated? | Holdings/exposures/loss distribution | Component risk, HHI, drawdown contribution; model error | 4–5 |
| RQ9 | What explains active performance? | Portfolio minus benchmark returns | Reconciled attribution; classification/linking limits | 5 |
| RQ10 | How does model uncertainty alter decisions? | Forecasts, weights, risk under alternatives | Rank/weight/outcome stability; structural uncertainty | 3–5 |

No question presumes a positive conclusion.

## 6. Research Hypotheses

`PROPOSED — OWNER APPROVAL REQUIRED`: report 1%, 5%, and 10% levels, never call 10% strong evidence, emphasize CIs/effect sizes, and use FDR for broad test families. Economic-materiality thresholds are `OPEN` pending costs/mandate.

| ID | H0 / H1 | Data/method | Economic/multiplicity rule | Phase |
|---|---|---|---|---|
| H1 | Characteristic spreads are zero / at least one differs in documented direction | Point-in-time features/returns; HAC, block bootstrap, ranks | Net of approved costs; FDR | 2 |
| H2 | Multifactor models do not improve on CAPM / at least one does | Test assets/factors; alpha, adjusted R², information criteria, OOS | Stable economic improvement; model-family correction | 3 |
| H3 | Premia/loadings are stable / material instability exists | Factors/regimes; rolling, interaction, break tests | Magnitude versus unconditional; regime multiplicity | 2–3 |
| H4 | Costs do not change conclusions / reduce or reverse them | Orders/prices/costs; gross-net sensitivity | Ranking/materiality change | 4 |
| H5 | Constraints do not improve concentration/downside / they do | Forecast/covariance/holdings; challenger comparison | Risk benefit versus net-return/tracking trade-off | 4 |
| H6 | ML adds no OOS value / adds stable incremental value | Features/targets; paired walk-forward comparison | Net/stability benefit, not fit; model correction | 5 |
| H7 | Explanations are unstable/incoherent / stable and economically interpretable | Exact pipelines; coefficients, permutation/SHAP stability | Cross-fold/regime stability; no causal claim | 5 |

## 7. Scope

### 7.1 V1 in scope

`APPROVED BASELINE`: EOD equities; reliable fundamentals and macro/RF inputs when approved; factors/scoring; CAPM, FF3, Carhart, FF5; interpretable ML; equal/inverse-volatility/minimum-variance/mean–variance/maximum-Sharpe/Black–Litterman/risk-parity/HRP/CVaR portfolios; risk, attribution, scenarios; cost-aware walk-forward backtests; provenance-aware API/dashboard/reports. Scope is not current implementation or unconditional feasibility.

### 7.2 V1 conditionally in scope

q-factor (approved inputs); PCA (training-safe and justified); ESG (licensed temporal data); SEC fundamentals (validated mapping/timing); international equities and country/currency attribution (approved identifiers/FX/calendars); Monte Carlo (approved calibration); LightGBM/CatBoost (baseline evidence and dependency review).

### 7.3 Out of scope

`OUT OF SCOPE`: deep learning, reinforcement learning, HFT/intraday, options/derivatives, live brokerage/trading, alternative-data scraping, proprietary ESG, NLP sentiment, crypto, distributed computing, Kubernetes, microservices, and streaming.

## 8. Research Universe

`APPROVED BASELINE`: US-listed common equities; large/mid-cap point-in-time transparent screen; broad S&P 500 total-return proxy; USD; daily research frequency; 2010-01-01 through latest validated date. A historically reconstructed membership universe remains conditional on lawful owner/licensed history; current constituents alone must be labeled survivorship-biased.

The US offers accessible research inputs, mature literature, sector depth, benchmarks, and French-factor compatibility, but still has licensing, delisting, membership, and point-in-time limitations.

| Alternative | Benefit | Data/survivorship/fundamental/currency issue | Timing |
|---|---|---|---|
| China | Distinct structure | Share classes, limits/suspensions, constituents, CNY/HKD, accounting | Dedicated post-v1 study |
| India | Relevant growth market | Licensed history, delistings/actions, INR, filing coverage | Viable v1 alternative if owner/data support |
| US/China/India | External validity | Three mapping/legal/calendar/FX regimes | After one-market validation |
| Developed global | Diversification | Expensive history, multi-currency/taxonomy | Later licensed phase |

Financial-sector primary common shares are included. ETFs, ETNs, closed-end funds, ADRs, preferred shares, REITs, warrants, rights, units, SPAC units, mutual/money-market funds, debt, options, futures, and crypto are excluded. Historical membership source remains `OPEN — OWNER DECISION REQUIRED` before an unbiased historical membership claim.

## 9. Security Master and Identifiers

`APPROVED BASELINE`: immutable internal `security_id`, not ticker, is the key because tickers change/reuse and vary by venue/provider. Store distinct issuer ID; ticker/exchange/MIC; name/type/share class; currency/country; taxonomy/version; listing and delisting dates/status; effective-dated provider IDs; benchmark membership. ISIN is conditional on availability; CUSIP on legal rights. Mapping intervals may not overlap ambiguously and require source/retrieval/conflict status.

## 10. Data-Source Strategy

Candidates do not authorize integration. Owner data is authoritative; public data is not institutionally licensed.

| Family | Preferred / fallback candidate | Fields/frequency/timing | Validation/license/failure |
|---|---|---|---|
| OHLCV/adjustments | Owner/licensed/official / Yahoo, Alpha Vantage | Daily raw/adjusted prices, volume, currency | Terms, OHLC/calendar/action reconciliation; quarantine, no empty success |
| Dividends/splits | Official/owner / Yahoo | Event dates, amount/currency/ratio | Duplicate/chronology/price-break checks; quarantine conflict |
| Cap/shares | Owner/licensed / SEC + market source | Shares/float/price/units, filing availability | Unit/split checks; never future-backfill |
| Statements | Owner/licensed / SEC EDGAR | Values/units/period/form/accession/filing/availability | Amendments versioned; missing stays missing |
| Sector/industry | Owner/licensed / approved provider | Effective-dated taxonomy | No guessed class; license/version check |
| Benchmark prices | Licensed/official/owner / approved ETF proxy | Daily total return or disclosed adjusted proxy | Never silently substitute index/ETF |
| Constituents | Licensed/official/owner | Entry/exit/weight history | Block unbiased claim when absent |
| RF/Treasuries | FRED/US Treasury / owner | Series/tenor/value/unit/releases | Metadata/unit/frequency checks; no zero fallback |
| Inflation/GDP | FRED/BEA/World Bank / owner | Value/unit/period/vintage/availability | Preserve revisions; exclude unavailable feature |
| FF factors | Kenneth French / owner-licensed | MKT, SMB, HML, RMW, CMA, momentum | Region/unit/checksum; never relabel project factors official |
| FX | Central bank/owner / approved public | Pair/convention/rate/time | Inverse/holiday checks; no parity fallback |
| ESG | Approved licensed/owner only | Score/pillar/method/effective date | `OPEN — OWNER DECISION REQUIRED`; remains absent if unapproved |

Approved Phase 1 sources are Yahoo Finance, Kenneth French Data Library, FRED, SEC EDGAR, and owner-supplied data. Every adapter records request/source identity, retrieval, requested/returned range, raw location/hash, schema, terms limitation, and partial failures. Use is local-owner-only with no redistribution; any new provider, licensed budget, or broader right remains an owner decision.

## 11. Data Governance

`APPROVED BASELINE`: immutable checksum-protected raw responses; append-only ingestion where feasible; manifests for request, timestamps, files/hashes, schema/license/status; versioned downstream artifacts with parent/config/code identities and validation reports; critical failures quarantined and blocked.

Operational paths include Phase 1 `data/{raw,interim,processed,manifests,quarantine}` and ignored Phase 2 `data/{factors,factor_manifests}` outputs. Future model paths remain unimplemented. Empirical contents/databases/generated reports are ignored; reviewed contracts, metadata definitions, and isolated software fixtures may be tracked. Raw retention is until explicit owner deletion; access is local-owner-only with no public serving or redistribution. Transformations never edit raw files.

## 12. Data Contracts

Dates/timestamps must distinguish observation, period end, filing, publication, retrieval, and availability; unknown timing remains unknown and restricts use.

| Contract | Key | Required core / optional | Validation |
|---|---|---|---|
| Security master | `security_id`; provider+effective interval | IDs, ticker, venue, currency, country, type, dates/status / taxonomy, ISIN | Unique IDs, valid nonoverlapping intervals |
| Daily market | security,date,venue | raw OHLCV, currency, source / adjusted close/status | OHLC bounds, nonnegative volume, unique/calendar-valid |
| Actions | security,action ID | type, announced/ex/effective/pay dates, value/ratio/currency | chronology, positive ratio, duplicate/conflict |
| Fundamentals | issuer,concept,period,accession,version | value/unit/form/filing/availability / segment/restatement | units/periods; no pre-filing availability |
| Macro | series,period,vintage | value/unit/frequency/publication/availability/source | series/unit/vintage validity |
| Factor returns | set,factor,period | return/unit/frequency/source/method/availability | unique/finite/aligned/provenance |
| Characteristics | security,as-of,factor,version | raw/transformed value, direction, cutoff, availability / coverage | no future input or silent imputation |
| Holdings | portfolio,as-of,security | quantity/weight/price/currency/value/run | duplicate, weight/value/constraint reconciliation |
| Transactions | portfolio,order,fill | times, side, quantity, price, costs, currency/run | temporal order and cash reconciliation |
| Predictions | run,model,security,decision,horizon | value/target/feature cutoff/training window / uncertainty | version link, probability bounds, uniqueness |
| Backtest | run,portfolio,valuation time | NAV, gross/net return, cash, benchmark, costs | accounting/gross-net/timeline reconciliation |
| Risk | run,portfolio,as-of,measure,horizon,confidence | value/unit/loss convention/method / components | valid confidence; component reconciliation |

Concrete numeric precision/nullability is a Phase 1 schema decision.

## 13. Financial Conventions

`APPROVED BASELINE`: simple returns for portfolio accounting; log returns only when statistically justified; raw prices/actions retained; validated total-return adjustments for performance; UTC-normalized storage plus exchange-local metadata; frequency-matched RF; no invented missing values.

`PROPOSED`: close-to-close total returns; configurable 252-day annualization; next-eligible execution; benchmark matched on currency/return/calendar/frequency. RF conversion must document compounding/day count. Define positive loss `L=-r`; VaR is a loss quantile and ES the documented tail-loss mean. Calendar, close, FX, dividend tax, non-trading-day, and final benchmark conventions require approval.

## 14. Temporal Integrity

Every item exposes observation, availability, decision, execution timestamps where applicable. Signals use only information available at cutoff; execution is next eligible unless same-period executability is proved. Fundamentals use actual filing availability or a disclosed conservative configured lag. Full-sample scalers/selection/imputation, future constituents/covariance, shuffled time splits, and same-close execution from same-close inputs are prohibited. Tests must inject future data and verify rejection plus interval/calendar boundaries.

## 15. Data Quality Framework

Check completeness, uniqueness, validity, consistency, timeliness, continuity, accuracy proxies/cross-source agreement, outliers, stale prices, and corporate actions. Primary-key/required-field loss, impossible values, future timing, ambiguous IDs, or unexplained required-series breaks block. Verified extremes, optional-field gaps, or known suspensions may warn. Statuses: `PASS`, `PASS WITH WARNINGS`, `QUARANTINED`, `FAIL`. Critical failures override composite scores. Reports include check/version/scope/counts/severity/disposition/run; quarantine preserves evidence but is unavailable to primary research.

## 16. Factor Taxonomy

| Factor | Candidate definition/intution | Timing/direction/limits |
|---|---|---|
| Market | Market total return minus RF; beta as characteristic | Aligned factor; beta is not automatically positive score |
| Size | cap or log cap | Point-in-time shares×price; smaller premium direction; microcap bias |
| Value | book-to-market, earnings/cash-flow yield, EBITDA/EV | Filed data; higher cheapness; denominator/accounting issues |
| Momentum | 12–1, 6–1 cumulative return | End before recent month; higher positive; crash/turnover risk |
| Profitability | operating profitability, ROE/ROA, gross profit | Filing lag; higher positive; sector comparability |
| Investment | asset/capex growth | Consecutive available filings; lower growth conventionally positive |
| Quality | profitability, earnings quality, leverage, stability | Composite; redundancy/coverage risk |
| Low volatility | realized/downside/idiosyncratic volatility, beta | Historical window; lower risk positive after alignment |
| Liquidity | Amihud, turnover, dollar volume, zero returns | More liquid positive for investability; volume quality |
| Growth | revenue/earnings growth | Avoid investment duplication/base effects |
| PCA | Training-window components | `DEFERRED`; sign/rotation/interpretability risk |

Every factor documents formula, rationale, units, inputs, eligibility, lookback/history, publication lag, outliers/transforms, standardization/neutralization, direction, formation/execution/holding, rebalance, missingness, validation/version/limits. Exact definitions and weights are not approved here.

## 17. Factor Preprocessing

`APPROVED BASELINE`: eligibility → point-in-time alignment → missingness → outliers → transform → cross-sectional standardization → optional sector/industry neutralization → direction → composite. Winsorization, robust z-scores/ranks/logs and thresholds are proposed per characteristic and fit within formation/training data. Missing stays missing absent approved causal treatment; coverage is reported. Compare raw/neutralized variants. Diagnose correlation, VIF/clustering and duplicated concepts. Equal weights are the proposed transparent challenger; optimized weights require OOS evidence.

## 18. Factor Portfolio Construction

Proposed validation portfolios: top-minus-bottom quintiles, deciles if breadth permits, long-only top quantile, equal/cap weighting, conditional sector/beta neutrality. Record formation/cutoff, execution lag/price, hold/rebalance, eligibility, delisting/missingness, turnover, gross/net costs. Use “research replication,” “project-specific factor,” or “independently constructed characteristic portfolio”; never claim official replication without equivalent universe, breakpoints, fields, timing, and method.

## 19. Asset-Pricing Models

For excess return `R_i-R_f`: CAPM `= α+β_M MKT+ε`; FF3 adds `SMB,HML`; Carhart adds momentum `UMD`; FF5 adds `RMW,CMA`. q-factor is conditional; custom models require change control.

Models declare test asset, factor provenance/region/units/frequency, configurable estimation window, assumptions, and interpretation. OLS baseline uses HC/HAC (Newey–West) where appropriate and clustering only when panel structure justifies it. Output alpha/loadings, SEs, t/p values, CIs, R²/adjusted R², AIC/BIC, observations, residual and rolling-stability diagnostics. Statistical significance alone is not economic importance.

## 20. Statistical Validation

Use descriptive/missingness analysis, correlations/VIF, appropriate stationarity/residual/autocorrelation/heteroskedasticity tests, robust/block-bootstrap CIs, subperiod/regime analysis, multiple-testing correction, and sensitivity to universe/window/preprocessing/cost/source. Proposed policy is Section 6; disclose adjusted and unadjusted results, selection, families, magnitude, CI, and sample size.

## 21. Factor Scoring Engine

Versioned component/composite scores carry raw/transformed values, direction, coverage, availability/formation time, and explanation. Weights are configuration-controlled; arbitrary percentages are prohibited. Proposed baseline: equal-weight approved available components subject to owner-approved minimum coverage and explicit missing-weight behavior; compare broad and sector-relative scores OOS.

## 22. Machine-Learning Scope

`APPROVED BASELINE` sequence: linear, ridge, lasso/elastic net, justified logistic, random forest, XGBoost; LightGBM/CatBoost conditional; no v1 deep learning. Targets may be next-period excess return/rank, probability of benchmark outperformance, volatility, or risk class; ranking/calibrated probabilities are proposed over noisy raw-return forecasts.

Use rolling/expanding splits without shuffle. Fit selection/scaling/imputation/tuning only on training data. Compare naive, linear, and factor challengers. Report predictive/rank/calibration metrics, net economic backtests, stability, turnover, drift, and regimes. Complexity requires stable incremental value.

## 23. Explainable AI

Report coefficients for linear models; permutation importance and SHAP for tree models on the exact fitted pipeline; cautious partial dependence; local/global explanations with model/fold/cutoff/reference/version. Test signs/ranks across folds, time, sectors, regimes. SHAP is not causal; correlation distorts attribution and importance may be unstable. LIME is deferred absent need.

## 24. Portfolio Construction

| Method | Objective/inputs | Principal limitation |
|---|---|---|
| Equal/inverse-vol | Transparent count or volatility allocation | Ignores return/correlation partly |
| Min variance | Minimize `w'Σw` | Covariance/concentration sensitivity |
| Mean–variance/max Sharpe | Trade expected return and risk | Noisy expected returns/nonlinearity |
| Black–Litterman | Combine equilibrium prior and views | Subjective prior/views/confidence |
| Risk parity | Balance component risk | Covariance and budget dependence |
| HRP | Cluster then recursively allocate | Linkage/order instability |
| CVaR | Minimize/constrain tail loss | Scenario-tail instability |

All use explicit constraints and benchmarks and return weights, objective/status, input versions, exposures, checks, diagnostics/failure. Black–Litterman must define equilibrium prior, risk aversion, covariance, `P`, `Q`, confidence/`Ω`, `τ`, posterior, and temporal cutoff. No external project code/results without provenance review.

## 25. Portfolio Constraints

`APPROVED BASELINE`: long-only and unlevered, with short selling and leverage disabled. Configurable maximum position/sector deviation, turnover/liquidity controls, and explicit costs remain proposed for Phase 4; exact bounds are `OPEN — OWNER DECISION REQUIRED`. System supports min/max, gross/net, country/factor/tracking-error, holdings count, minimum trade, cash, leverage, and short availability only where later authorized. Units/tolerances are explicit; infeasibility fails diagnostically and never relaxes silently.

## 26. Expected Return and Covariance Estimation

Expected-return candidates: historical mean diagnostic, factor-implied, Black–Litterman, ML-rank mapping, shrinkage/robust. Covariance: sample, Ledoit–Wolf, EWMA, factor-model, conditional robust. Declare window/frequency/missingness/annualization/minimum observations/cutoff/version. Check finite, symmetric, PSD, conditioning and repair magnitude. Named fallback policies record failure and alternative or stop; never silently replace.

## 27. Backtesting

Separate signals, formation, orders, execution, accounting, holdings, valuation, metrics, reporting. Record warm-up/training cutoff, rebalance decision, next eligible fill/price, hold/retrain schedule, fees/spread/slippage, turnover, cash/RF, dividends/actions, delistings, stale/missing prices, benchmark, capital, gross/net. Ledger reconciles cash, positions, costs, actions, NAV. Prohibit final weights over history, future estimates, unavailable-close fills, silent drops, valueless disappearance, and unsupported annualization.

## 28. Performance Metrics

Cumulative return is `∏(1+r_t)-1`; CAGR uses elapsed years; volatility uses configured periods/year; Sharpe uses matched RF; Sortino documents target/downside; Calmar uses absolute max drawdown; drawdown is `V_t/max(V_≤t)-1`. Also alpha/beta, information ratio/tracking error, hit rate, capture, turnover, and feasible shortfall/active share. Every metric states frequency, annualization, RF/benchmark, gross/net, sample/minimum, CI where defensible. Insufficient metrics are unavailable, not zero.

## 29. Risk Engine

Historical/parametric VaR, ES, rolling volatility/beta, tracking error, downside deviation, drawdown, factor/marginal/component risk, concentration/liquidity; Monte Carlo conditional. Confidence/horizon configurable; positive-loss convention explicit. State method/window/distribution/currency/as-of/run. Components reconcile. Where sample permits, VaR tests include exception count, Kupiec coverage and Christoffersen independence; traffic lights only when correctly defined. VaR is not maximum loss.

## 30. Scenario and Stress Analysis

Historical replay may cover 2008, 2011, 2015 China correction, 2020 COVID, 2022 tightening only within validated coverage. Hypothetical market/rate/inflation/oil/volatility/factor/liquidity shocks require units and propagation assumptions. Monte Carlo is deferred pending calibration/dependence validation. Distinguish instant shock, historical path, simulation; disclose unmapped exposure. Scenarios are not forecasts.

## 31. Performance Attribution

As data permits: total/active return; Brinson allocation/selection/interaction; sector/security/factor/cost; conditional country/currency. Distinguish arithmetic and approved multi-period geometric linking. Effective-dated holdings/benchmark/returns/classes/trades/FX must align. Reconcile within configured tolerance; unresolved residual can block publication.

## 32. System Architecture

Conceptual packages are not authorization to create them.

| Layer/package | Responsibility | May depend on / must not depend on |
|---|---|---|
| `config`, `core` | Validation, IDs, exceptions, run/time protocols | Standard primitives / providers, analytics, UI |
| `data.sources` | Approved retrieval to raw/manifests | core/config/provider clients / research/UI |
| `data.schemas,validation,storage,lineage` | Contracts, promotion, persistence, lineage | core/config / conclusions/UI |
| `factors,asset_pricing,scoring` | Characteristics, models, scores | validated data/core/config / UI/providers |
| `ml,portfolio,backtesting` | Pipelines, optimization, ledger | domain/data services / UI/direct ingestion |
| `risk,attribution,scenarios` | Reconciled analytics | holdings/returns/factors / UI/providers |
| `reporting` | Render validated contracts | services/domain output / new calculations |
| `api,dashboard` | Validate/present application services | service/reporting / domain reimplementation |
| `utilities` | Narrow cross-cutting helpers | core/stdlib / orchestration |

Direction: UI/API → application services → domain → data access/storage → core/config. Lower layers never import higher; core never imports FastAPI/Streamlit.

## 33. Storage Architecture

`APPROVED BASELINE` for Phase 1: original raw formats; immutable content/config/schema-addressed Parquet; replaceable DuckDB local catalog/query views; YAML/TOML configuration; authenticated JSON v5 dataset manifests, v4 promotion envelopes and lifecycle lineage, append-only lifecycle events with independent head checkpoints, and structured logs. PostgreSQL remains a later multi-user option, Redis remains deferred, and later report/model artifact formats are not authorized by this storage decision.

## 34. Configuration Architecture

Future domains: project, sources, universe, calendars, factors, asset pricing, ML, portfolio, backtesting, risk, scenarios, API, dashboard, logging. Require schema/version validation, relative paths, explicit units/defaults, documented environment precedence, no secrets/magic numbers, cross-field checks, immutable run snapshot/hash. Add only active-phase files; retain current base foundation.

## 35. Experiment and Run Metadata

Every model/prediction/portfolio/backtest/risk/report has run ID and parent IDs, Git commit/dirty state, package/dependencies, start/end/status, config path/version/hash/snapshot, data manifest/date range, universe version, seed/determinism limits, model/training IDs, outputs/hashes, warnings/errors, environment. Failed runs remain auditable and cannot publish partial success.

## 36. Output Contracts

Families: quality/data cards, factor matrices/returns/diagnostics, pricing tables, scores/predictions/model cards, weights/transactions/backtests, risk/attribution/scenarios, research reports. Every artifact includes generation time, run, cutoff/period, universe/version, config/hash, units/currency/frequency, method version, gross/net, validation/warnings, parents. Rendering cannot alter values.

## 37. API Boundary

Conceptual versioned `/health`, `/metadata`, `/data-quality`, `/factors`, `/asset-pricing`, `/scores`, `/predictions`, `/portfolios`, `/backtests`, `/risk`, `/attribution`, `/scenarios`, `/reports`. Future FastAPI calls application services, validates/authenticates, returns provenance/status, paginates, and distinguishes unavailable/failed/not-generated/empty. No research calculations or demo fallback.

## 38. Dashboard Boundary

| Page | Question/output | Required warnings/download |
|---|---|---|
| Overview/System Metadata | Runs, freshness, lineage/environment | stale/unapproved/dirty; metadata |
| Data Quality/Market Explorer | Fitness, coverage, validated history | blocks/actions/currency/source; report/data |
| Factor Research/Asset Pricing | Definitions, spreads, estimates/diagnostics | method, missingness, inference, cost; tables |
| Security Scoring/Explainable ML | Components, predictions, explanations | not recommendation/causal; score/model card |
| Portfolio Lab/Backtesting | Weights, feasibility, ledger outcomes | estimate, constraint, bias, gross/net; config/ledger |
| Risk/Attribution/Scenarios | Risk sources, reconciled effects, shocks | conventions/residual/not forecast; reports |
| Research Reports | Validated publishable artifacts | draft/status; controlled download |

Future Streamlit renders services only; it never fits, optimizes, backtests, or recomputes metrics.

## 39. Reporting Standards

Charts include title, period, universe, benchmark, axes/units, legend, source, methodology, validation/gross-net, run/report ID. Tables include units/currency/frequency, sample, period, missingness, justified uncertainty/significance, gross/net, benchmark. No decorative claims, misleading axes, hidden failures, or undefined significance stars.

## 40. Software Quality Requirements

Correct financial invariants; locked reproducibility/run lineage; layered typed documented interfaces; offline testability/current 90% coverage floor; structured redacted observability; no critical secret/license issue; measured—not invented—performance goals; supported portable clean install; actionable usability; immutable audit evidence. Ruff lint/format, strict Mypy core, tests, secret scan, docs consistency and diff review are gates.

## 41. Testing Strategy

Unit, integration, provider contract, schema, temporal, quality, numerical, regression, useful property-based, optimizer, ledger, risk, API, dashboard smoke, E2E, reproducibility, performance. Critical tests reject duplicate/future data, preserve raw hashes, reconcile actions/returns/weights/cash/NAV/costs/risk/attribution, preserve infeasibility, distinguish unavailable API results, and reproduce deterministic hashes. Approved synthetic fixtures are isolated/labeled and never feed empirical outputs.

## 42. Model Risk Management

Every model/optimizer records purpose, owner/version, theory, inputs, assumptions, intended use, estimation period, validation, limits/failures, challenger, monitoring, deprecation. ML needs model cards; complex optimizer settings analogous records. Statuses: research, validated research, production-like (not regulated production), deprecated. Promotion requires evidence, not good backtest performance.

## 43. Bias and Limitation Register

| Limitation | Impact/mitigation | Residual/phase |
|---|---|---|
| Survivorship/constituents | Upward bias; point-in-time history or restrict claim | High / 1,4 |
| Free-data quality | Gaps/revisions; manifests, checks, cross-source samples | Medium-high / 1 |
| Fundamental timing | Leakage; actual filings/vintages or disclosed lag | Medium / 1–2 |
| Actions/delistings/reconstitution | Wrong total/relative returns; event and membership history | Medium-high / 1,4 |
| Snooping/multiple tests | False findings; preregister families, OOS, FDR | Medium / 2–5 |
| Crowding/nonstationarity/regimes | Decay; rolling/subperiod/capacity diagnostics | High irreducible / 2–5 |
| Estimation/optimizer error | Extreme weights; shrinkage/constraints/challengers | Medium / 4 |
| Cost/capacity/liquidity | Overstated net results; screens/grids/disclosure | Medium-high / 4–5 |
| Interpretability | Unstable/noncausal; simple models/exact pipelines/stability | Medium / 5 |
| Historical/live gap | Past not future/live; stress and no performance guarantee | High irreducible / 4–7 |

## 44. Seven-Phase Implementation Plan

| Phase | Scope and outputs | Blockers/exclusions | Gate deliverables |
|---|---|---|---|
| Phase 1 — Institutional Data Platform | Master, approved adapters, immutable raw, schemas, validation, manifests, lineage, calendars, timing, approved Parquet/DuckDB → validated data/cards | Market/universe/source/license; no factors | Architecture/contracts; offline temporal/immutability/quality tests; fit-for-purpose data |
| Phase 2 — Multi-Factor Research Engine | Definitions, features, preprocessing, scores, portfolios, diagnostics/matrices | Coverage/timing; no pricing conclusions/optimizer | Method/lineage; factor/numerical/temporal tests; reviewable factors |
| Phase 3 — Asset-Pricing Research Platform | CAPM/FF3/Carhart/FF5, inference, comparison, rolling stability | q-factor conditional; no optimizer | Model/inference docs/tests; reproducible diagnosed tables |
| Phase 4 — Portfolio Construction and Institutional Backtesting | Estimators, methods, constraints, execution/cost ledger, benchmarks | Mandate/cost/capital; no silent fallback | Optimizer/backtest specs; constraint/accounting/timing tests; reconciled OOS |
| Phase 5 — Risk Analytics and Explainable Machine Learning | Risk, scenarios, attribution, time-aware ML, explanation/cards | Deep learning excluded | Methods/cards; risk/reconciliation/leakage/stability tests |
| Phase 6 — API, Dashboard, and Research Workspace | Services, versioned API/UI, provenance/downloads | Deployment/access; no duplicated analytics | Contracts/security/UI docs; smoke/integration tests |
| Phase 7 — Production Hardening and Research Publication | CI, approved Docker/deployment, E2E, performance/security/license review, docs/report/audit | No scope creep | Runbooks/cards/report; clean regeneration and owner sign-off |

Each phase reviews governance/current Git/risks first and closes with evidence, documentation, unresolved risks, and non-fabrication confirmation.

## 45. Phase Acceptance Criteria

- **P1:** unchanged raw hashes; manifested partial failures/checksums/licenses; unique valid keys/mappings/times; quarantine blocks promotion; offline tests; lineage; no fake data; matching docs.
- **P2:** formulas/directions/versions; point-in-time/training-safe preprocessing; coverage/outliers/turnover/costs/timing; accurate official/project labels; temporal/numerical tests.
- **P3:** approved equations/alignment; verified robust inference/diagnostics; explicit units/windows/counts; past-only rolling; uncertainty/economic magnitude; reproducible failure-aware outputs.
- **P4:** documented objectives/constraints; feasible tolerance and diagnostic infeasibility; past-only estimates; reconciled ledger/actions/cash/cost/NAV; gross/net/benchmark distinction; sensitivity tests.
- **P5:** risk conventions/components and attribution reconcile; scenarios not forecasts; ML splits/features/tuning time-safe; challengers, net/stability evidence, exact-pipeline explanations, cards/tests.
- **P6:** service-only versioned interfaces; validated access/inputs; provenance/freshness; unavailable distinct from empty; downloads match artifacts; security/contract/smoke tests.
- **P7:** locked clean setup/full suite; repeatable approved deployment; no critical dependency/license/secret/security issue; measured performance; aligned docs/code; report regeneration and owner sign-off.

## 46. Definition of Done

All approved phases pass gates; no critical integrity defect or known leakage remains; clean setup/tests pass; assumptions are configurable; lineage is complete; gross/net are distinct; docs match code; no fabrication/silent fallback exists; limitations are disclosed; approved report regenerates from manifests. Deferred/out-of-scope items are not required.

## 47. Owner Decision Register

| Decision | Recommendation | Status | Required before |
|---|---|---|---|
| Market/universe | US common equities; large/mid-cap; point-in-time inputs required for historical claims | `APPROVED BASELINE` | Phase 1 |
| Security types | Primary common class; financials included; ETFs/ETNs/CEFs/ADRs/preferred/REITs/warrants/rights/units/SPAC units/funds/debt/derivatives/crypto excluded | `APPROVED BASELINE` | Master schema |
| Benchmark/base currency/start | Broad S&P 500 total-return proxy / USD / 2010-01-01 | `APPROVED BASELINE` | Phase 1 |
| Historical constituents | Licensed/owner source | `OPEN — OWNER DECISION REQUIRED` | Primary historical claim |
| Provider priority/budget/licenses | Yahoo Finance, Kenneth French, FRED, SEC EDGAR, owner-supplied; local owner use/no redistribution | `APPROVED BASELINE` | Adapters |
| Fundamentals | SEC EDGAR or owner-supplied data | `APPROVED BASELINE` | Phase 1 |
| RF proxy/calendar/time | DGS3MO/FRED; XNYS; UTC timestamps and exchange-local dates | `APPROVED BASELINE` | Phase 1 |
| Return/action convention | Simple total return, validated adjustments, raw retained | `PROPOSED — OWNER APPROVAL REQUIRED` | Phase 1 |
| Fundamental lag | Actual availability; conservative disclosed fallback | `PROPOSED — OWNER APPROVAL REQUIRED` | Phase 1/2 |
| Rebalancing | Monthly | `APPROVED BASELINE` | Phase 2/4 |
| Factor challenger weights | Equal-weight candidate | `PROPOSED — OWNER APPROVAL REQUIRED` | Phase 2 |
| Preprocessing thresholds | Decide per factor after coverage analysis | `OPEN — OWNER DECISION REQUIRED` | Phase 2 |
| Significance | 1/5/10% report; FDR families | `PROPOSED — OWNER APPROVAL REQUIRED` | Phase 2/3 |
| Capital and position/sector/turnover/liquidity bounds | Decide after universe/capacity analysis | `OPEN — OWNER DECISION REQUIRED` | Phase 4 |
| Short/leverage | Disabled | `APPROVED BASELINE` | Phase 4 |
| Cost model | Configurable bps + optional spread/slippage | `PROPOSED — OWNER APPROVAL REQUIRED` | Phase 4 |
| ML target/horizon | Rank or outperformance probability candidate | `OPEN — OWNER DECISION REQUIRED` | Phase 5 |
| Storage | Immutable raw + versioned Parquet + DuckDB catalog | `APPROVED BASELINE` | Phase 1 |
| Retention/privacy/access | Retain raw until owner deletion; local owner only; no public serving/redistribution | `APPROVED BASELINE` | Phase 1/6 |
| Deployment | Local first; PostgreSQL later if needed | `PROPOSED — OWNER APPROVAL REQUIRED` | Phase 6 |
| Deadline | Owner schedule | `OPEN — OWNER DECISION REQUIRED` | Planning |
| License | MIT; copyright (c) 2026 AMIT KUMAR DUDI | `APPROVED BASELINE — MIT` | Effective baseline |

Delay blocks the named phase; it never authorizes assumption. Relevant sections explain options and consequences.

## 48. Traceability Matrix

| Question | Data → module → output | Validation | Phase |
|---|---|---|---|
| RQ1 | Market/actions/fundamentals → factors → spreads | Timing, HAC/bootstrap/FDR/costs | 1–2 |
| RQ2 | Test assets/RF/factors → pricing → comparisons | Robust inference/diagnostics | 3 |
| RQ3 | Long histories → factors/pricing → stability | Break/subperiod sensitivity | 2–3 |
| RQ4–5 | Scores/covariance/benchmark/orders → portfolio/backtest → ledger/net/cost grid | Walk-forward/constraints/accounting | 4 |
| RQ6 | Returns/macro vintages → factors/risk → conditional results | Ex ante labels/CIs | 2–5 |
| RQ7 | Features/targets → ML/backtest → predictions/cards | Time splits/challengers/net | 5 |
| RQ8–9 | Holdings/factors/classes/trades → risk/attribution → contributions | Sum/reconciliation | 4–5 |
| RQ10 | Alternative inputs/models → analytical domains → sensitivity | Stability/challengers | 3–5 |

## 49. Project Risk Register

| Risk | Likelihood/impact | Mitigation | Owner/phase/residual |
|---|---|---|---|
| Missing constituents/survivorship | High/Critical | Licensed history or restrict claim | Data / 1,4 / High |
| Fundamental timing | High/Critical | Filings/vintages or disclosed lag | Validation / 1–2 / Medium |
| Rate limits/outages | High/Medium | Manifest retries/partial state/raw cache | Data / 1 / Medium |
| Corporate actions | Medium/High | Reconcile/cross-check/quarantine | Validation / 1 / Medium |
| Scope creep | High/High | Gates/exclusions/change control | Owner / all / Medium |
| ML overfit | High/High | Time-aware challengers/stability/net tests | Model validator / 5 / Medium |
| Optimizer instability | High/High | Shrinkage/bounds/sensitivity/diagnostics | Portfolio / 4 / Medium |
| Cost understatement | High/High | Cost grids/liquidity/capacity disclosure | Portfolio / 4 / Med-high |
| Duplicated calculations/UI-first | Medium/High | Layer/service rules and contracts | Architecture / 2–6 / Low |
| Dependency bloat | Medium/Medium | Active-phase need/license review | Architecture / all / Low-med |
| Reproducibility failure | Medium/Critical | Locks/manifests/hashes/clean setup | Repro / all / Low-med |
| Secret exposure | Medium/Critical | Env/redaction/scans/rotation | Security / 1,6–7 / Low-med |
| Deployment complexity | Medium/High | Local-first/measured need | Owner / 6–7 / Low |
| Data license breach | Medium/Critical | Rights register/export control | Owner/legal / 1,7 / Medium |

Likelihood is qualitative planning, not empirical frequency; role owners require later assignment.

## 50. Change Control

Every change records reason, affected questions/phases, migration/backward compatibility, data/schema/lineage impact, test/validation impact, documentation impact, decision-register update, and semantic version increment. Only explicit owner record promotes decisions. Existing runs retain their specification version. Wording clarification may not silently change status, numbers, scope, methods, or gates.

## 51. Final Approved Baseline

Phase 1 owner-approved baselines are: US common equities/USD; daily research frequency; 2010 onward; large/mid-cap with point-in-time inputs required for historical claims; broad S&P 500 total-return proxy; approved named sources; DGS3MO/XNYS/UTC; immutable raw plus Parquet/DuckDB; and local owner-only access with no redistribution. Later-phase methods and any item still marked proposed/open remain unauthorized until their named phase and owner decision. This clarification records prior explicit owner decisions and does not approve later-phase defaults.

Phases 1, 2, and 3 are implemented, assured, and complete under the governing documents and applicable owner instructions. Phase 4 is formally authorized as the next phase but has not started. Proposed/open choices in the Owner Decision Register remain unchanged and unauthorized until their affected use requires explicit owner resolution.
