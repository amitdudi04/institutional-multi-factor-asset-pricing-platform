# Phase 1 Institutional Audit Report

## A. Audit Scope

This independent audit reviewed branch `phase/1-institutional-data-platform` at authorized commit `c0b42e17524bb49dcd27ff79cc92556951246552`, against baseline `d578b896d55a4fcae09473587287e8de65852349`.

The review covered every tracked document, configuration file, Python source file, test, lockfile, ignore rule, environment example, license, Phase 1 commit, and changed top-level area. Git branch/history/remotes, tracked and ignored files, binary and large-file indicators, secrets, paths, data artifacts, internal imports, documentation links, dependency metadata, test collection, and coverage configuration were inspected.

Executed checks included:

- `git branch --show-current`, `git rev-parse`, status, remote, log, merge-base, tracked/ignored inventories, baseline diff/stat/dirstat, `git fsck`, and history scans.
- `uv sync --all-groups`.
- `uv run pytest` and `uv run coverage report`.
- `uv run ruff check .` and `uv run ruff format --check .`.
- `uv run mypy src` and `uv lock --check`.
- Package-import and CLI-help smoke tests.
- Local Markdown-link, secret/path, dependency, internal-import-cycle, large-file, binary-file, and artifact scans.
- Temporary-directory adversarial probes for SEC temporal validation/promotion, Parquet rewrite behavior, DuckDB failed-status exposure, configuration/snapshot determinism, security IDs, and unexpected-column handling.

No live provider request was run. Live integration status is **LIVE INTEGRATION VALIDATION PENDING**.

## B. Executive Assessment

Phase 1 contains a coherent and useful data-platform foundation, and the ordinary quality suite passes. The audit nevertheless found three directly demonstrated critical integrity defects: invalid SEC temporal data can be marked `PASS`, standardized Parquet can be overwritten in place, and DuckDB can expose a `FAIL` dataset through a `validated_*` view. These behaviors violate the Phase 1 acceptance criteria and directly threaten Phase 2 temporal safety and dataset isolation.

Additional high-severity gaps affect lineage persistence, standardized-artifact verification, cross-source security mapping, manifest lifecycle/provenance, owner-supplied schema strictness, and governance traceability. Phase 1 is therefore not safe to authorize as the dependency baseline for factor research.

## C. Claim Verification

