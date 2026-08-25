# Project Interview Defense Pack

This pack contains 105 questions for MSc Finance, Financial Engineering, quantitative-finance, and technical interviews. Answers defend the released evidence without implying persistent alpha, causal effects, professional investment experience, or proprietary-data equivalence.

## Level 1 — Project overview

### 1. What is the project?

It is an independent, institutional-style US-equity research platform connecting point-in-time data, factor construction, asset-pricing tests, constrained portfolios, walk-forward ML, and authenticated research delivery.

### 2. What question does it ask?

It asks which quantitative conclusions survive once historical identity, filing availability, transaction costs, temporal leakage, and reproducibility are enforced.

### 3. Why did you build it?

I wanted to understand the complete empirical-research chain rather than study models on a pre-cleaned dataset.

### 4. What is the strongest contribution?

The evidence architecture: unsupported inputs or broken lineage fail closed instead of silently producing a result.

### 5. What real data scale did you reach?

I screened 822 candidates, accepted 487 equities, and retained 715,447 market and 37,273 point-in-time fundamental observations.

### 6. What are the analytical phases?

Governed data, factors, asset pricing, portfolios/risk, ML, delivery, assurance, and final dissemination.

### 7. What makes it more than a backtest?

It includes identity and availability controls, immutable publications, econometric inference, multiple portfolio methods, temporal ML, tamper tests, and reproducible delivery.

### 8. What did you find?

Multifactor models improved in-sample fit, costs reduced every portfolio result, and ML did not show stable incremental predictive or after-cost value.

### 9. Is it a production trading system?

No. It has no brokerage, live execution, streaming-data SLA, or claim of production deployment.

### 10. Why call it institutional-style?

The term describes its controls—lineage, point-in-time evidence, governance, model comparison, costs, audit, and fail-closed publication—not actual institutional deployment.

### 11. What was frozen before performance?

The 487-equity universe and the 5/10/20 bps transaction-cost sensitivity schedule.

### 12. What was the final assurance result?

Three hundred tests passed with 90.59% branch-aware coverage, plus lint, typing, lock, catalog, restart, tamper, and security checks.

### 13. What result are you most cautious about?

The Phase 4 performance because it covers only 32 months and factor portfolios rather than directly investable security portfolios.

### 14. What result are you most confident about?

That the ML evidence does not establish stable incremental value: all aggregate IC intervals include zero.

### 15. What did you personally learn?

That data timing and research design often dominate model sophistication, and that a defensible negative answer is a successful research outcome.

## Level 2 — Finance fundamentals

### 16. State CAPM.

Expected excess return equals beta times expected market excess return; in time-series form, the intercept tests unexplained average return under the model.

### 17. What is beta?

The sensitivity of an asset or portfolio return to market return, commonly estimated as covariance with the market divided by market variance.

### 18. What does alpha mean here?

It is a model intercept on project-specific diagnostic portfolios. It is descriptive and not proof of skill, causality, or investability.

### 19. Why use multifactor models?

They test whether systematic dimensions beyond market beta explain common return variation and reduce omitted-risk structure.

### 20. What do size, value, and momentum represent?

They are return spreads associated with market capitalization, valuation characteristics, and prior relative performance; their interpretation can include risk, behavior, or data effects.

### 21. What is FF3?

CAPM augmented with size and value factors.

### 22. What does Carhart 4 add?

A momentum factor to the Fama-French three-factor model.

### 23. What does FF5 add?

Profitability and investment factors to market, size, and value.

### 24. What is the q-factor intuition?

Expected returns relate to investment and profitability through firms’ investment decisions and the cost of capital; this project uses its configured mapping rather than claiming a universal implementation.

### 25. Why was no Custom model estimated?

No custom equation was approved or configured, so inventing one after observing data would violate governance.

### 26. What is the Sharpe ratio?

Excess return per unit of total return volatility. It is scale-free but sensitive to sample length, non-normality, and estimation error.

### 27. What is maximum drawdown?

The largest peak-to-trough decline in cumulative wealth over the observed path.

### 28. What is tracking error?

The volatility of active return relative to a benchmark.

### 29. What is the information ratio?

Mean active return divided by tracking error; it measures benchmark-relative return per unit of active risk.

### 30. Why do transaction costs matter?

Turnover converts small forecast improvements into implementation drag; ignoring it can reverse the economic interpretation of a signal or allocator.

## Level 3 — Econometrics

### 31. What assumptions support OLS unbiasedness?

Correct linear specification, no perfect multicollinearity, and zero conditional mean of errors; homoskedasticity is needed for classical efficiency and standard errors, not unbiased coefficients.

### 32. What is heteroskedasticity?

