# Phase 1 Material Defect Remediation Report

## Status and scope

**Phase 1 remediated — independent re-audit required.**

This report maps remediation of the independent findings at audit commit `89c2a08691a9203190ac09e614a0f88fa3e82aad`. It does not erase that audit, authorize Phase 2, claim live-source validation, or claim empirical data fitness. No provider dataset, credential, research feature, model, portfolio, API, or dashboard was introduced.

## Defect remediation matrix

| Audit ID | Original failure/root cause | Remediation and files | Regression evidence | Residual limitation | Status |
|---|---|---|---|---|---|
| P1-AUD-C01 | String dispatch did not match SEC/French contract names, bypassing temporal/source rules | Contract-keyed validator registry; SEC v2 chronology and availability-quality checks in `services.py`, `validation.py`, `contracts.py`, `sec_edgar.py` | Invalid SEC end-to-end quarantine; filing/availability/retrieval/instant/duration tests | SEC date-level availability is not intraday acceptance time | Remediated |
| P1-AUD-C02 | Parquet final path was always replaced | `ParquetStorage.publish` uses content/config/schema-addressed IDs, temporary validation, idempotent checksum reuse, conflict refusal, and manifested checksum/size | Same-content reuse, different-content conflict, unchanged original, temp cleanup, physical checksum assertions | Atomic rename/fsync remain filesystem/platform dependent | Remediated |
| P1-AUD-C03 | Catalog accepted arbitrary status and immediately created a validated view | Registration and promotion separated; promotion checks eligible status, checksum, manifest, lineage; views rebuild only from promoted PASS/warning rows | FAIL/QUARANTINED/checksum/lineage rejection, PASS promotion, idempotence, demotion, rollback visibility | Local catalog uses resolved physical paths and must be rebuilt after relocation | Remediated |
| P1-AUD-H01 | Source-dependent IDs had no canonical cross-source map | Source-independent listing UUID plus immutable effective-dated mapping store with resolved/ambiguous/conflict outcomes and registrant semantics | Yahoo/owner convergence, CIK ambiguity, restart, ticker reuse, active conflict tests | Mapping evidence remains owner/provider supplied; no commercial master is claimed | Remediated |
| P1-AUD-H02 | Lineage graph was memory-only | Immutable v2 lineage document/store with typed edges, evidence paths, Git/config/run/transformation identity, parent and cycle validation; service persists full chain | Restart reconstruction, missing parent, duplicate edge, cycle, reprocessing, service-chain tests | Catalog rebuild is deterministic by replaying verified manifests; no separate bulk command yet | Remediated |
| P1-AUD-H03 | Output hash, Git, validation link, parameters, response and returned coverage were incomplete | v2 run/source/dataset/promotion manifests require complete evidence; output checksum/size/schema fingerprint/Git/units/temporal policy added | Manifest lifecycle/evidence validation and service artifact assertions | Secrets remain redacted, so secret values are intentionally not recoverable from snapshots | Remediated |
| P1-AUD-H04 | Catalog mutation preceded coherent final evidence and failures could leave visibility | Raw verification, validation, immutable Parquet, report, lineage and eligible manifest precede promotion; promotion failure is non-visible; post-promotion failure triggers deterministic demotion; raw/evidence remain | Fault-injected post-promotion failure, no research-ready row, raw preserved | Unpromoted immutable Parquet may remain as explicit failure evidence | Remediated |
| P1-AUD-H05 | Owner files allowed incomplete metadata and schema projection | Exact columns/schema/version and explicit ownership/units/date/identifier semantics required for CSV/JSON/Parquet; original bytes preserved | Missing metadata/schema, extra fields, wrong version, empty units, valid/corrupt Parquet, unchanged file tests | Contract-specific units are asserted as metadata, not economically reconciled across datasets | Remediated |
| P1-AUD-H06 | Governing register still called implemented Phase 1 decisions proposed/open | Owner Decision Register and final baseline now record only previously explicit Phase 1 approvals; later-phase/open decisions remain untouched | Documentation/config consistency and local-link review | Historical constituents remain open for historical membership claims | Remediated |
| P1-AUD-M01 | Market calendar unused by ingestion | Configurable XNYS coverage ratio, listing-window adjustment, missing-session evidence, and out-of-range blocking integrated only for daily market | Holiday/weekend, listing boundaries, missing session, complete ingestion, out-of-range tests | Suspensions require explicit external evidence and are warnings, never guessed | Remediated |
| P1-AUD-M02 | No running evidence; final writer could unlink prior manifest | Immutable `run-started.json` plus terminal `run.json`; transition validators prohibit invalid completion/output/error states; retries are new run IDs | Running/completed/failed lifecycle tests and service failure evidence | Cross-process resume creates a new explicit run rather than mutating an old one | Remediated |
| P1-AUD-M03 | Findings lacked actionable metadata | Finding model adds rule version, dataset/source/time, affected count, representative keys, remediation and deterministic report ordering | Coverage/temporal report-field assertions | Some generic schema findings cannot safely include example values | Remediated |
| P1-AUD-M04 | SEC midnight timestamp could imply premature availability | UTC end-of-filing-date plus `INFERRED_DATE_LEVEL`; retrieval must not precede availability; next-session choice deferred explicitly | Availability-before-filing/retrieval-before-availability/quality tests | Exact SEC acceptance time is not reconstructed from company-facts response | Remediated with documented limitation |
| P1-AUD-M05 | Integrity and source workflows were incomplete in CLI | Added validated-only listing, standardized verification, catalog integrity, lineage/dataset inspection, and existing-raw reprocessing commands | Temporary-directory CLI success/failure/help/inspection/reprocessing tests | Yahoo DataFrame-derived raw representation is not reprocessable by the byte adapters | Remediated with non-blocking limitation |
| P1-AUD-L01 | Supporting wording and collection behavior were stale | Documents updated; authoritative execution remains `uv run pytest`, not coverage-gated collection-only | Full documented gate run | `pytest --collect-only` still inherits configured coverage and is not an authoritative gate | Non-blocking |