| Implementation-report claim | Result | Evidence | Impact |
|---|---|---|---|
| Typed configuration | Verified | Strict frozen Pydantic models in `data/config.py`; invalid values tested | Sound foundation |
| Immutable configuration snapshots | Verified | Refuse-different-content behavior and deterministic temporary probe | Snapshot is redacted, but its recorded config hash cannot be regenerated from it when secrets were present |
| Yahoo Finance adapter | Partially verified | Mocked daily OHLCV/actions and partial-failure tests | No CLI workflow, session-coverage validation, or live validation; raw artifact is reconstructed CSV rather than provider-native response |
| FRED adapter | Verified with warning | Explicit DGS3MO/TB3MS, units/frequency/missing marker, mocked tests | Requested-versus-observed coverage is not validated |
| Kenneth French adapter | Partially verified | ZIP parsing and percent-to-decimal conversion tested | Service dispatch uses the wrong contract name, so its source-specific validator never runs |
| SEC EDGAR adapter | Contradicted as an end-to-end safety claim | Adapter preserves fields, but adversarial ingestion marked impossible filing order `PASS` | Critical temporal-integrity failure |
| Owner-supplied adapter | Partially verified | Bytes are copied before parsing; CSV/JSON/Parquet supported | Extra fields are silently dropped by schema construction; strict owner CSV type/date handling is incomplete |
| Immutable raw storage | Verified for documented single-owner behavior | Hash-addressed timestamped path, atomic temporary file, mutation tests | Filesystem ACL immutability is correctly not claimed |
| SHA-256 verification | Verified | Raw checksum functions and mutation test | Standardized Parquet checksum is not persisted in its manifest |
| Versioned PyArrow contracts | Partially verified | Six tabular contracts exist with keys/types/nullability | No Arrow schema metadata; manifest/report schemas are Pydantic, not PyArrow; record enum/domain validation is incomplete |
| Parquet persistence | Contradicted as immutable/versioned publication | Atomic write/read-back exists, but same dataset/version overwrote different bytes in audit probe | Critical upstream evidence loss |
| DuckDB catalog | Contradicted as validated-only query layer | Registry/view exists; audit probe registered `FAIL` and returned it from `validated_audit` | Critical quarantine/status isolation failure |
| Validation framework | Partially verified | Schema/key/null/status and selected source rules exist | Dispatch mismatch, missing calendar/coverage rules, and sparse result metadata |
| Quarantine workflow | Partially verified | Blocking service outcomes copy raw data and avoid normal registration | Not all documented failure classes reach quarantine; public catalog API bypasses status controls |
| Run manifests | Partially verified | Final success/failure manifests contain config/code/request metadata | No persisted `RUNNING` state; completion always populated; `_write_run` deletes an existing manifest before replacement |
| Source manifests | Partially verified | Raw path/hash/status/row count recorded | Parameters, byte size/media type, actual observed coverage, and some response metadata are absent |
| Dataset manifests | Partially verified | Transformation, raw parent, dimensions, validation, paths, config/code recorded | No Parquet checksum or Git commit; `duckdb_registered=True` is asserted before registration and manifest persistence |
| Lineage | Unsupported as a persisted reconstructable graph | Standalone in-memory graph is tested; dataset stores hashes/parents | No persisted graph, parent existence checks, reprocessing workflow, or catalog reconstruction |
| Security-master eligibility controls | Partially verified | Common-stock/primary/US/USD and duplicate/date/quality checks exist | Cap band and financial/REIT policy are not represented in `SecurityRecord`; cross-source mapping is absent |
| XNYS exchange calendar | Verified with warning | Weekend/holiday sessions tested | Early closes/DST not tested; calendar is not invoked by market ingestion |
| Operational CLI | Partially verified | Help/config/init/inspect/list/verify and three live commands exist | No Yahoo or owner-supplied ingestion command; success summaries are minimal |
| Documentation | Contradicted in material areas | Files and links exist | Quality/lineage/immutability claims exceed implementation; owner register conflicts with implemented Phase 1 baseline |
| No Phase 2 implementation | Verified | No factor/model/portfolio/backtest/API/dashboard modules or dependencies | Correct phase boundary |
| No committed empirical datasets/credentials/generated manifests | Verified | Full tracked/history scans; one header-only CSV | No issue found |

## D. Architecture Assessment

The package is generally cohesive: configuration, contracts, domain types, sources, validation, storage, orchestration, CLI, logging, and exceptions have recognizable responsibilities. Internal-import analysis found no cycle. Provider code is not embedded in CLI presentation logic, adapters do not write storage directly, DuckDB is implemented as a Parquet query layer, and no later-phase logic is present.

The main coupling risk is string-based contract dispatch in `DataIngestionService`. Contract names in `contracts.py` are `french_factor_returns` and `sec_financial_facts`, while the service checks `french_factors` and `sec_facts`; compiler/type checks cannot protect this path. `DataIngestionService.ingest` also combines run lifecycle, retrieval, serialization, storage, validation, quarantine, Parquet publication, catalog mutation, and three manifests in one transaction-like method without an actual cross-store transaction. This is not a style objection: the ordering produces observable integrity failures.

`configuration.py` and `data/config.py` are layered rather than truly duplicate authorities: the former expands YAML/environment references and the latter validates Phase 1. Logging and exception systems are not duplicated. The standalone lineage abstraction is speculative unless integrated with persisted manifests and parent validation.

Changed-area classification from baseline:

| Area | Classification | Basis |
|---|---|---|
| `src/institutional_factor_platform/data` and CLI | Justified Phase 1 | Active data-platform scope |
| `tests` | Justified Phase 1 | Offline contract/integration coverage |
| `config`, environment example, ignore rules | Justified Phase 1 | Runtime, secrets, and artifact controls |
| Phase 1/data documentation and README/roadmap | Justified Phase 1 | Required operating and closeout evidence |
| Dependency metadata/lock and exception expansion | Harmless support change | Required by implemented modules |
| Header-only universe CSV | Harmless support change | Schema aid with no data rows |
| Potentially excessive/out of scope | None found | No Phase 2 implementation or dependency |

## E. Data Integrity Assessment

Raw persistence is the strongest part of the implementation. First write, identical repeat, collision-safe differing bytes, mutation detection, timezone validation, and atomic temporary-file cleanup are covered. The application does not rewrite raw bytes during standardization. Quarantine preserves a copy plus a report and performs no deletion.