Error variance changes with observations. OLS coefficients may remain unbiased, but conventional standard errors become unreliable.

### 33. What are heteroskedasticity-consistent standard errors?

Sandwich estimators such as HC variants that estimate coefficient uncertainty without assuming constant error variance.

### 34. Why use Newey-West/HAC inference?

It adjusts covariance estimates for both heteroskedasticity and serial correlation up to a chosen lag structure.

### 35. What is autocorrelation?

Correlation of regression errors across time, which can understate conventional uncertainty when ignored.

### 36. What is multicollinearity?

Strong correlation among regressors that inflates coefficient uncertainty and makes individual effects unstable without necessarily reducing fitted prediction.

### 37. R-squared versus adjusted R-squared?

R-squared never falls when regressors are added; adjusted R-squared penalizes model dimension and is more useful for comparing nested fit.

### 38. Why does higher adjusted R-squared not prove a better investment model?

It is an in-sample explanatory statistic and says nothing by itself about stability, costs, timing, or out-of-sample economic value.

### 39. What is a t-statistic?

An estimate divided by its estimated standard error, used to assess distance from a null value under an inference model.

### 40. What is multiple-testing risk?

Testing many factors or models increases false discoveries unless family-wise or false-discovery controls and preregistered families are used.

### 41. Why use block bootstrap methods?

They preserve local time dependence better than independently resampling observations.

### 42. What is a confidence interval telling you?

Under repeated samples and the stated method, it describes a range generated by a procedure with specified coverage; it is not a probability that this fixed parameter lies inside.

### 43. What does an IC interval including zero imply?

The evidence cannot distinguish the aggregate rank association from zero at the interval’s stated confidence level.

### 44. What is a structural break?

A material change in model parameters or data-generating relationships across time.

### 45. Why are H1 and H3 inconclusive?

The publications do not complete the full preregistered net-cost/FDR decision for H1 or corrected regime/break multiplicity decision for H3.

## Level 4 — Data engineering

### 46. What is point-in-time data?

Data tagged by when it was actually available to a researcher, not merely the economic period it describes.

### 47. Period end versus availability date?

Period end identifies the reporting interval; availability date determines when the filing could legally enter a historical decision.

### 48. What is look-ahead bias?

Using information in a historical decision that was not available at that decision time.

### 49. What is survivorship bias?

Constructing history from securities that survive to the present, thereby excluding failures and changing the historical opportunity set.

### 50. How did the project address delistings?

It retained lifecycle evidence but excluded candidates whose terminal treatment could not be resolved defensibly.

### 51. Why is ticker insufficient as identity?

Tickers can be reused or changed and may identify different listings or share classes across time.

### 52. What is a CIK?

The SEC’s issuer identifier. It anchors filings to issuers but does not by itself uniquely identify every listed security or share class.

### 53. How do issuer and listing identity differ?

An issuer can have multiple securities or listings; research returns must map issuer facts to the correct effective-dated listed security.

### 54. Why check split basis?

Price and share histories must use compatible adjustment bases; otherwise market capitalization and returns can jump mechanically.

### 55. Why preserve accession and taxonomy metadata?

They make each fundamental observation traceable to a specific filing and accounting concept definition.

### 56. What is data lineage?

The recorded graph from source evidence through transformations and upstream publications to a downstream result.

### 57. What does immutable raw data mean?

Acquired source bytes are not overwritten; corrections produce new evidence or transformations while preserving audit history.

### 58. Why were 335 candidates rejected?

They failed attribution, splice, identity, share, terminal-event, split-basis, asset-type, venue, or fundamental-projection requirements.

### 59. Why not backfill current SEC mappings?

Current mappings do not prove historical listing identity and would create survivorship and look-ahead risk.

### 60. What does fail closed mean?

Missing or inconsistent evidence blocks authentication or estimation instead of triggering a permissive fallback.

## Level 5 — Portfolio theory

### 61. What is minimum variance?

The fully invested feasible portfolio that minimizes estimated variance, independent of expected-return estimates.

### 62. What is mean-variance optimization?

Choosing weights by trading expected return against covariance-based risk under constraints.

### 63. Why is mean-variance fragile?

Expected returns are noisy, covariance estimates are uncertain, and small input changes can create large weight changes.

### 64. What is maximum Sharpe optimization?

Selecting feasible weights to maximize estimated excess return per unit of volatility.

### 65. What is maximum diversification?

Maximizing the ratio of weighted constituent volatilities to portfolio volatility, encouraging imperfectly correlated risk sources.

### 66. What is risk parity/ERC?

A portfolio designed so constituents contribute approximately equal amounts of total risk rather than equal capital.

### 67. What is HRP?