## Schema and compatibility

- Run, source, dataset, promotion, validation, and lineage evidence use schema `2.0.0`.
- SEC financial facts use contract `2.0.0` due to required `availability_quality`; all other table contracts remain `1.0.0`.
- DuckDB catalog schema is `2.0.0`, with separate registered/promoted state and standardized checksum/lineage evidence.
- Runtime v1 manifests and catalogs are rejected. Because no empirical artifact is committed, delete/rebuild any local experimental catalog after preserving raw evidence; no complex migration framework is warranted.
- The header-only universe template remains data-free and unchanged; mapping evidence is a runtime artifact rather than a fake template row.

## Controlled publication

The remediated order is: immutable started-run/config evidence; retrieval or verified raw reuse; exact standardization; common/source/calendar/temporal validation; quality report and source evidence; immutable Parquet publication; persisted complete lineage; eligible dataset manifest; structurally verified DuckDB promotion; promotion manifest; terminal run evidence. A critical finding quarantines raw evidence. A failure after promotion invokes demotion, and prior published artifacts are never deleted or replaced.

## Original adversarial attacks after remediation

1. Invalid SEC chronology: produces critical `filing_after_period`, quarantines, final run `FAILED`, and leaves no research-ready catalog row.
2. Parquet overwrite: different bytes under the same immutable identity raise `PublicationConflictError`; original bytes/checksum remain unchanged. Identical content is reused without rewrite.
3. Failed dataset view access: `FAIL` and `QUARANTINED` can be registered as lifecycle evidence but `promote` raises `PromotionError`; no `validated_*` view includes them.

## Validation evidence

The final remediation gate must record exact results in the task closeout. The development suite at documentation time contained 60 passing offline tests with 90.38% branch-aware coverage; `services.py` had 93% direct coverage. Ruff lint/format and strict Mypy passed. Live integration remains **LIVE INTEGRATION VALIDATION PENDING**.

## Residual limitations

- An independent agent must rerun the complete audit; this report is implementation-team evidence.
- Public providers retain availability, quality, licensing, and service-level limitations.
- Canonical mapping requires explicit evidence and deliberately refuses ambiguous CIK/share-class joins.
- Date-level SEC availability does not claim intraday precision; Phase 2 must choose and test a next-session rule.
- No point-in-time historical universe is included; historical membership claims still require approved lawful data.
- Local DuckDB is disposable query state and must be rebuilt after path relocation or v1 schema detection.

## Final remediation status

**Phase 1 remediated — independent re-audit required.** Do not authorize Phase 2 or merge to `main` until a fresh independent audit passes.