Standardized storage is not immutable: `ParquetStorage.write` always calls `os.replace` on the final version path. An audit probe wrote values `[1]` and then `[2]` to the same dataset/version; the hash changed and the final file contained `[2]`. Dataset IDs are derived only from the raw checksum, so reprocessing the same raw artifact after code/config changes targets the same path.

The dataset manifest discards the Parquet checksum returned by storage. Consequently a Phase 2 consumer cannot verify standardized bytes against its manifest. The source-to-dataset relationship is represented by raw checksum and source-manifest content hash, but the graph is neither persisted nor validated for parent existence. Operational data paths and generated artifacts are ignored correctly. Tests use inline, explicitly synthetic fixtures in temporary directories; no fixture is in an operational data path.

## F. Temporal Integrity Assessment

The domain model checks timezone awareness, filing after period end, and availability after filing. SEC records preserve period, filing, availability, and retrieval fields. Market uses exchange-local dates and the calendar module correctly returns XNYS sessions. Macro observations are not forced onto the exchange calendar.

End-to-end enforcement is critically defective. SEC source-specific validation is never selected because of the contract-name mismatch. The audit ingested a record whose filing date preceded period end; its dataset status was `PASS` and it was registered. Retrieval-before-availability is not validated. SEC availability is assigned to midnight UTC on filing date, not the actual acceptance/publication time, and thus is not a defensible intraday availability timestamp. Listing date ordering is checked only by the standalone security-master validator, which is not part of an ingestion workflow. Market ingestion does not compare returned dates with XNYS sessions or requested coverage. Phase 1 correctly creates no lagged factor input.

## G. Adapter Assessment

| Adapter | Contract compliance | Failure behavior | Test quality | Live validation | Limitations |
|---|---|---|---|---|---|
| Yahoo | Partial | Explicit empty, missing-ID, per-ticker partial errors | Useful mocked single/multi-index cases | Pending | End date semantics/coverage not checked; successful partial rows are discarded; no CLI; reconstructed raw representation |
| FRED | Good with warning | Rejects unapproved/empty/malformed; no interpolation/fill | Useful mocked missing-marker and schema cases | Pending | Negative-value policy and requested coverage not explicit |
| Kenneth French | Partial | Rejects bad archive/header/missing factor | Useful but narrow fixture | Pending | Changed layouts/duplicates insufficient; service validator dispatch broken |
| SEC EDGAR | Failed end-to-end safety | Requires contact, validates CIK, rejects malformed/empty | Adapter fields tested, service temporal failure untested | Pending; contact absent | Impossible temporal rows can pass; actual acceptance time unavailable; malformed observations are sometimes skipped silently |
| Owner supplied | Partial | Rejects missing file/extension/schema and malformed JSON | CSV/JSON paths tested; Parquet/corruption/strict columns weak | Not applicable | Extra fields silently disappear; no unit/date guessing prevention beyond Arrow conversion; no CLI |

The shared adapter interface is small and does not force inappropriate HTTP behavior on Yahoo/owner data. HTTP retries and timeouts are bounded; 429 and non-retryable 4xx are explicit. There is no provider fallback or silent date contraction.

## H. Storage Assessment

Parquet uses explicit schema order, configured compression, a temporary file, basic read-back, and a checksum. It does not refuse duplicate targets or preserve prior standardized versions, and it does not persist the checksum. Empty tables can be written if called outside the service. No partition strategy beyond dataset/version is implemented; this avoids tiny partition proliferation but yields one file per artifact.

DuckDB uses a transactional registry and views over Parquet rather than copying payloads. Registry paths are absolute, reducing portability. More importantly, `register` accepts arbitrary validation-status strings and creates a `validated_*` view without enforcing `PASS`/`PASS_WITH_WARNINGS`; a temporary probe exposed a `FAIL` dataset. Each new dataset of a type replaces the view with only that dataset rather than presenting the full validated history. No catalog rebuild from manifests exists. Configuration's `duckdb_read_only_default` is not enforced by the catalog's mutation interface.

## I. Validation and Quality Assessment

