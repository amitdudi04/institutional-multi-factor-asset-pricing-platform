# Phase 1 Third Remediation Report

## Status and scope

**Phase 1 third remediation complete — another independent final audit is required.**

This report addresses only `FR-C01` through `FR-M03` from the preserved final re-audit at
`e4cfb92`. It does not rewrite that audit, claim Phase 1 passed, authorize Phase 2, validate a
live provider, or introduce analytical functionality. The work used synthetic temporary data
only. **LIVE INTEGRATION VALIDATION PENDING.**

## Repository baseline

- Branch: `phase/1-institutional-data-platform`
- Starting head: `e4cfb92c7a23db833c095a125b1e8f4fdcdabcf3`
- Implementation commit: `24726698dc4f362252d00d77a11f6eff18d18350`
  (`Enforce crash-safe lifecycle and authenticated data access`)
- Adversarial validation commit: `60b861b32bdd3fb8844eda6bd716593391c40c9a`
  (`Expand adversarial recovery and lifecycle validation`)
- Remote: official `origin`; no upstream tracking branch
- Merge/push: neither performed
- Governing documents and earlier audit verdicts: preserved

## Defect closure evidence

| Defect | Original evidence and root cause | Correction and schema effect | Direct tests and failure/restart evidence | Residual limitation | Status |
|---|---|---|---|---|---|
| FR-C01 | Relationship labels anywhere in a DAG could satisfy promotion; identifiers and order were not connected. | V4 evidence authenticates the exact artifact → dataset → registration → promotion chain and binds dataset, run, manifest revision, report, lineage, configuration, catalog, Git commit, predecessor, and state. | Disconnected edges with valid labels are rejected and no ready row is returned; journal identity/ordering/state attacks also fail. | Local evidence depends on filesystem integrity and is not a remote attestation system. | CLOSED |
| FR-C02 | Verification raised but stale DuckDB visibility remained consumable. | Integrity failure demotes the row/view first, appends `INVALIDATED` authority when possible, and the supported research repository authenticates every list/get/read. | Deleted report produces zero authenticated rows, zero catalog-ready rows, `INVALIDATED`, and remains invisible after service restart. | Direct DuckDB-file querying is an unsupported operational bypass; research consumers must use `ResearchDatasetRepository`. | CLOSED |
| FR-C03 | Catalog promotion preceded complete promotion/run evidence; abrupt exit could expose data. | Registration and staging are non-visible. Activation requires durable `FINALIZED` lifecycle evidence; startup reconciliation demotes incomplete or finalized-but-unactivated state. | Real subprocess `os._exit(91)` probes cover registration, final-manifest write, staging, promotion event, run completion, and journal finalization. Every incomplete case returns zero authenticated rows after restart. | Single-host local recovery is provided; distributed consensus is out of Phase 1 scope. | CLOSED |
| FR-H01 | Compensating demotion left `dataset.json` marked `PUBLISHED`, so the manifest alone contradicted current state. | Immutable manifest is historical publication evidence; append-only journal terminal state is authoritative. Demotion/invalidation changes current authority and catalog visibility without overwriting history. | Failure after promotion-manifest persistence leaves historical `PUBLISHED`, terminal `DEMOTED`, zero authenticated rows, and the same result after restart. | Consumers must not infer current authority from a historical manifest alone. | CLOSED |
| FR-H02 | Snapshot checksum could be replaced without matching configuration identity; report ID was arbitrary. | Canonical redacted non-empty configuration bytes determine both checksum/hash and `config:<hash>` identity. Validation report ID is `validation:<content-checksum>`. | Empty/substituted snapshot, changed config identity, arbitrary report ID, missing report, and malformed evidence all fail closed. | Secret values remain intentionally redacted and cannot be reconstructed from evidence. | CLOSED |
| FR-H03 | Ticker-derived constructor, caller-injected IDs, and mixed resolved/ambiguous issuer evidence could cross share classes. | Removed `SecurityId.create`; listing IDs require stable owner-governed keys or persisted assignment. Yahoo requires the mapping store and rejects supplied IDs. SEC always emits issuer ID and permits a listing only through a unique effective-dated mapping. Any active unresolved evidence blocks. | Caller-ID attacks, no-authority Yahoo use, mixed ambiguity, conflicting listing/issuer periods, malformed stores, ticker reuse, and symbol-history identity are tested. | No commercial security master or universal issuer-to-share-class mapping is claimed. | CLOSED |
| FR-H04 | Rebuild wrote directly to the target and could leave a partial usable catalog. | Rebuild authenticates all candidates in a same-directory temporary DuckDB, verifies it, then atomically replaces the target. | Unsupported evidence and injected replacement failure preserve the prior ready catalog. A real subprocess exit at replacement also preserves the active catalog. Successful rebuild returns the authenticated dataset. | An orphan temporary file may remain after process death and is non-authoritative. | CLOSED |
| FR-H05 | Request-declared units could contradict row/source units and persisted metadata. | Reconciliation binds request, row, contract, source/series authority, standardized unit, and transformation. FRED, French, market, and SEC semantics are explicit. | Percent-versus-shares contradiction blocks with zero ready rows; FRED percent-per-annum and French percent-to-decimal valid paths remain covered. | Phase 1 preserves source observations; later return-frequency conventions remain Phase 2 decisions. | CLOSED |
| FR-M01 | Generic lineage plus partial demotion events could not reconstruct one legal lifecycle. | One append-only V4 state machine defines legal publication, recovery, demotion, invalidation, and supersession transitions with contiguous sequences, predecessors, invariant identities, monotonic times, and checksummed events. | Duplicate, reordered, missing predecessor, illegal transition, identity mixing, timestamp reversal, checksum substitution, recovery, demotion, invalidation, and restart reconstruction are tested. Lifecycle module branch coverage is 100%. | `SUPERSEDED` is modeled and validated but no replacement workflow is added in Phase 1. | CLOSED |
| FR-M02 | Authoritative JSON writes were direct and stale lock removal could be unsafe. | Evidence uses canonical JSON, same-directory temporary files, file fsync, atomic replacement, and best-effort directory fsync. Locks record PID/host/run/operation; only proven terminal locks are removed, active locks remain, ambiguity requires intervention. Windows uses a non-signalling process-handle liveness check. | Injected replace failure and real abrupt JSON-write termination never create the target. Terminal, active, malformed, nonpositive, missing-journal, and ambiguous locks fail safely. | Orphan temp files require housekeeping; ambiguity intentionally sacrifices availability. | CLOSED |
| FR-M03 | Documentation described V3 and overstated lifecycle/identity/recovery behavior. | Current governance, architecture, contracts, quality, source, roadmap, specification, README, and historical-report links now describe V4, authenticated reads, crash recovery, identity authority, rebuild, and units without altering old verdicts. | Markdown links, documentation consistency tests, private-path scan, and diff review are final gates. | Another independent audit remains mandatory. | CLOSED |

