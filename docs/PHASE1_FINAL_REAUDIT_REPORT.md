# Final Independent Phase 1 Re-Audit Report

## A. Scope and Evidence

This final audit reviewed the official repository on branch
`phase/1-institutional-data-platform` at the required starting head
`4a93e19d24b93a0cf40e38f1cfb159aa87473451`. The authorized baseline
`d578b896d55a4fcae09473587287e8de65852349`, original implementation, both prior
audits, and both remediation series are ancestors of the audited head. History is linear,
the starting worktree was clean, `origin` is the official HTTPS remote, and the branch has
no upstream.

The review covered every tracked document, configuration file, Phase 1 module, test file,
CLI command, dependency declaration, schema version, manifest and lineage model, catalog
operation, security-identity store, and relevant commit. Temporary synthetic software-test
fixtures were confined to operating-system temporary directories and were not used as
research data.

Executed gates and probes included:

- `uv sync --all-groups`;
- `uv run pytest` (68 passed, 90.11% branch-aware coverage);
- `uv run coverage report`;
- `uv run ruff check .` and `uv run ruff format --check .`;
- `uv run mypy src` and `uv lock --check`;
- the complete suite with `PYTHONHASHSEED=731` (68 passed, 90.11%);
- selected publication, restart, tamper, demotion, identity, and mapping tests individually
  (10 passed; the selected-only command returned nonzero solely because repository-wide
  coverage was 56.50%, below the global 90% gate);
- package/import smoke tests, dependency tree, AST import-cycle analysis, and help for all
  14 CLI subcommands;
- independent malformed-manifest, evidence-substitution, disconnected-lineage,
  post-publication tamper, ordinary demotion, abrupt-termination, rebuild, identity,
  issuer-mapping, SEC caller-ID, and owner-unit probes;
- current-tree and Phase 1-history scans for secrets, empirical data, databases, generated
  evidence, caches, local absolute paths, and large binaries;
- Markdown local-link validation, tracked-file review, header-only CSV inspection, license
  review, ancestry review, and remote inspection.

No live provider request was made. **LIVE INTEGRATION VALIDATION PENDING**.

## B. Independent Executive Assessment

Several second-remediation controls are real: `{}` cannot be promoted, the unsafe in-memory
catalog methods are gone, raw and Parquet bytes are immutable, ordinary validation failures
are quarantined, normal restart/rebuild works for honest evidence, and the intended stable-ID
and symbol-history path works. Static quality gates also pass.

The permanent Phase 2 foundation is nevertheless unsafe. Promotion authenticates the
presence and checksums of several files, but it does not authenticate the required lifecycle
as a connected state transition. Catalog verification detects some post-publication tampering
but does not revoke visibility. Abrupt failure after catalog commit bypasses compensation,
leaves no promotion/run completion evidence, and still passes catalog integrity. Additional
High defects affect configuration binding, demotion consistency, rebuild atomicity,
issuer/listing ambiguity, SEC mapping enforcement, and owner-unit semantics.

## C. Original Critical Defect Closure

| Defect | Original failure | Independent final probe | Result | Status | Residual risk |
|---|---|---|---|---|---|
| P1-AUD-C01 | Invalid SEC chronology passed | Existing and selected end-to-end SEC quarantine tests | Invalid chronology remains blocked | CLOSED | Date-level availability remains documented |
| P1-AUD-C02 | Parquet overwrite | Conflict/idempotency tests and code review | Different bytes cannot replace the same artifact identity | CLOSED | Logical row order remains part of identity |
| P1-AUD-C03 | Failed data entered validated view | Malformed manifest, disconnected lifecycle, tamper, and crash probes | Normal status gate works; alternate persisted-state attacks still create or retain visibility | REOPENED / FAILED | Critical research-ready isolation failure |

## D. Original High Defect Closure

