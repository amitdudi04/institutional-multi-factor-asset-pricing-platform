# Phase 1 Second Remediation Report

## Scope and authority

This focused implementation responds to `docs/PHASE1_REAUDIT_REPORT.md` at starting commit `6e561b3b3a3c01c068d1d24d462f2adc096806eb`. It changes only Phase 1 publication authentication, evidence lifecycle, security identity/mapping, owner-unit validation, tests, configuration, and aligned documentation. It does not constitute an independent audit pass or authorize Phase 2.

## Defect closure matrix

| Defect | Root cause | Code/schema correction | Test evidence | Remaining limitation | Status |
|---|---|---|---|---|---|
| RA-C01 / C2-01 | DuckDB trusted a caller's in-memory manifest and only checked evidence-path existence | Removed in-memory register/promote APIs. `authenticate_dataset_evidence` reloads strict persisted v3 manifest, validation, lineage, configuration, source/raw and Parquet evidence; verifies hashes, IDs, run, status, findings, size and schema before identifier-based promotion | `{}` manifest, absent/tampered/substituted evidence, persisted FAIL, dataset mismatch, restart and catalog-integrity probes | Local single-owner filesystem lock semantics; no distributed transaction claim | CLOSED |
| RA-H01 / H2-01 | Canonical listing UUID included mutable ticker | Listing IDs are assigned once or derived only from stable owner-governed listing keys; `SymbolHistoryRecord/Store` preserves effective-dated ticker changes and reuse | Ticker change preserves ID; reuse, overlap, venue/date and restart probes | Correct mapping still requires trustworthy owner/provider evidence | CLOSED |
| RA-H02 / H2-02 | Lineage stopped at manifestation | V3 lineage includes `REGISTERED_IN_CATALOG` and `PROMOTED_TO_RESEARCH_READY`; append-only lifecycle journal records `DEMOTED_FROM_RESEARCH_READY` and supports invalidated/superseded relationship types | Successful-chain and post-promotion demotion/restart tests | Manual invalidation remains an explicit operator/service action | CLOSED |
| RA-H03 / H2-03 | Dataset manifest remained `NOT_REGISTERED/ELIGIBLE` | Immutable `dataset-registered.json` and final `dataset.json` revisions end at `REGISTERED/PUBLISHED`, with registration ID, promotion event/time and evidence checksums | End-to-end state, stale-state, rebuild and restart tests | Earlier uncommitted runtime forms require rebuild | CLOSED |
| RA-H04 / H2-04 | Files and catalog could disagree after partial finalization | Promotion is the final gated operation after final evidence persistence; later failure demotes deterministically and journals evidence; catalog verification reauthenticates persisted authority | Injected post-promotion failure, demotion event, missing/tampered artifact, restart/rebuild tests | Recoverable compensation, not a distributed ACID transaction | CLOSED |
| RA-H05 / H2-05 | Listing and registrant identity were insufficiently separated | Added distinct `IssuerId`, stable listing `SecurityId`, effective-dated symbols, and persisted `IssuerListingMappingStore`; ambiguous issuer/listing joins fail | One/multiple listings per issuer, ambiguity and restart tests | No commercial security master or inferred mapping is claimed | CLOSED |
| RA-M01 / M2-01 | Previously approved monthly and no-short/no-leverage decisions remained proposed | Project Specification now records monthly rebalancing and disabled short/leverage as approved while factor weights, bounds, costs, thresholds, ML and deployment remain proposed/open | Documentation consistency review | Later-phase exact bounds remain owner decisions | CLOSED |
| RA-M02 / M2-02 | Any non-empty units dictionary passed | Contract-specific unit-bearing fields and allowed units are enforced; ambiguous percent/decimal and wrong fields fail | Missing, incompatible, ambiguous, wrong-field and valid-unit tests | Source-specific XBRL units remain preserved rather than globally enumerated | CLOSED |

## Publication and recovery lifecycle

The service writes immutable raw/source/config/validation/Parquet evidence, v3 validated lineage, and an authenticated registered manifest revision. Catalog registration creates no research visibility. It then writes final lifecycle lineage and a `PUBLISHED` manifest revision. DuckDB promotion reloads this persisted bundle, verifies the existing registration, and transactionally rebuilds the validated view. Any subsequent finalization failure demotes visibility and writes an immutable lifecycle event. Catalog rebuild requires authenticated registered and promoted revisions plus promotion evidence.

## Identity model

- `IssuerId` represents the reporting entity; SEC CIK may provide stable issuer evidence.
- `SecurityId` represents one listing/share class and is not derived from ticker.
- `SymbolHistoryRecord` stores effective-dated ticker and venue metadata.
- Provider mappings require explicit stable listing identity; issuer-to-listing mappings remain ambiguous unless evidence resolves exactly one eligible listing.

## Schema and rebuild

Dataset manifests, lifecycle lineage, and DuckDB catalog use `3.0.0`. Run/source/promotion envelopes and validation reports remain `2.0.0`; SEC facts remain `2.0.0`; other tables remain `1.0.0`. Configuration requires manifest schema v3. Runtime dataset-manifest/lineage/catalog v1–v2 forms fail clearly. Because no empirical artifacts are committed, deterministic rebuild from raw/source evidence is the supported path and no migration subsystem was added.

## Validation evidence

The implemented offline suite contains 68 deterministic tests and no skipped or expected-failure tests. The final authoritative quality-gate results, exact bypass output, coverage, static checks, security/repository scans, and commit hashes are recorded in the task closeout after all documentation and Git checks complete.

## Limitations

- **LIVE INTEGRATION VALIDATION PENDING**
- Public-provider availability, quality, and licensing limitations remain.
- Stable identity depends on explicit trustworthy listing and issuer mapping evidence; ambiguity is blocked, not guessed.
- The local single-owner recovery model uses immutable evidence plus deterministic compensation, not distributed transactions.

## Status

**Phase 1 second remediation complete — independent final re-audit required**

Do not merge into `main` and do not authorize Phase 2 until a final independent re-audit passes.