Severity aggregation itself is correct: critical dominates error, error dominates warning, warning produces `PASS_WITH_WARNINGS`, and an empty finding set produces `PASS`. Common schema, required-null, empty, and duplicate-key checks are deterministic. Market checks cover OHLC, negative volume, nonpositive/nonfinite prices, ordering, staleness, and extreme returns.

Material gaps remain. SEC and French validators are bypassed by name mismatch. Calendar and requested/observed coverage are not integrated. Unexpected input columns can be discarded before validation because `pa.Table.from_pylist(..., schema=...)` projects to known fields. `ValidationResult` lacks a rule display name, timestamp, affected count/context, and remediation guidance. Quarantine is only triggered for findings reached by the service; checksum mismatch and corrupt standardized artifacts do not have a unified quarantined dataset manifest.

## J. Testing Assessment

The authoritative run collected 45 tests, all passed, with 90.37% branch-aware overall coverage. There were no skipped or expected-failure tests and no warning output. Tests are offline, use HTTP/download injection and temporary directories, and do not depend on execution order or mutate repository data. Coverage has no broad source exclusions.

Coverage is not sufficient evidence for the critical workflow: `services.py` is 74% covered, and its SEC/French dispatch, blocking quarantine path, partial/failed source-manifest path, run overwrite path, and several serialization/error branches are uncovered. `pytest --collect-only -q` itself exits on the configured coverage floor because collection is counted without execution; this is a low operational nuisance, not a correctness failure. The suite missed all three critical behaviors demonstrated by the audit probes.

## K. Security and Licensing Assessment

Tracked files and the Phase 1 commit history contain no detected live credentials, authorization headers, cookies, provider responses, local home paths, or environment dumps. Test emails use the reserved `.invalid` domain and the test key is explicitly non-live. `.env.example` values are empty. SEC requires an owner-supplied contact and does not invent one. Snapshots replace contact and FRED key values; audit inspection confirmed only key names remain.

The repository MIT License is standard and identifies AMIT KUMAR DUDI. Documentation correctly distinguishes software licensing from external data rights. Direct runtime dependencies are Phase 1 relevant:

| Package/version | Purpose | Direct | License metadata available locally |
|---|---|---|---|
| duckdb 1.5.5 | Local Parquet catalog/query | Yes | Package metadata did not state license |
| exchange-calendars 4.13.2 | XNYS sessions | Yes | Package metadata did not state license |
| httpx 0.28.1 | HTTP transport | Yes | BSD-3-Clause |
| pydantic 2.13.4 | Typed validation | Yes | Package metadata did not state license |
| pyarrow 21.0.0 | Schemas/Parquet | Yes | Apache Software License |
| PyYAML 6.0.3 | YAML configuration | Yes | MIT |
| yfinance 0.2.66 | Yahoo access | Yes | Apache |

Development dependencies are Mypy 1.20.2, pytest 8.4.2, pytest-cov 6.3.0, Ruff 0.16.1, and types-PyYAML 6.0.12.20260724. The lock resolved 56 packages and passed validation. Locally installed metadata does not establish present maintenance health for packages whose metadata omits it; no independent live maintenance review was performed. No later-phase statistics, ML, optimizer, API, dashboard, Redis, or PostgreSQL dependency was found.

## L. Defect Register