## Publication lifecycle and crash matrix

| Abrupt boundary | State immediately before exit | Restart result | Research-ready result |
|---|---|---|---|
| Artifact publication | Verified immutable Parquet; no lifecycle journal/catalog registration | No authority can be reconstructed; lock remains manual-intervention evidence | 0 rows |
| Catalog registration | Journal ends `ARTIFACT_PUBLISHED`; registered catalog row is not promoted/finalized | `RECOVERY_REQUIRED → DEMOTED`; catalog demoted; terminal lock recovered | 0 rows |
| Final manifest persistence | Journal ends `PROMOTION_PENDING`; final historical manifest exists | `RECOVERY_REQUIRED → DEMOTED` | 0 rows |
| Catalog promotion/staging | Row is staged `promoted=true, finalized=false`; view is absent | `RECOVERY_REQUIRED → DEMOTED`; staged state cleared | 0 rows |
| Promotion-event persistence | Journal ends `PROMOTED`; catalog remains staged | `RECOVERY_REQUIRED → DEMOTED` | 0 rows |
| Run completion | Promotion manifest and successful run exist; journal ends `PROMOTED` | Incomplete lifecycle is demoted despite successful run envelope | 0 rows |
| Journal finalization | Journal ends `FINALIZED`; catalog remains staged and invisible | `DEMOTION_PENDING → DEMOTED` for incomplete activation | 0 rows |
| Catalog rebuild activation | Complete temporary catalog exists; active catalog not replaced | Existing active catalog remains authenticated and readable | Prior ready row retained |
| Atomic JSON replacement | Fully written/fsynced temporary exists; target absent | Target remains absent | No partial authority |

Normal publication activates the view only after `FINALIZED`. Read-time loss of any required
evidence demotes visibility before returning control, records `INVALIDATED` when the journal is
intact, and remains invisible after restart.

## Authenticated read gate

