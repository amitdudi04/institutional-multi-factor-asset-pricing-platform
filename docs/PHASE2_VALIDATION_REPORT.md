# Phase 2 Validation Report

## Authoritative validation run

Validation was executed on 2026-08-04 in the local locked `uv` environment on branch `phase/2-factor-engine`.

| Gate | Result | Evidence |
|---|---|---|
| Full Pytest and branch coverage | PASS | 134 passed; 90.34% total coverage; configured floor 90% |
| Phase 2 focused/adversarial suite | PASS | 17 passed |
| Ruff lint | PASS | `uv run ruff check .` |
| Ruff format | PASS | 76 files already formatted |
| Strict mypy | PASS | 37 source files; no issues |
| Lock verification | PASS | `uv lock --check`; 56 packages resolved |
| Locked environment sync | PASS | 54 packages checked and compatible |
| CLI/configuration | PASS | root help, factor config hash, compute help, owner-input help |
| Factor configuration | PASS | canonical hash `94dc2b2c79add12b3a1b7dc3cc25feb8e05fdaf07b1349d8bef814f7c844d5eb` |
| Secret scan | PASS | no high-confidence credential/private-key/token patterns |
| Local Markdown links | PASS | all resolve |
| Internal import cycles | PASS | none detected |
| Private absolute paths | PASS | none in current implementation/docs |
| Tracked generated artifacts | PASS | no datasets, Parquet, database, cache, `.env`, or coverage artifact |
| Dependency compatibility | PASS | `uv pip check`: all installed packages compatible |
| Git whitespace | PASS | `git diff --check` |

Four warnings come from upstream `exchange-calendars`/pandas handling of generic NumPy timedeltas in existing Phase 1 calendar tests. They are non-blocking deprecation warnings, not Phase 2 calculation failures.

## Test coverage

The suite exercises configuration validation; every preprocessing mode; all 48 definitions; ranking and preferred-direction scoring; monthly holding-period timing; market/fundamental schemas; duplicate/null/non-finite/extreme inputs; return plausibility; unit contradictions; canonical mappings; future market, membership, classification, and filing timestamps; missing values; denominator zeros; authenticated parent roles; exact-byte parsing; publication ID reproducibility; immutable collisions; crash-before-activation restart; envelope, artifact, portfolio, configuration, validation, diagnostics, and lineage tampering; path escape; and authenticated repository reads.

## Phase 2 acceptance criteria

| Criterion | Result | Evidence |
|---|---|---|
| Formulas, directions, and versions | PASS | Versioned definition registry, methodology, manifest metadata, direction-aligned scores |
| Point-in-time preprocessing | PASS | Date-local/optional classification-local transforms; future timestamps rejected |
| Coverage and outliers | PASS | Persisted coverage ratios and winsorized-value counts |
| Turnover and costs | PASS WITH DISCLOSURE | Monthly membership turnover; costs intentionally unavailable pending owner-approved Phase 4 model |
| Timing | PASS | Month-end formation, following holding period, evidence availability propagation |
| Accurate labeling | PASS | Project-specific characteristics; no official replication or empirical claim |
| Numerical tests | PASS | Ratios, compounding, rolling risk, normalization/ranking, ranges, missingness |
| Temporal tests | PASS | Market, eligibility, classification, filings, as-of joins, next-period realization |
| Reproducibility | PASS | Parent/config/code-addressed ID; idempotent immutable rerun |
| Lineage and immutable storage | PASS | Complete authenticated evidence graph and byte-bound reads |

## Data availability statement

The report validates software behavior only. No issuer-scale or live integration dataset was supplied, so no empirical coverage, factor premium, economic significance, or investability result is claimed. A real run must use the documented owner/approved-source contracts and will fail if required point-in-time evidence is absent.
