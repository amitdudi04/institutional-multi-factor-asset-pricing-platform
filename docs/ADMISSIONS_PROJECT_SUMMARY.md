# Admissions Project Summary

## Version 1 — 60 words

I built an institutional-style US-equity research platform combining point-in-time SEC fundamentals, historical market data, 48 factor definitions, five asset-pricing models, eight portfolio methods, and purged walk-forward machine learning. The study screened 822 securities, accepted 487, and passed 300 tests with 90.59% coverage. Its key finding was disciplined: costs mattered, while stable incremental ML value was not established under constraints.

## Version 2 — 150 words

I designed and validated a quantitative-finance research platform that connects data engineering, econometrics, portfolio theory, and machine learning. The system screened 822 US-equity candidates and froze a 487-security universe using identity, point-in-time SEC filings, share-basis checks, lifecycle evidence, and lineage. It defined 48 factors, estimated 47, compared CAPM with Fama-French 3, Carhart 4, Fama-French 5, and a q-factor mapping, and evaluated eight constrained portfolio methods under transaction costs preregistered before inspection. A purged monthly walk-forward study compared eight ML models on 27,640 observations. Multifactor models improved in-sample fit and costs materially reduced portfolio results, but ML confidence intervals included zero and stable after-cost incremental value was not established. Real data exposed cross-phase software defects, which I corrected with regression tests without weakening methodology. Final assurance passed 300 tests with 90.59% branch-aware coverage. The project strengthened my interest in finance where computational engineering supports, rather than replaces, research judgment.

## Version 3 — 300–400 words

I developed an independent institutional-style multi-factor asset-pricing and portfolio-research platform to explore a question that sits between computer science and empirical finance: how much confidence can we place in an equity-research result when historical identity, filing-time availability, transaction costs, temporal leakage, and reproducibility are treated as engineering constraints rather than footnotes?

The platform screened all 822 available HF Data Library stock candidates before examining analytical performance and accepted 487 equities—372 Tier A and 115 Tier B—using source attribution, ticker/CIK evidence, effective-dated listing mappings, point-in-time shares and fundamentals, split-basis checks, and lifecycle controls. The resulting panel contains 715,447 market observations and 37,273 fundamental observations across 18 fields. Raw evidence is immutable and every analytical publication binds checksums, configuration, code identity, lineage, and upstream parents.

On this foundation, I implemented 48 governed factor definitions, of which 47 were estimable. I deliberately left `equity_issuance` non-estimable because the available SEC evidence could not support it without zero-filling or fabrication. I compared CAPM with Fama-French 3, Carhart 4, Fama-French 5, and a q-factor mapping; multifactor models improved adjusted R-squared in-sample, but I did not interpret that as persistent alpha. I then evaluated eight long-only portfolio methods after freezing one-way transaction-cost assumptions at 5, 10, and 20 basis points. Costs reduced every result, and the short 32-month factor-portfolio window limited claims about persistence.

For machine learning, I used book-to-market and 12-minus-1 momentum to predict 21-session SPY-relative returns in a purged monthly walk-forward design with 17 complete folds. Eight baseline, linear, tree, and boosting models were compared. All aggregate IC intervals included zero, and stable after-cost incremental ML value was not established. Preserving that negative result was central to the project: the objective was trustworthy inference, not tuning until a positive answer appeared.

Real data uncovered defects in benchmark calendars, sparse regressions, explainability routing, economic mapping, publication lineage, and monthly sampling. I remediated them with regression tests while preserving the research rules. The final platform passed 300 tests with 90.59% branch-aware coverage. This project taught me that strong quantitative finance requires econometrics, portfolio theory, machine learning, data governance, and the judgment to refuse unsupported claims.

## Recommended CV entry

**Institutional Multi-Factor Asset Pricing & Portfolio Analytics Platform**

*Independent Research Project*

- Built a point-in-time US-equity research platform; screened 822 securities and froze a governed 487-stock universe with SEC identity, filing-availability, share-basis, lifecycle, and immutable-lineage controls.
- Defined 48 factors (47 estimable) and compared CAPM, Fama-French 3, Carhart 4, Fama-French 5, and q-factor models without fabricating the unavailable equity-issuance signal.
- Evaluated eight long-only portfolio methods under preregistered 5/10/20 bps costs and eight ML models using purged monthly walk-forward tests; found no stable after-cost incremental ML value.
- Delivered authenticated API/dashboard/report outputs and adversarial assurance with 300 passing tests and 90.59% branch-aware coverage.

## 60-second interview pitch

My strongest project is an institutional-style US-equity research platform that I built to test whether quantitative results survive realistic data and governance constraints. I screened 822 securities and accepted 487 using historical identity, point-in-time SEC fundamentals, share-basis, and lifecycle checks. On that evidence I built 48 factor definitions, tested five asset-pricing models, compared eight portfolio methods after freezing transaction costs, and evaluated eight machine-learning models with purged monthly walk-forward validation. The most valuable result was not a claim of alpha. Multifactor models improved in-sample fit and costs clearly mattered, but the ML confidence intervals included zero and stable after-cost value was not established. Real data also exposed several pipeline defects that ordinary fixtures had missed, so I added regression and tamper tests. The final release passed 300 tests with 90.59% branch-aware coverage. It taught me how finance theory, econometrics, software engineering, and research integrity have to work together.

## SOP paragraph

I became interested in graduate study in finance while building an institutional-style US-equity research platform that forced me to connect computational engineering with empirical judgment. I assembled a 487-security universe from 822 candidates using effective-dated identity, point-in-time SEC evidence, share-basis checks, and immutable lineage, then implemented factor construction, CAPM and multifactor regressions, constrained portfolio methods, transaction-cost analysis, and purged walk-forward machine learning. The technical challenge was not simply fitting models; it was ensuring that every feature and decision used only information available at the relevant date and that every published result could be authenticated. Real data revealed benchmark-calendar, sparse-regression, lineage, and temporal-sampling defects that I corrected without relaxing the methodology. The final evidence was also intellectually valuable because it was mixed: multifactor models improved in-sample fit and costs were material, but stable after-cost ML value was not established. Learning to preserve that negative result strengthened my interest in econometrics, asset pricing, portfolio theory, and model risk. Graduate study would let me deepen the theoretical and statistical foundations needed to design research that is both computationally sophisticated and financially credible.
