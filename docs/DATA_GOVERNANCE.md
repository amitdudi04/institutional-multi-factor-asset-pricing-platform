# Data Governance

## Scope and authority

This policy implements Phase 1 under the Development Constitution and Project Specification. Approved sources are Yahoo Finance, FRED, Kenneth French Data Library, SEC EDGAR, and owner-supplied data. A new provider requires owner approval. Public accessibility does not imply institutional quality or redistribution permission.

The repository code and documentation are MIT licensed. External market, macroeconomic, factor, fundamental, and owner data retain their own terms and are never relicensed by this repository.

## Immutable raw evidence

Every retrieval or owner file is persisted before standardization under `data/raw/<source>/<dataset>/<YYYY>/<MM>/<DD>/<timestamp>_<hash>.<ext>`. The manifest records source, request, retrieval time, media type, size, SHA-256, status, and failures. Existing bytes are never overwritten; repeat retrievals deduplicate only when timestamp and content identity coincide. Checksums detect later mutation. Filesystem permissions are not claimed as a portable control.

Raw, interim, processed, manifest-instance, quarantine, output, database, and log contents are ignored by Git. Trackable contracts, templates, documentation, and source code contain no empirical provider payloads.

## Promotion, lineage, and quarantine

Data flows raw → source-specific standardization → schema and quality validation → Parquet → DuckDB registration. Each dataset manifest links the raw checksum, source manifest, configuration hash, code version, schema, transformation, and validation status. Critical failures are retained with their raw bytes and report in quarantine and are not registered as research-ready. Failed artifacts are not deleted automatically and may be reprocessed from raw evidence.

## Retention, access, and deletion

The approved baseline is local owner access only, no public data service, and no redistribution. Raw artifacts are retained until explicit owner deletion. Normal ingestion never deletes data. Source-specific restrictions added later override general retention. Processed artifacts may be regenerated from raw data and manifests. Any deletion requires explicit scope, license review, lineage impact assessment, and a recorded owner action.

## Security and redaction

Credentials remain in environment variables or an untracked `.env`. Configuration snapshots redact FRED keys and SEC contact information. Manifests and logs exclude secrets, authorization headers, large payloads, and sensitive owner records. SEC live retrieval fails unless the owner supplies a valid contact email.

## Reproducibility

Runs record Git commit, package version, configuration snapshot/hash, requested source/dataset, output IDs, warnings, errors, and timestamps. Source and dataset manifests plus checksums reproduce lineage. Unknown availability metadata remains unknown; it is never replaced with period end or retrieval time without an explicit inferred flag.