Hierarchical Risk Parity clusters correlated assets and recursively allocates risk without inverting a potentially unstable covariance matrix.

### 68. What is CVaR?

Expected loss conditional on losses exceeding the VaR threshold; it focuses on tail severity and is coherent under standard conditions.

### 69. VaR versus CVaR?

VaR is a loss quantile; CVaR averages losses beyond that quantile and better reflects tail magnitude.

### 70. What is Black-Litterman conceptually?

It combines an equilibrium prior with investor views and uncertainty to stabilize expected returns. It existed as a framework but was not a configured empirical publication method here.

### 71. Why long-only and unlevered?

Those were governed mandate constraints that limit implementation complexity and prevent performance-driven mandate changes.

### 72. How is turnover used?

It measures traded weight between portfolio states and scales one-way proportional costs.

### 73. Why freeze costs before results?

It prevents selecting favorable costs after seeing which portfolios need them to look attractive.

### 74. Which method had the highest observed Sharpe?

CVaR at 1.667 under BASE costs, but that short-window descriptive ranking is not evidence of future superiority.

### 75. What did H5 conclude?

Partially supported: constrained methods changed risk and concentration trade-offs, but stable superiority was not established over a sufficiently long OOS period.

## Level 6 — Machine learning

### 76. What was the target?

Twenty-one-trading-session forward security total return minus SPY forward total return.

### 77. Why a benchmark-relative target?

It asks the model to rank cross-sectional performance beyond broad market movement rather than predict the market level.

### 78. Why monthly decision observations?

The research design retrains and rebalances monthly; daily feature rows would pseudo-replicate nearly identical decisions and overstate sample size.

### 79. Why use a 60-month training window?

It provides the governed minimum five-year initial history while allowing relationships to update through walk-forward evaluation.

### 80. Why a 12-month validation window?

It separates hyperparameter selection from the next one-month test while covering a meaningful range of market conditions.

### 81. What is purging?

Removing training or validation observations whose label horizons overlap a later evaluation period.

### 82. What is an embargo?

A gap around evaluation boundaries that reduces leakage from adjacent observations; this study uses a stricter one-month embargo.

### 83. Why Spearman rank IC?

The downstream decision ranks securities, so monotonic cross-sectional ordering matters more than exact return-level calibration.

### 84. Why include zero and historical-mean baselines?

They test whether complex models add value beyond no signal and simple historical information.

### 85. Why include linear and regularized models?

They are interpretable challengers; Ridge stabilizes correlated coefficients and Elastic Net combines shrinkage with variable selection.

### 86. Why Random Forest?

It captures nonlinearities and interactions without requiring a parametric functional form, while remaining a bounded tabular-data challenger.

### 87. Why XGBoost?

Boosted trees are strong tabular predictors, but they require strict temporal evaluation and bounded tuning to avoid overfitting.

### 88. Why only two features?

Only the approved authenticated book-to-market and momentum features were used; adding features after weak results would change the study.

### 89. Did ML fail technically?

No. The pipeline trained, authenticated, and evaluated correctly. The empirical hypothesis was not supported.

### 90. Why did ML not establish value?

Signals were weak and unstable: aggregate IC intervals included zero, and after-cost returns were not consistently positive across folds.

## Level 7 — Research defense

### 91. Why should I trust the results?

Because selection and costs were frozen before performance, timing is explicit, publications bind lineage and configuration, reads fail closed, and adversarial tests cover restart and tampering. Trust remains conditional on disclosed data limits.

### 92. Why no CRSP?

The project used accessible free/public sources. I therefore disclose source-selection limits rather than claim CRSP-grade historical coverage or identifiers.

### 93. Why no Compustat?

Fundamentals came from governed SEC evidence. This increases accessibility and traceability but creates concept, coverage, and reconciliation limitations absent from standardized proprietary panels.

### 94. Why only 32 months in Phase 4?

That is the defensible overlap supported by the authenticated upstream factor-portfolio evidence; extending it by backfilling would weaken temporal integrity.

### 95. Why is equity issuance unavailable?

Net-equity-issuance and shareholder-equity evidence cannot be reconciled consistently from the approved SEC concepts without zero-filling or fabrication.

### 96. Why does the project matter if ML adds no alpha?

It demonstrates correct hypothesis testing, temporal validation, economic reconciliation, and the discipline to retain a negative result—skills more transferable than one favorable backtest.

### 97. What is the biggest limitation?

The free/public-data universe is source-availability selected, with limited early breadth and no CRSP/Compustat equivalence.

### 98. What surprised you most?

Real data exposed cross-phase integrity defects that extensive synthetic tests had not revealed, especially benchmark-calendar and monthly-sampling issues.