| ID | Severity | Issue and evidence | Recommended remediation | Regression test required | Phase 2 blocker |
|---|---|---|---|---|---|
| P1-AUD-C01 | Critical | Service checks `sec_facts`/`french_factors`, but contracts are `sec_financial_facts`/`french_factor_returns`; impossible SEC filing order was marked `PASS` and registered | Replace string dispatch with contract-bound validator registry or typed contract identity; enforce all temporal rules before publication | End-to-end invalid SEC/French ingestion must quarantine and never register | Yes |
| P1-AUD-C02 | Critical | Same Parquet dataset/version overwrites prior bytes via `os.replace`; audit hash changed and old content disappeared | Content/code/config-address standardized artifacts; refuse an existing different target; preserve prior versions | Different-content duplicate target must fail without altering original | Yes |
| P1-AUD-C03 | Critical | `DuckDBCatalog.register` accepted `FAIL` and exposed it in `validated_audit` | Type status, allow only pass statuses, validate manifest/artifact existence and checksum, and build research-ready views from filtered registry rows | FAIL/QUARANTINED registration must rollback with no view/row | Yes |
| P1-AUD-H01 | High | Security IDs include source, so the same listing from Yahoo and SEC receives different IDs; no persisted cross-source map exists | Add owner-governed effective-dated source-identifier mapping to canonical listing identity | Cross-source same listing joins; ambiguous/reused identifiers fail | Yes |
| P1-AUD-H02 | High | Lineage graph is in memory and unused; no parent-existence validation, reprocessing service, multiple-output handling, or manifest/catalog rebuild | Persist and validate lineage edges; implement raw-artifact reprocessing and catalog reconstruction within Phase 1 | Missing parent/cycle/reprocessing/multiple-output reconstruction tests | Yes |
| P1-AUD-H03 | High | Dataset manifest omits Parquet checksum/Git commit; source manifest omits request parameters, bytes/media, actual coverage; requested dates are recorded as source coverage | Expand immutable manifests and derive observed coverage; bind standardized checksum, code revision, raw/source/dataset IDs | Manifest round-trip and tamper/reproduction tests | Yes |
| P1-AUD-H04 | High | Catalog registration precedes dataset-manifest persistence; manifest asserts registration before it occurs; a later failure can leave catalog/file state inconsistent | Stage manifest/artifact, perform validated transactional publication, then atomically finalize consistent state or roll back | Inject failure at every publication step and assert no false-success/dangling state | Yes |
| P1-AUD-H05 | High | Owner extra columns are silently projected away; valid typed CSV date/numeric handling is not explicitly implemented; strict schema claim is false | Parse per selected contract with explicit conversions and reject missing/extra/wrong/unit fields before Arrow construction | CSV/JSON/Parquet missing/extra/type/date/unit/corruption cases | Yes |
| P1-AUD-H06 | High | Owner Decision Register still marks Phase 1 universe, security, source/license, fundamentals, RF, storage, and retention decisions proposed/open while code treats them as approved | Record the actual owner-approved Phase 1 decisions through Section 50 change control without altering later-phase decisions | Documentation consistency gate for config versus decision register | Yes |
| P1-AUD-M01 | Medium | Market ingestion does not use XNYS missing-session or requested/observed coverage checks; docs claim coverage checks | Integrate calendar-aware warning/error policy and report returned coverage | Holiday, missing session, exclusive-end, partial-range tests | No after blockers fixed, but required before market factor use |
| P1-AUD-M02 | Medium | Run lifecycle never persists `RUNNING`; completion is always populated; `_write_run` unlinks an existing manifest | Define append-only lifecycle/events or immutable final manifest with separate running marker; never unlink audit evidence | Interrupted/failed/completed lifecycle and overwrite refusal tests | No if final manifests remain truthful, but remediate with publication work |
| P1-AUD-M03 | Medium | Validation findings lack several documented audit fields and quarantine does not cover every claimed failure category | Add count/context/time/remediation fields where meaningful and unify quarantine evidence | Deterministic report and each quarantine-trigger test | No |
| P1-AUD-M04 | Medium | SEC availability is filing-date midnight rather than actual acceptance/publication timestamp; retrieval-before-availability is unchecked | Preserve SEC accepted timestamp where available; otherwise label conservative date-only availability and define next-session use | Acceptance/retrieval/availability ordering tests | Yes before SEC fundamentals enter Phase 2 |
| P1-AUD-M05 | Medium | Yahoo and owner adapters have no operator ingestion command; CLI claim is broader than usable source coverage | Add explicit safe service-backed commands or narrow documentation | Mocked CLI argument/exit/summary tests | No |
| P1-AUD-L01 | Low | `pytest --collect-only` triggers the coverage gate; direct package descriptions and initialization report contain stale wording | Separate collection behavior if desired and correct documentation during remediation | Documentation/command smoke check | No |

## M. Acceptance Criteria Review

The Project Specification defines P1 as unchanged raw hashes; manifested partial failures/checksums/licenses; unique valid keys/mappings/times; quarantine blocking promotion; offline tests; lineage; no fake data; and matching documentation.

