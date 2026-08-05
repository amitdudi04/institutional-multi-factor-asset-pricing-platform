# Phase 3 Validation Report

## Authoritative gate results

| Gate | Result | Evidence |
|---|---|---|
| Full Pytest and branch coverage | PASS | 153 tests passed; 90.11% total branch-aware coverage |
| Phase 3 focused numerical/adversarial suite | PASS | 19 test cases passed after final remediation, including every approved model |
| Ruff lint | PASS | All checks passed |
| Ruff format | PASS | 97 files formatted/verified after Phase 3 additions |
| Strict Mypy | PASS | No issues in 52 source files |
| Lock verification | PASS | `uv lock --check`; 58 packages resolved |
| Configuration and CLI | PASS | Phase 3 hash emitted; compute/list/verify commands exposed |
| Schema and artifact authentication | PASS | End-to-end publication, exact-schema read, retry, and mutation rejection |
| Secret scan | PASS | No AWS key, private-key header, GitHub token, or OpenAI-style live token pattern |
| Tracked-artifact scan | PASS | No Parquet, database, cache, bytecode, coverage, or generated data artifact tracked |
| Diff whitespace | PASS | `git diff --check` |

The full test run used Python 3.13.14. Ruff retains Python 3.11 syntax compatibility, and package metadata requires Python 3.11 or newer. Mypy targets the active Python 3.13 validation environment because current NumPy stubs use Python 3.12+ type-alias syntax; this changes type-check parsing only, not the declared runtime floor.

## Numerical evidence

Known analytical fixtures recover an intercept of approximately 0.02 and factor loadings of approximately 1.5 and -0.7 under classical, HC0, HC1, HC2, HC3, and HAC covariance choices, with adjusted R-squared above 0.99. WLS uses explicit positive aligned weights. Fama-MacBeth recovers the configured cross-sectional premium. Rolling-window probes show that changing the final future observation cannot alter any earlier window.

## Rejection and adversarial evidence

Tests reject missing columns/factors, insufficient observations, constant returns and predictors, rank-deficient/perfectly collinear designs, invalid WLS weights, invalid HAC lags, duplicate rolling dates, insufficient Fama-MacBeth cross-sections, conflicting common factors, absent mapped factors, future-available factor evidence, delayed realized-return evidence, unapproved models, modified artifacts, and unauthenticated publication bundles. Repeating an identical run produces the same publication identity and authenticates the existing evidence.

## Acceptance criteria

| Phase 3 criterion | Result |
|---|---|
| Approved equations and alignment | PASS — registry, configuration, exact-date excess returns, explicit mappings |
| Verified robust inference and diagnostics | PASS — analytical recovery, HC/HAC, assumptions and influence suite |
| Explicit units, windows, and counts | PASS — monthly decimal-return contract and strict configuration/output counts |
| Past-only rolling | PASS — ordered unique dates, window bounds, future-mutation regression |
| Uncertainty and economic magnitude | PASS — uncertainty tables and raw decimal estimates; no significance-to-economics claim |
| Reproducible failure-aware outputs | PASS — deterministic identity, immutable artifacts, fail-closed errors, authenticated reads |

No live integration or empirical fitness claim is made. Independent assurance remains the reviewed-merge gate.