### 99. Could the positive Phase 4 returns be data mining?

Yes, sampling variation and method comparison remain concerns. That is why I describe them as short-window results and do not claim persistence.

### 100. Why not tune ML until it works?

Repeated adaptation to the same folds would convert evaluation data into training information and inflate false discovery.

### 101. What would you do with WRDS access?

Pre-register a replication using CRSP security identifiers, delisting returns, historical constituents, and Compustat fundamentals; reconcile it against this chain without overwriting the public-data study.

### 102. What would you improve first?

Extend the defensible out-of-sample horizon and independently replicate identities, delisting treatment, and factors with proprietary reference data—not add model complexity first.

### 103. Is SHAP an explanation of economic causality?

No. It attributes a fitted model’s prediction under assumptions about feature coalitions; it does not identify causal mechanisms.

### 104. How would you defend the term reproducible?

Code, configuration, dependencies, publication identities, checksums, and pipeline order are recorded. Reproduction still requires lawful access to the untracked source evidence.

### 105. Give the one-sentence defense of the project.

I built a research system designed to reject unsupported claims, and its strongest evidence is that it preserved weak and negative findings after real-data, cost, temporal, and adversarial checks.

## 10-Minute Interview Presentation

### 0:00–1:00 — Problem

“Many quantitative projects start from a clean panel. Mine asks what happens before that panel exists and whether downstream results survive realistic controls. I built a US-equity research platform where identity, filing availability, costs, temporal leakage, and publication integrity are part of the research design. The goal was not to guarantee alpha; it was to produce a result I could defend.”

### 1:00–2:00 — Data

“I screened 822 HF candidates before looking at performance and accepted 487: 372 Tier A and 115 Tier B. The panel contains 715,447 market rows and 37,273 point-in-time fundamental rows. Admission required attribution, compatible source splices, exact ticker/CIK evidence, share-basis checks, filing-time availability, and lifecycle treatment. Present mappings were never backfilled historically.”

### 2:00–3:00 — Architecture

“The chain moves from governed evidence to factors, asset pricing, portfolios, ML, delivery, assurance, and communication. Every publication binds checksums, configuration, code identity, lineage, lifecycle state, and upstream parents. A downstream reader cannot bypass authentication by opening a convenient table directly.”

### 3:00–4:30 — Factors

“I defined 48 factors and estimated 47. Equity issuance remained non-estimable because approved SEC inputs could not reconcile issuance and shareholder equity without fabrication. That refusal is important. Real data also exposed a benchmark-calendar defect: missing security sessions had made benchmark compounds differ. I corrected it so all portfolios use one authenticated calendar per holding period.”

### 4:30–5:30 — Asset pricing

“I compared CAPM, FF3, Carhart 4, FF5, and a configured q-factor mapping over 123 diagnostic portfolios. Mean adjusted R-squared rose from 0.063 for CAPM to roughly 0.26–0.30 for the multifactor models. I classify that as partial support for improved fit, not alpha, because stable out-of-sample economic improvement was not demonstrated.”

### 5:30–6:30 — Portfolios

“Before inspecting performance, I froze one-way costs at 5, 10, and 20 basis points. Eight long-only methods were evaluated. Under BASE costs, annualized returns ranged from 12.72% to 25.48% and volatility from 10.00% to 16.04%. Costs reduced every result. The window is only 32 months and uses factor portfolios, so I do not claim persistence.”

### 6:30–7:30 — Machine learning

“The ML study uses book-to-market and 12-minus-1 momentum to predict 21-session SPY-relative returns. It has 27,640 monthly decisions, 60 months of training, 12 months of validation, purging, a one-month embargo, and 17 test folds. Eight models include baselines, regularized linear models, Random Forest, and XGBoost.”

### 7:30–8:30 — Findings

“All aggregate IC intervals included zero. Random Forest had only a tiny positive mean after-cost result and was positive in 9 of 17 folds; other models were negative on average after costs. Therefore stable predictive and economic ML value was not established. Feature rankings also varied across explanation methods.”

### 8:30–9:30 — Limitations

“This is a free/public-data, source-selected universe, not CRSP/Compustat or historical-index replication. Early coverage is sparse, unresolved terminal events were excluded, Phase 4 is short, and ML uses two features. SHAP and scenarios are not causal. These limitations bound every claim.”

### 9:30–10:00 — What I learned

“The project taught me that credible quantitative finance is a chain of data, econometrics, portfolio logic, software controls, and judgment. Real evidence found defects that synthetic tests missed. The final release passed 300 tests with 90.59% branch-aware coverage, but the most important outcome was learning to defend a negative result instead of optimizing it away.”
