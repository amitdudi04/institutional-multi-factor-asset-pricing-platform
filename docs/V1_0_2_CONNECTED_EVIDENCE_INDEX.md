# V1.0.2 Connected Evidence Index

SYNTHETIC SOFTWARE FUNCTIONAL EVIDENCE — NOT EMPIRICAL RESEARCH

The canonical test is `tests/test_full_platform_connected.py`. All listed IDs came from the final isolated temporary root; no generated publication is tracked.

## Publication inventory

| Phase | Model/kind | Publication ID | Connected evidence |
|---:|---|---|---|
| 2 | All 48 factor IDs | `factor-373785989b4b5d288867d5bcc726f290` | 48 periods, 24 synthetic securities, authenticated market/fundamental parents, diagnostics, portfolios, restart. |
| 3 | CAPM | `asset-pricing-d67016db50bfdb2659063bfc39da719f` | Model-specific factor resolution, coefficients, residuals, diagnostics, comparisons, rolling output, restart. |
| 3 | Fama-French 3 | `asset-pricing-c82f91080703379fac8eba8c419bd261` | Same authenticated service/publication boundary. |
| 3 | Carhart 4 | `asset-pricing-4a3c15818d2dc065e2e0191ea6285bc4` | Same authenticated service/publication boundary. |
| 3 | Fama-French 5 | `asset-pricing-e9534bbeb793ab411e782b8f9246ff34` | Same authenticated service/publication boundary. |
| 3 | Hou-Xue-Zhang q | `asset-pricing-6bbeaa644e43688c84ddf904db26d4ac` | Same authenticated service/publication boundary. |
| 3 | Custom value/momentum | `asset-pricing-6b2b49936076b3e6d21330f908f5f54a` | Strict custom specification and immutable identity binding. |
| 4 | Connected portfolio/scenarios | `portfolio-e1548dabf0308a1f9c7b704190bcfa7e` | Allocation, trades, returns, costs, risk, six scenario kinds, lineage, restart. |
| 5 | Ridge/economic integration bundle | `ml-c7efb1e82c809d58bdf75e09c218a222` | Authenticated target/features/model/card/explanations/economic evidence and restart. |

An additional Phase 4 publication, `portfolio-cd51a470dec52407012b43beb3e00332`, was created through the real `compute-portfolio` CLI.

## Boundary matrices

| Boundary | Fresh evidence |
|---|---|
| Phase 1 | Owner-supplied market/fundamental contract ingestion, immutable raw/standardized evidence, mapping, lifecycle, catalog, restart and parent-tamper refusal. FRED/Kenneth French adapters remain covered by provider-contract/live integration tests. |
| Phase 2 | Exact 48-ID assertion across all configured families; temporal preprocessing, diagnostics and portfolio artifacts. |
| Phase 3 | Six separate publications. Invalid unrelated mappings do not affect unused factors; missing required mappings fail closed. |
| Phase 4 | Seven optimizer service methods plus equal weight; market-cap, Black-Litterman and Bayesian posterior at their documented primitive boundary; covariance/constraint adversarial matrix retained. |
| Phase 5 targets | `future_return`, `future_excess_return`, `percentile_rank`, `ordinal_rank`, `quantile_bucket`, `outperformance`, `future_volatility`, `future_downside_volatility`, `future_drawdown`, `future_risk_quantile`; each binds Phase 1 source ID/checksum/unit. |
| Phase 5 splits/models | Holdout, rolling, expanding and walk-forward; 12 task-compatible model families; bounded search, calibration, explanation, challenger/stability and Phase 5→4 economic execution. |
| Phase 6 API | Non-empty factor, asset-pricing, portfolio and ML listing/detail/artifact endpoints against a restarted real catalog. General API security regressions retained. |
| Dashboard | All nine page-state/presentation paths against the connected API adapter; no screenshot claim. |
| Reports | Markdown, HTML, JSON and CSV created, authenticated and read through the restarted report repository. |
| CLI | Five analytical commands plus configuration, list, verification and delivery-readiness commands executed against the connected repository; all 38 command help surfaces separately pass. |

## Restart, determinism and tamper

Every Phase 1–6 repository/service was reconstructed. Two independent clean-root workflows, one under `PYTHONHASHSEED=731`, produced equal governed numerical behavior; Phase 1 retrieval/event timestamps intentionally create new evidence identities and therefore propagate different publication IDs. This is provenance-bearing metadata, not numerical nondeterminism.

Tamper regressions independently cover Phase 1 parent artifacts; Phase 2/3/4 repository artifacts and manifests; Phase 5 model, prediction, calibration, explanation, model-card and economic artifacts; and Phase 6 report source/manifest binding. Authenticated reads fail closed.
