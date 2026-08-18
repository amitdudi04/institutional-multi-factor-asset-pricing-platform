# Final Project Assurance Report

## Scope and verdict

Prompt 23 technically controllable work was exhausted locally. Expanded real Phase 1, corrected real Phase 2, corrected real Phase 3, and real Phase 6 delivery passed. Phase 4 and Phase 5 are `NOT ESTIMABLE — OPEN OWNER DECISIONS`; therefore the full local empirical project completion verdict is not available. Phase 7 assurance passes for the work actually estimable, with no known Critical or High research-integrity defect. Phase 8 documentation is complete with the non-estimability limitation preserved.

## Candidate assurance

All 822 HF candidates have a deterministic terminal status in the ignored runtime matrix. Accepted: 487. Rejected: 335. Rejections are 114 attribution, 56 splice, 68 identity, 70 shares, 16 terminal event, 7 split basis, 2 asset type, 1 venue/non-US, and 1 fundamentals. Accepted quality tiers are 372 A, 115 B, and 0 C. The optional non-HF route gate reviewed 5,264 candidates and accepted 0.

No candidate was selected using Phase 2–5 performance. The universe was frozen after exact identity and governed projection. Detailed source rows, SEC covers, HF Parquet, and the candidate matrix remain ignored runtime evidence.

## Publication assurance

| Phase | Result | Evidence |
|---|---|---|
| Expanded Phase 1 | PASS | `factor_market_input-89848f8e3c34d53d0432f6e0`; `factor_fundamental_input-962c8ada3e74e32b00568cd7` |
| Phase 2 | PASS WITH WARNINGS | `factor-5a73616f131fca2102fa2ca4141ad64f`; 48 defined, 47 estimable |
| Phase 3 | PASS | `asset-pricing-c0a72fae5349f1048e18557250da1927`; five configured models |
| Phase 4 | NOT ESTIMABLE | commission, spread, slippage, and impact are open/null |
| Phase 5 | NOT ESTIMABLE | target, horizon, benchmark, features, and Phase 4 parent are open/null |
| Phase 6 | PASS FOR AVAILABLE EVIDENCE | delivery catalog READY; 102 authenticated retained publications; API and four report formats passed |
| Phase 7 | PASS WITH DISCLOSED NON-ESTIMABILITY | zero known Critical/High integrity defects after remediation |
| Phase 8 | COMPLETE | eight permitted final documents plus README updated |

## Defects found and remediated

1. Sparse early factor formation dates aborted later valid Phase 3 dates. Complete-case dates are now used, with a regression test.
2. Sparse rolling windows aborted full-sample estimable regressions. Non-estimable windows are skipped, with a regression test.
3. Benchmark compounding followed security-specific missing sessions. Phase 2 now uses one authenticated benchmark calendar per holding period, with reconciliation and regression tests.
4. Generated analytical publication roots were missing from `.gitignore`; explicit ignore rules were added.

## Final validation

- The single authoritative full-suite run collected 298 tests and completed with an updated coverage database; aggregate statement and branch coverage rounded to 91%, above the required 90% floor.
- Ruff lint passed; all 227 files passed the Ruff format check; strict Mypy passed for 113 source files; and the 96-package lock resolved unchanged.
- The installed-environment dependency audit found no known vulnerabilities. The local project itself was the only unaudited item because it is not a PyPI dependency.
- Catalog integrity passed. A fresh delivery restart authenticated 102 retained publications and returned `READY`.
- All 86 Markdown files passed local-link and UTF-8/mojibake checks. The final documentation contained no contradictory Phase 4 or Phase 5 completion claim.
- Repository scans found zero tracked dataset/database/cache/generated-artifact paths, zero tracked files above 5 MiB, zero private-key or cloud-key signatures, and zero configured secret values in tracked content.
- The full connected test exercises authenticated restart and deliberate artifact tampering across the Phase 1–6 publication chain. The empirical publications were then independently re-read through the catalog and delivery authentication boundaries; no direct database bypass was used.

## Hypotheses

H1, H3, H4, H5, H6, and H7 are `INCONCLUSIVE`. H2 is `PARTIALLY_SUPPORTED` by higher in-sample adjusted R-squared for configured multifactor models versus CAPM, but stable OOS/economic improvement is not established.

## Deferred operations

`DOCKER = DEFERRED BY OWNER — NOT PART OF THIS RUN`.

`GITHUB / MERGE / TAGS = DEFERRED BY OWNER — NOT PART OF THIS RUN`.

No push, merge, tag, release, Docker, WSL, or GitHub action was performed.

## Final verdict

`LOCAL EMPIRICAL RUN PARTIALLY COMPLETE — REAL PHASES 1–3 AND 6 PASSED; PHASES 4–5 NOT ESTIMABLE UNDER OPEN OWNER DECISIONS`
