# Final Empirical System Architecture

The completed empirical chain is:

```text
HF market + Alpha lifecycle + SEC submissions/Company Facts/tagged covers
  -> ignored immutable source cache and 822-row screening matrix
  -> effective-dated security and issuer/listing authorities
  -> authenticated Phase 1 market and fundamental publications
  -> authenticated 48-factor publication (47 estimable)
  -> authenticated five-family asset-pricing publication
  -> frozen-cost eight-method portfolio and scenario publications
  -> purged monthly walk-forward ML publications
  -> authenticated FastAPI, Streamlit, and four-format reports
```

## Phase responsibilities

| Phase | Responsibility | Integrity boundary |
|---|---|---|
| P1 — Data | Acquire, validate, map, and publish point-in-time market/fundamental evidence | Immutable raw bytes, effective-dated identity, lifecycle, availability, checksums |
| P2 — Factors | Construct governed characteristics, portfolios, and diagnostics | Authenticated P1 parents, temporal joins, common benchmark calendar |
| P3 — Asset pricing | Estimate configured model families and robust diagnostics | Fixed model registry, complete-case handling, no invented Custom model |
| P4 — Portfolio/risk | Allocate under mandate constraints, account for turnover/costs, and run scenarios | Costs frozen before performance; reconciled holdings, trades, gross/net returns |
| P5 — ML | Build monthly features/targets, train challengers, explain, and evaluate economics | Purging, embargo, training-only preprocessing, exact P2/P3/P4 parent identity |
| P6 — Delivery | Expose authenticated evidence through API, dashboard, and reports | No local-path/SQL bypass; manifests and artifacts re-authenticated on read |
| P7 — Assurance | Challenge lifecycle, timing, mapping, publication, restart, and tamper controls | Zero open Critical/High integrity defects at release |
| P8 — Packaging | Communicate paper, case study, admissions, and interview evidence | Documentation-only; empirical tags and findings remain immutable |

The dependency direction is one-way. A later phase may authenticate and consume an earlier publication but cannot rewrite its evidence or silently substitute a different parent.

Identity is listing-level and effective-dated. SEC issuer facts reach a security only through singular persisted issuer/listing mappings. Fundamentals preserve availability dates, and accepted intervals begin no earlier than verified tagged filing anchors. Raw and generated evidence remains local and ignored by Git.

Phase 4 freezes one-way LOW/BASE/HIGH costs at 5/10/20 bps before results. BASE uses authenticated equal-weight Phase 4 evidence as the Phase 5 economic parent. Phase 5 monthly decision sampling prevents daily pseudo-replication while its target retains the governed 21-session horizon. Purging, a one-month embargo, bounded hyperparameter grids, deterministic seed 17, and single-thread estimators protect temporal and configuration identity.

Every analytical publication binds manifests, checksums, configuration identity, code revision, lineage, and lifecycle state. Phase 6 re-authenticates those boundaries for discovery, API responses, dashboard views, and report generation. The final restart check discovered 143 authenticated retained publications; it did not read analytical tables through an unverified database shortcut.

## Public repository boundary

The Git repository contains code, configuration, contracts, tests, and aggregate documentation. Raw provider files, processed empirical datasets, DuckDB catalogs, generated Parquet, trained model artifacts, and generated reports remain ignored local evidence. The MIT licence covers repository code; it does not grant redistribution rights for third-party data.