| P1 criterion | Status | Evidence |
|---|---|---|
| Unchanged raw hashes | PASS | Raw persistence/mutation tests and audit inspection |
| Partial failures/checksums/licenses manifested | PASS WITH WARNING | Raw checksum and terms note exist; standardized checksum and richer response metadata do not |
| Unique valid keys and mappings | FAIL | Table keys checked, but cross-source canonical mapping is absent |
| Valid times/temporal safety | FAIL | Invalid SEC temporal record passed and registered |
| Quarantine blocks promotion | FAIL | Normal reached blocking path avoids registration, but catalog directly exposes failed status and bypassed validators allow invalid promotion |
| Offline tests | PASS WITH WARNING | 45 pass at 90.37%; critical orchestration failures untested |
| Reconstructable persisted lineage | FAIL | In-memory graph is not integrated/persisted; standardized hash absent |
| No fake/empirical research data | PASS | Only header-only CSV; synthetic fixtures inline/test-only |
| Matching documentation | FAIL | Material validation, lineage, immutability, and governance claims conflict with code |

## N. Phase 2 Readiness

| Question | Answer | Basis |
|---|---|---|
| 1. Can Phase 2 load only validated, non-quarantined datasets? | No | Catalog API/view does not enforce status |
| 2. Can it identify exact supporting raw artifacts? | Qualified yes | Raw checksum/path and parent exist, but no persisted verified graph |
| 3. Can it identify configuration? | Qualified yes | Hash and redacted snapshot exist; secret-bearing original hash is not reproducible from snapshot |
| 4. Can it identify Git commit? | Qualified yes | Run manifest has commit; dataset manifest alone does not |
| 5. Are units explicit? | Qualified | Macro/French/SEC units are explicit; market price currency is optional and adjustment semantics rely on field names/docs |
| 6. Are identifiers stable for cross-source joining? | No | IDs deliberately vary by source and no canonical mapping is persisted |
| 7. Are temporal fields sufficient to prevent fundamental leakage? | No | SEC validator bypass and approximate availability timestamp |
| 8. Are provider failures distinct from legitimate empty data? | Yes | Empty/partial/failure exceptions and statuses are explicit |
| 9. Can raw artifacts be reprocessed without redownloading? | No supported workflow | Bytes exist, but no reprocessing service/CLI and overwrite behavior is unsafe |
| 10. Are standardized datasets deterministically reproducible? | No | Output checksum absent; environment lacks full version capture; same target is mutable |
| 11. Can quarantined data appear in research views? | Yes | Direct `FAIL` registration was exposed in audit probe |
| 12. Can test fixtures enter operational paths? | Unlikely | Inline fixtures and temporary roots; operational paths ignored |
| 13. Are source limitations visible? | Yes | Source guide/governance disclose major limitations |
| 14. Is the universe process explicit rather than invented? | Qualified | Rules/template exist; no universe is fabricated, but point-in-time source/mapping remains unresolved |
| 15. Is the platform usable by Phase 2 without data-layer changes? | No | Blocking fixes and lineage/mapping work are required |

## O. Git Status

Audit start state:

- Branch: `phase/1-institutional-data-platform`.
- Head: `c0b42e17524bb49dcd27ff79cc92556951246552`.
- Baseline/merge base with local `main`: `d578b896d55a4fcae09473587287e8de65852349`.
- `origin/main`: `a1df709e45546fbae3d8902b59b170b84bed4d71`; the baseline and Phase 1 commits are not on the remote default branch.
- Initial working tree: clean.
- History: linear; no baseline corruption or rewrite detected. `git fsck` reported two unreachable trees but no reachable-object corruption.
- Ignored local state: `.coverage`, tool caches, `.venv`, and bytecode only.
- Audit change: this report only; no implementation remediation.
- Push status: not pushed.

If the audit report commit is to be published for review, the exact branch push command is:

```shell
git push -u origin phase/1-institutional-data-platform
```

## P. Final Verdict

**PHASE 1 AUDIT FAILED — MATERIAL INTEGRITY DEFECTS**

The passing ordinary suite does not offset demonstrated invalid-data promotion, mutable standardized storage, or unfiltered research views. Phase 2 authorization would expose research code to temporally invalid or failed data and non-reproducible standardized artifacts.

## Q. Next Action

> Resolve all blocking defects, rerun the complete Phase 1 audit, and do not authorize Phase 2.

## Remediation status

The original findings and verdict above are immutable audit evidence for commit `c0b42e17524bb49dcd27ff79cc92556951246552`. A subsequent focused remediation is documented in `docs/PHASE1_REMEDIATION_REPORT.md`. The audit verdict is not retroactively changed: a fresh independent re-audit must verify the remediated branch before Phase 2 can be authorized.
