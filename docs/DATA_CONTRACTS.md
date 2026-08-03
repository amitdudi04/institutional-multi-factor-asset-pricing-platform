# Phase 1 Data Contracts

Tabular contracts use deterministic column order and exact PyArrow enforcement. SEC financial facts are version `3.0.0`; other table contracts remain `1.0.0`. Dataset manifests, lifecycle events/lineage, and DuckDB catalog state use strict schema `4.0.0`; promotion envelopes use `3.0.0`, while run/source envelopes and validation reports remain `2.0.0`. Earlier runtime manifest/lineage/catalog artifacts are unsupported and must be rebuilt; none is committed.

| Contract | Primary key | Required content | Temporal semantics |
|---|---|---|---|
| Security master | `security_id` | ticker, issuer, exchange, asset/listing type, currency/country, listing/source IDs, provenance, quality | listing interval, retrieval, availability |
| Daily market | `security_id, trading_date` | ticker, OHLC/close, volume, source, retrieval, version | exchange-local session date; no forward fill |
| Corporate actions | `security_id, action_id` | type, effective date, value, source | provider effective date |
| Macro observations | `series_id, observation_date` | value/null marker, source unit/frequency, source/retrieval | source observation; release availability only if known |
| French factors | `dataset_identifier, factor_date, factor_name` | value, original/standard units, frequency/source | published date; percent-to-decimal transformation recorded |
| SEC facts | CIK, taxonomy, concept, unit, period end, filing, accession | entity, value, form, fiscal metadata, source/retrieval/availability and availability quality | period start ≤ end ≤ filing ≤ date-level availability ≤ retrieval |

Manifest contracts contain:

- **Run:** ID/type/times/status, Git and package versions, configuration hash/snapshot, requests, outputs, warnings/errors.
- **Source:** source/request/time/status, raw path/hash, rows/date coverage, partial failures, rate-limit and terms notes.
- **Dataset:** content/config/schema-addressed ID, schema fingerprint, parents/transformation, dimensions/key/date/security/missingness/units, validation evidence, Parquet checksum/size, Git/config/temporal policy, lineage completeness and promotion eligibility.
- **Promotion:** dataset-manifest hash, output checksum, lineage, eligible validation status, Git/config identity, terminal lifecycle event, and promotion time.
- **Validation report:** dataset/source/run/schema, requested/observed range, counts, deterministic findings/status/quarantine path.

## Security identity

Canonical `SecurityId` is UUIDv5-derived only from a stable owner-governed listing key plus exchange/MIC, or permanently assigned in persisted reference data; it is never derived from display ticker text. Effective-dated provider mappings connect Yahoo/owner listing identifiers to it. SEC CIK deterministically identifies an `IssuerId`, not a share class; an explicit unique effective-dated mapping is required before issuer facts can join a listing. Caller-supplied IDs and mixed resolved/ambiguous evidence are rejected. No ISIN/CUSIP is invented, and no complete commercial security master is claimed.

## Units and nullability

Prices/yields/factor values are numeric, never formatted strings. FRED DGS3MO/TB3MS remain percent per annum. French source percentages are preserved and explicitly transformed to decimal return. Market prices are USD, volume is shares, and SEC facts retain XBRL units. Request declarations, source/series authority, row units, standardized units, and persisted transformation metadata must agree; contradiction blocks publication. Required keys/provenance cannot be null. Source-declared missing observations remain null with an explicit indicator; they are not interpolated.

The header-only `examples/templates/security_universe.csv` is a schema aid and contains no securities or empirical values.

## Schema v4 publication and identity

Dataset manifests, lifecycle events/lineage, and DuckDB catalog state use `4.0.0`; promotion envelopes and SEC facts use `3.0.0`; run/source envelopes and validation reports remain `2.0.0`; other tabular contracts remain `1.0.0`. Runtime dataset-manifest/lineage/catalog v1–v3 forms are rejected and rebuilt because no empirical artifacts are committed. Listing ID, issuer ID, and effective-dated symbol history are distinct. Owner-supplied units must exactly cover unit-bearing fields and reconcile with source and row semantics; percent and decimal are never interchangeable without an explicit transformation.