| Defect | Result | Status | Residual risk |
|---|---|---|---|
| P1-AUD-H01 identity mapping | Stable assigned/canonical IDs and symbol history work | PARTIAL | Public ticker-derived `SecurityId.create` remains; SEC accepts caller-supplied listing IDs; mixed ambiguity resolves |
| P1-AUD-H02 lineage/rebuild | V3 files persist and honest restart works | PARTIAL | Lifecycle is label-checked, not connected-state authenticated; invalidation/supersession reconstruction is absent |
| P1-AUD-H03 manifest evidence | Many hashes and identities are checked | PARTIAL | Configuration hash and validation-report ID are not bound to their persisted evidence |
| P1-AUD-H04 transactional publication | Ordinary `Exception` after promotion demotes | FAILED | Abrupt termination leaves research-ready visibility without final journal/run evidence |
| P1-AUD-H05 owner inputs | Exact columns/types and declared unit keys are enforced | PARTIAL | Declared units are not reconciled to row units or fully persisted |
| P1-AUD-H06 governance | Approved decisions are aligned | CLOSED | Later-phase decisions remain correctly proposed/open |

## E. Second-Remediation Defect Closure

| Area | Assessment |
|---|---|
| Evidence authentication | PARTIAL: malformed/missing/checksum-altered evidence blocks initial promotion, but configuration identity and lifecycle connectivity are not authenticated |
| Stable identity | PARTIAL: assigned/canonical IDs survive ticker change, but a public ticker-derived constructor and unenforced SEC mapping remain |
| Lifecycle lineage | FAILED: relationship names anywhere in the graph satisfy promotion; no lifecycle state-machine reconstruction exists |
| Manifest final state | FAILED under compensation: demotion leaves `dataset.json` at `PUBLISHED` |
| Transaction recovery | FAILED for abrupt termination and demotion-evidence disagreement |
| Yahoo-SEC mapping | FAILED as an enforced boundary: SEC accepts arbitrary caller `security_id`; mixed ambiguous/resolved issuer evidence resolves |
| Unit validation | PARTIAL: request metadata is contract-keyed but can contradict row units |
| Governance alignment | PASSED for the owner decisions changed by remediation |

## F. New Defects

1. **FR-C01 — Critical:** disconnected lifecycle labels authorize promotion. The audit removed
   the real registration/promotion edges, added those relationship names on an unrelated
   three-node chain, updated the lineage checksum, and called `promote_persisted`. Result:
   `PROMOTED`, with the dataset listed research-ready.
2. **FR-C02 — Critical:** integrity failure does not revoke access. After deleting the
   validation report, `verify_integrity` raised `EvidenceIntegrityError`, but
   `list_datasets(research_ready_only=True)` still returned the dataset and the existing
   `validated_macro_observations` view still returned one row.
3. **FR-C03 — Critical:** abrupt post-promotion termination leaves unauthenticated visibility.
   A `SystemExit` injected while writing `promotion.json` left one research-ready dataset,
   zero promotion manifests, zero successful final run manifests, and
   `verify_integrity = PASS`.
4. **FR-H01 — High:** ordinary compensating demotion is internally contradictory. The catalog
   is demoted and a demotion event is written, but final `dataset.json` remains `PUBLISHED`;
   catalog integrity ignores non-promoted rows and reports success.
5. **FR-H02 — High:** persisted configuration identity is not authenticated. Replacing the
   snapshot with `{}`, updating only its checksum, and retaining the old `configuration_hash`
   was accepted. An arbitrary substituted `validation_report_id` was also accepted.
6. **FR-H03 — High:** issuer/listing ambiguity is bypassable. Overlapping `RESOLVED` and
   `AMBIGUOUS` evidence for one issuer resolved to the listing. SEC standardization accepted
   `caller-forged-listing` without consulting a persisted mapping store, and the public
   ticker-derived `SecurityId.create` changed when `AAA` changed to `BBB`.
7. **FR-H04 — High:** rebuild is not atomic. When a valid promotion was followed by unsupported
   v1 evidence, rebuild raised `ValidationError` but left the target catalog present with the
   first dataset research-ready.
8. **FR-H05 — High:** owner-unit metadata can contradict the data. A DGS3MO macro request
   declared `value=percent`, while its row declared `source_unit=shares`; the adapter accepted
   the record. Request unit metadata is not reconciled with row units or copied completely to
   the dataset manifest.
9. **FR-M01 — Medium:** lifecycle event capabilities are incomplete. Demotion has a journal
   event, but registration/promotion are graph edges without prior/new state, reason, catalog
   identity, or state-machine validation; invalidation and supersession have enum labels only.
10. **FR-M02 — Medium:** manifests, lineage, snapshots, validation reports, and lifecycle
    events use direct writes rather than atomic replace/fsync publication. A stale publication
    lock has no documented or implemented recovery path after process death.
