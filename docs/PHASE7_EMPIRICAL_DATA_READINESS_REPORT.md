# Phase 7 Empirical Data Readiness Report

Status date: 2026-08-18

## Executive conclusion

The repository has completed a defensibly bounded real Phase 1 publication for AAPL and MSFT. It has not completed the preregistered cross-sectional empirical study. The authenticated intersection has maximum daily breadth two, while the approved Phase 2 configuration requires at least three securities and value-weighted factor portfolios.

Final verdict:

**PHASE 7 EMPIRICAL ASSURANCE NOT PASSED — PHASE 2 IS NOT ESTIMABLE FROM THE DEFENSIBLE FREE/PUBLIC INPUT INTERSECTION**

## Starting and continuation evidence

The continuation began from validated checkpoint `7087ab9691530e3295837e1ca5e35be9d2e5ea60`. Commit `71f701b331eb1ce6d40cf73aef6874d34c8a10fb` added the governed legacy SEC XBRL parser and bounded historical identity/PIT authority without resetting earlier work.

## Bounded Phase 1 evidence

| Evidence | Result |
|---|---|
| Historical SEC identity | 33 authenticated legacy annual XBRL publications, 2010–2018, across Apple, Microsoft, Meta, predecessor Google, and Alphabet |
| Effective symbol authority | Nine bounded intervals preserving FB/META, Google/Alphabet succession, and separate GOOG/GOOGL classes |
| PIT shares | 19 legacy dimensionless observations plus authenticated Company Facts; ambiguous multi-listing totals remain unallocated |
| Market quality | AAPL and MSFT accepted; SPY benchmark accepted; FB is bounded at ticker change; GOOG/GOOGL rejected for the 95.25% PiTrading-to-IEX discontinuity |
| Market input | `factor_market_input-9ee8af3b5f5d1f49095af46e`; 7,930 rows; 2010-10-27–2026-08-04; SHA-256 `fc9a867a7a8d7d823a543feb3becc7ffe3adf320f6e3511cb9a8817a8354f695` |
| Fundamental input | `factor_fundamental_input-a6da21983efceee71390ca12`; 518 rows; 17 observed fields; SHA-256 `20f649dbcdd20a957f95cadbce0f51e188eae2582ebbc69c2c6c2da7a4bf2a92` |
| Restart/determinism | Re-ingesting the exact inputs returned the same dataset IDs |
| Catalog | PASS |

The market publication uses SPY for market and benchmark return. DGS3MO uses the latest nonmissing FRED observation strictly before each trading date and converts annual percentage yield to a 252-day simple return. This is a documented conservative rule because the FRED artifact does not contain vintage release timestamps.

HF prices are source-adjusted. The authenticated AAPL/MSFT files contain no split-factor observations. MSFT has no study-period split; Apple pre-2020 filed counts are therefore not combined with restated prices. Apple shares remain null until the first post-split filing on 2020-10-30. The publication retains 5,410 rows with compatible PIT shares and 2,520 without shares.

## Universe and terminal-event disposition

The resulting population is the Free Public-Data Covered Common-Stock Research Universe, bounded to two exact listings. It is not Russell 1000, S&P 500 membership history, or a broad large/mid-cap universe. It cannot support the intended annual top-1,000 ranking.

Neither retained security delists within the panel. The panel therefore has zero terminal events, zero terminal returns, and zero unresolved terminal cases within the retained population. FB/META is excluded at the source/ticker boundary rather than treated as a delisting. GOOG/GOOGL is excluded for market-series integrity, not assigned a synthetic terminal return.

## Phase 2 execution evidence

The exact authenticated command attempted the existing Phase 2 service with the two Phase 1 parents. The first adversarial run exposed and closed two software error-boundary defects: missing XNYS breakpoints caused a null callback crash, and insufficient breadth lacked an early preflight gate. Focused regression tests pass.

The final execution result is:

```text
error: Phase 2 is not estimable: no date meets the approved minimum cross-section of 3; maximum authenticated breadth is 2.
```

No factor publication was created. No configuration threshold, quantile, weighting rule, factor formula, or universe rule was changed.

## Downstream empirical status

| Stage | Status | Reason |
|---|---|---|
| Real bounded Phase 1 | COMPLETE | Authenticated market and fundamental publications exist and restart deterministically |
| Historical identity 2010–2018 | COMPLETE / defensibly bounded | Exact evidence exists for the five investigated issuers; unsupported broader identities are excluded |
| Study-wide PIT shares | COMPLETE / explicit non-estimability coverage | Exact eligible facts are preserved; multi-class and split-basis gaps remain null |
| Broad HF panel | COMPLETE with documented rejections | The defensible intersection is two securities; unsafe GOOG/GOOGL and discontinuous FB/META coverage are excluded |
| Terminal treatment | COMPLETE for retained panel | No retained terminal cases; exclusions are not recoded as terminal returns |
| Real Phase 2 | NOT ESTIMABLE | Maximum breadth two is below approved minimum three |
| Real Phase 3 | NOT EXECUTED | No authenticated Phase 2 parent |
| Real Phase 4 | NOT EXECUTED | No authenticated Phase 2/3 parents |
| Real Phase 5 | NOT EXECUTED | No authenticated Phase 2/3/4 parents |
| Real Phase 6 empirical delivery | NOT EXECUTED | No real empirical publications to serve; synthetic fallback remains forbidden |
| Phase 7 assurance | NOT PASSED | Cross-sectional study cannot be estimated |
| Phase 8 packaging | NOT AUTHORIZED | Final research-completion claim would be false |

## Hypotheses and claims

H1–H5 are **INCONCLUSIVE** because their required Phase 2–4 evidence does not exist. H6 and H7 are also **INCONCLUSIVE** because no authenticated ML research dataset can be assembled. No alpha, premium, coefficient, portfolio return, risk statistic, ML metric, or economic-value claim was generated.

## Branch and release disposition

The research branch must not be merged to `main`, pushed as a completed empirical release, or tagged `research-empirical-public-v1` / `project-complete-public-data-v1`. Those operations are conditional on Phase 7 assurance passing. Preserving the branch prevents the bounded negative result from being mislabeled as project completion.

## Final software and operational gates

| Gate | Result |
|---|---|
| Full suite | PASS — 296 tests, 103 classified warnings |
| Branch-aware coverage | PASS — 90.75% against 90% minimum |
| Ruff / format | PASS / PASS — 219 files checked |
| Strict Mypy | PASS — 113 source files |
| Lock / dependency audit | PASS / PASS — no known vulnerabilities; editable project skipped as documented |
| Catalog / Git whitespace | PASS / PASS |
| Credential and repository hygiene | PASS — zero configured-value matches, private-key patterns, tracked empirical datasets/databases, generated artifacts, files over 5 MiB, or forbidden caches |
| Docker | BLOCKED — EXTERNAL OWNER/ADMIN INFRASTRUCTURE; Docker is absent and WSL is not installed |
| GitHub Actions | BLOCKED — EXTERNAL ACCOUNT/BILLING; latest public run failed in three seconds and both jobs were prevented from starting by the account lock |

## What would change the result

The minimum missing evidence is at least one additional security with authenticated effective-dated common-stock identity, an HF series that passes the source-splice checks, and PIT share counts compatible with the split-adjusted price basis. This is an external evidence limitation, not authorization to invent mappings, allocate issuer totals across share classes, repair unexplained price jumps, or lower the approved cross-sectional threshold.