`ResearchDatasetRepository` is the supported future-research boundary. A returned
`VerifiedDatasetHandle` binds dataset ID, path, checksum, schema, units, configuration hash, Git
commit, validation status, mapping status, and temporal policy. `read_table` reuses this gate.
Catalog listing with `research_ready_only=True` verifies current evidence, and the CLI
`list-datasets --research-ready` uses the repository. Missing, tampered, disconnected, demoted,
invalidated, incomplete, or non-finalized evidence returns no authenticated dataset.

## Identity and unit authority

- Listing identity is not ticker identity. Tickers live in effective-dated symbol history.
- SEC CIK maps deterministically to issuer identity, never automatically to one listed share class.
- Yahoo and SEC reject caller-injected security IDs.
- Mixed resolved and ambiguous evidence is ambiguous; conflicts are preserved and rejected.
- Unit metadata records observed/requested/contract/standardized/transformation relationships.
- FRED `DGS3MO`/`TB3MS` remain `percent_per_annum`; French percent becomes explicit
  `decimal_return`; market prices/volume are USD/shares; SEC retains XBRL units.

## Schema and rebuild impact

| Artifact | Current version | Compatibility action |
|---|---:|---|
| Dataset manifest | 4.0.0 | Reject and deterministically rebuild uncommitted V1–V3 runtime artifacts |
| Lifecycle event and lineage | 4.0.0 | Reject earlier lifecycle authority; regenerate from approved raw evidence |
| DuckDB catalog | 4.0.0 | Atomically rebuild from fully authenticated V3 promotion manifests |
| Promotion manifest | 3.0.0 | Requires exact final lifecycle event identity |
| SEC facts | 3.0.0 | Rebuild to add required issuer identity |
| Run/source/validation envelopes | 2.0.0 | Unchanged |
| Other tabular contracts | 1.0.0 | Unchanged |

No empirical runtime artifact is committed, so deterministic rebuild is the approved migration
path. No migration subsystem or Phase 2 compatibility layer was introduced.

## Validation evidence

Final gate results recorded for this remediation:

- `uv sync --all-groups`: PASS; 56 packages resolved, 54 checked.
- `uv run pytest`: PASS; 97 tests in 39.83 seconds; no skip or xfail; 90.10%
  branch-aware total coverage.
- Critical direct coverage: lifecycle 100%, authenticated access/recovery 92%, identity 94%.
- Alternate `PYTHONHASHSEED=271828`: PASS; 97 tests in 35.84 seconds without coverage.
- `uv run coverage report`: PASS; threshold at least 90%.
- `uv run ruff check .`: PASS.
- `uv run ruff format --check .`: PASS; 54 files formatted.
- `uv run mypy src`: PASS; 26 source files.
- `uv lock --check`: PASS.
- Package import smoke: PASS.
- CLI help matrix: PASS for all 16 commands.
- Authenticated-read, lifecycle reconstruction, startup reconciliation, atomic rebuild, atomic
  JSON, and abrupt termination probes: PASS within the main test suite.
- Import-cycle analysis: PASS for 26 package modules.
- Markdown local-link check: PASS.
- Secret/private-key and credential-assignment scans: PASS; no candidates.
- Private-path scan: PASS.
- Tracked inventory: 62 files; zero tracked ignored files, zero files over 1 MiB, and zero
  binary candidates.
- One tracked delimited file is the verified header-only
  `examples/templates/security_universe.csv`; it has no records or empirical values.
- Git diff/whitespace check: PASS.
- Live provider validation: not run; `LIVE INTEGRATION VALIDATION PENDING`.

## Data integrity and limitations

- No empirical data, provider response, database, cache, generated report, or credential is added.
- The tracked CSV is the existing header-only universe template, not a dataset.
- No raw or standardized artifact is overwritten; synthetic fixtures use temporary directories.
- No financial value, provider identity, credential, or live-integration output is fabricated.
- No factor, return, portfolio, backtest, model, API, dashboard, or other Phase 2+ feature is added.
- Local filesystem/DuckDB controls are not distributed transactions, remote attestation, licensed
  data governance, or production multi-user authorization.
- Direct access to a DuckDB file cannot be made impossible on an owner-controlled filesystem; it is
  explicitly unsupported for research. The authenticated repository is the enforceable software
  boundary for future consumers.

## Final remediation status

All eleven final re-audit defect IDs have implementation and adversarial-test closure evidence.
There are no known remaining Critical, High, or blocking Medium defects within the authorized
third-remediation scope. Historical audits remain unchanged and Phase 2 remains unauthorized.

**Phase 1 third remediation complete — another independent final audit is required.**