11. **FR-M03 — Medium:** current documentation overstates controls. `DATA_CONTRACTS.md` still
    says canonical `SecurityId` derives from ticker; README/Roadmap claim complete lifecycle;
    architecture/governance claim cryptographic configuration linkage and deterministic
    recovery that the probes contradicted.

## G. Architecture Assessment

The package is reasonably layered, imports have no detected cycle, provider adapters do not
own catalog operations, and Phase 2 could import services without CLI imports. The dominant
architectural defect is that a materialized DuckDB view remains an authorization result after
its evidence becomes invalid. `verify_integrity` is an optional check, not a query-time gate or
an invalidation transaction. The lifecycle model is a generic DAG plus label presence rather
than an authenticated dataset state machine.

## H. Evidence Authentication Assessment

The exact original `{}` bypass now fails with `EvidenceIntegrityError`, no research-ready rows,
no promotion lineage, and no additional final promoted manifest. Missing reports, changed
checksums, wrong dataset/run identities, blocking findings, Parquet size/schema/hash changes,
missing source/raw data, and unsupported manifest models also fail the intended path.

Authentication remains incomplete because the configuration hash is not derived from or
verified against the snapshot, validation-report ID is not linked to report content, paths are
not constrained to the project root, and lifecycle relationship labels need not connect the
dataset, catalog registration, and promotion IDs.

## I. Manifest, Lineage, and Catalog Consistency

An honest successful fixture ends at `REGISTERED`/`PUBLISHED` and is queryable after restart.
Its Parquet checksum, size, schema fingerprint, source/raw checksum, validation checksum, and
lineage checksum agree. Stale and adversarial combinations do not reliably remove visibility.
Non-promoted registry rows are excluded from verification, and promoted rows do not require
promotion journal or successful run evidence.

## J. Transactional Publication and Recovery

Atomic Parquet publication and normal Python-exception compensation pass. The cross-store
publication is not crash-safe: DuckDB commits before promotion journal and final run evidence.
There is no startup reconciliation that demotes incomplete publications. Ordinary demotion
also fails the requirement that final manifest, catalog, and lineage agree. Rebuild from honest
v3 evidence passes, but mixed valid/unsupported evidence leaves a partial target.

## K. Security Identity and Mapping

`SecurityId.assign` and `SecurityId.canonical(stable_listing_key, venue, MIC)` support stable
listing identity, and effective-dated symbol history is persisted. `valid_to` is inclusive in
code. Ticker reuse after the inclusive end is supported. Documentation does not define a full
exchange-migration transition policy.

The mapping boundary is not institutional-safe: issuer ambiguity can be ignored when a
resolved record coexists, SEC rows can carry arbitrary caller IDs, and a legacy public
ticker-derived constructor remains in use by tests. No Phase 2 join service exists, so a safe
Yahoo-SEC join cannot be verified.

## L. Temporal and Unit Integrity

SEC period, filing, inferred availability, and retrieval ordering are enforced; invalid rows
quarantine. Phase 2 must still define next-session use for date-level availability. Owner-unit
field names and allowed tokens are checked, but declared units are not compared with record
units or series semantics, as the accepted percent-versus-shares probe demonstrates.

## M. Storage and Immutability

Raw and standardized Parquet artifacts are application-immutable and checksum protected;
Parquet uses temporary write, readback, fsync attempt, and atomic replace. Other critical JSON
evidence is immutable-by-content but not atomically written. No empirical or operational data
is tracked.

## N. Test Quality and Coverage

All 68 offline tests passed twice with 90.11% branch-aware coverage. There are no skips,
xfails, broad coverage exclusions, or detected live calls. Tests are substantially behavioral,
but the suite does not test connected lifecycle authentication, revocation after integrity
failure, abrupt termination, demoted-manifest agreement, mixed ambiguity, configuration-hash
binding, atomic rebuild, or declared-versus-row unit reconciliation. Passing coverage therefore
does not establish the failed integrity guarantees.

## O. Security, Privacy, Licensing, and Repository

The MIT text is standard and identifies `AMIT KUMAR DUDI` for 2026. Documentation correctly
separates repository licensing from external-data rights. `.env.example` contains empty
placeholders and SEC live retrieval requires a real configured contact. Current-tree and
history scans found no credential pattern, private key, empirical CSV/Parquet, DuckDB/database,
generated manifest, cache, log, absolute user path, or unexpected binary. The only tracked CSV
is one header line. The largest Git blob is `uv.lock` at 323,599 bytes.

## P. Documentation Consistency

Local Markdown links pass. Historical failed verdicts are preserved, owner approvals are
aligned, later decisions remain open/proposed, and no Phase 2 implementation is claimed.
Current lifecycle, identity, authentication, and recovery claims are not accurate for the
failure modes above. Historical v2 reports are appropriately historical; the specific current
ticker-derived identity sentence in `DATA_CONTRACTS.md` is contradictory rather than historical.

## Q. Live Integration Status

**LIVE INTEGRATION VALIDATION PENDING**

No network data was downloaded and no credentials or SEC contact identity were fabricated.
This is a limitation, not an independent blocker; the offline Critical and High defects block
merge regardless.

## R. Acceptance Criteria

| Area / criterion | Result | Evidence |
|---|---|---|
| Governance approvals preserved | PASS | Decision register and config align; no Phase 2 code |
| Licensing clear; no empirical data | PASS | MIT/external-rights text and repository scans |
| Typed, strict, deterministic configuration | PASS WITH NON-BLOCKING WARNING | Models/hash deterministic; persisted snapshot does not authenticate the hash |
| Immutable configuration snapshots | PASS WITH NON-BLOCKING WARNING | Overwrite refused; writes are not atomic |
| Stable listing/issuer/symbol model | FAIL | Legacy ticker-derived constructor and unenforced SEC mapping |
| Effective-dated ambiguity preservation | FAIL | Mixed ambiguous/resolved issuer evidence resolves |
| Approved adapters and explicit failures | PASS WITH NON-BLOCKING WARNING | Offline adapters pass; live validation pending |
| Owner inputs strict and units semantic | FAIL | Percent declaration with `shares` row accepted |
| Raw and Parquet immutability | PASS | Checksum and collision probes |
| DuckDB is disposable, not source of truth | FAIL | Stale view remains queryable; partial rebuild remains usable |
| Persisted/authenticated manifests and lineage | FAIL | Disconnected lifecycle and config mismatch accepted |
| Restart reconstruction and stale-state detection | FAIL | Honest restart passes; crash/tamper state stays visible |
| Temporal validation and quarantine | PASS | SEC and market tests |
| Gated and recoverable publication | FAIL | Abrupt failure remains research-ready |
| At least 90% meaningful offline coverage | PASS WITH NON-BLOCKING WARNING | 68 passed, 90.11%; critical scenarios absent |
| Accurate complete documentation | FAIL | Current identity/lifecycle/recovery claims overstate behavior |

## S. Phase 2 Readiness Answers

| # | Answer | Evidence |
|---:|---|---|
| 1 | NO | Disconnected lifecycle can authorize a validated view |
| 2 | YES | Tampered evidence remained visible after verification failed |
| 3 | NO | Exact `{}` initial-promotion probe is blocked |
| 4 | NO | Initial missing-report promotion blocks, but later loss does not revoke access |
| 5 | NO | Legacy in-memory promotion API is absent |
| 6 | YES | Parquet identities are immutable |
| 7 | NO | Configuration identity and validation-report ID are not fully bound |
| 8 | YES | Demoted catalog row can retain a `PUBLISHED` final manifest |
| 9 | YES | Stale promoted catalog state survives evidence loss |
| 10 | YES | Disconnected lifecycle labels were accepted |
| 11 | NO | No complete lifecycle state-machine reconstruction exists |
| 12 | YES WITH LIMITATION | Honest v3 rebuild works; mixed evidence leaves a partial catalog |
| 13 | YES WITH LIMITATION | Unsupported models reject, but rebuild is partial and exception is not integrity-specific |
| 14 | NO | Ordinary exceptions demote; abrupt termination does not |
| 15 | YES WITH LIMITATION | Intended APIs are stable; public legacy constructor is ticker-dependent |
| 16 | YES | Symbol intervals are persisted and effective-dated |
| 17 | YES | `IssuerId` and `SecurityId` are distinct types |
| 18 | YES | Legacy registrant helper can map a sole CIK candidate directly to a listing |
| 19 | NO | Mixed ambiguous/resolved issuer evidence silently resolves |
| 20 | NO | No enforced safe join boundary exists; SEC accepts caller listing IDs |
| 21 | YES WITH LIMITATION | SEC timing is conservative date-level evidence |
| 22 | NO | Period end and availability are separately modeled and validated |
| 23 | NO | Declared owner units can contradict row/source units |
| 24 | NO | Adapter reads owner files without editing them |
| 25 | NO | Exact columns/types are required, but semantic unit consistency is not guessed safely |
| 26 | YES WITH LIMITATION | Byte-native sources reprocess; Yahoo byte reprocessing is unsupported |
| 27 | YES | Empty, partial, failed, and valid responses are distinguished |
| 28 | YES WITH LIMITATION | Both are recorded; configuration hash is not authenticated from snapshot |
| 29 | YES WITH LIMITATION | Raw/Parquet chain exists; publication lifecycle can be disconnected |
| 30 | NO | Fixtures use temporary roots and no operational fixture path was found |
| 31 | YES WITH LIMITATION | Layering permits it, but no safe query boundary revokes invalid views |
| 32 | YES | Live status is explicitly pending |
| 33 | NO | New Critical and High defects remain |
| 34 | YES | Material publication, mapping, recovery, unit, and documentation changes remain required |

Answers are literal to each question; for negatively phrased questions, `YES` identifies the
unsafe capability.

## T. Defect Register

| ID | Severity | Evidence | Consequence | Required remediation | Blocker |
|---|---|---|---|---|---|
| FR-C01 | Critical | Disconnected registration/promotion edges re-promoted data | Incomplete lineage can authorize research use | Validate the exact connected dataset-registration-promotion chain, IDs, order, state, and evidence | Yes |
| FR-C02 | Critical | Deleted validation report; verifier failed but view returned one row | Known-invalid evidence remains consumable | Make verification failure transactionally demote/rebuild, and gate reads on authenticated state | Yes |
| FR-C03 | Critical | Abrupt termination left ready row without promotion/run evidence; verifier passed | Crash can publish unauthenticated data | Add crash-recoverable publication journal/state, startup reconciliation, and read-time safety | Yes |
| FR-H01 | High | Demotion left final manifest `PUBLISHED`; verifier passed | Authoritative evidence contradicts catalog | Persist immutable demoted state/event authority and verify all registry rows | Yes |
| FR-H02 | High | `{}` snapshot plus new checksum retained old config hash; arbitrary report ID accepted | Reproducibility identity can be substituted | Bind canonical redacted snapshot/config identity and report IDs cryptographically | Yes |
| FR-H03 | High | Mixed ambiguity resolved; SEC caller ID accepted; ticker-derived constructor remains | Wrong share class can join market/fundamental data | Validate mapping stores, require them at ingestion/join boundaries, remove unsafe constructor path | Yes |
| FR-H04 | High | Unsupported evidence left partial ready rebuild target | Failed recovery can look usable | Rebuild in a temporary catalog and publish atomically only after complete verification | Yes |
| FR-H05 | High | Declared percent with row unit shares accepted | Risk-free/macro magnitude can be misinterpreted | Reconcile request, row, series, source, standardized units and persist the mapping | Yes |
| FR-M01 | Medium | Only demotion uses full event; no lifecycle state-machine validator | Invalidation/supersession and audit history are incomplete | Implement one append-only state transition model and reconstruction validator | Yes, because lifecycle affects isolation |
| FR-M02 | Medium | Direct JSON writes; no stale-lock recovery | Crash can leave corrupt evidence or availability lock | Atomic writes/fsync and documented deterministic lock recovery | Yes, because recovery is affected |
| FR-M03 | Medium | Current docs contradict code/probes | Operators may trust controls that do not exist | Align documentation after implementation remediation | Yes before merge |

## U. Merge Readiness

The branch is **not ready** for a pull request intended to merge Phase 1 into `main`. A review
PR may be used for discussion, but it must not be approved or merged while these blockers
remain. Phase 2 is not authorized.

## V. Final Verdict

**PHASE 1 FINAL RE-AUDIT FAILED — MATERIAL DEFECTS REMAIN**

## W. Next Action

> Resolve all blocking defects and rerun the final independent audit. Do not merge and do not authorize Phase 2.
