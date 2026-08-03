# Phase 1 Data Contracts

All tabular contracts are version `1.0.0`, use deterministic column order, and are enforced by PyArrow plus reusable semantic validators. Metadata/manifests use strict Pydantic v2 models. Unknown fields are rejected in configuration and manifests.

| Contract | Primary key | Required content | Temporal semantics |
|---|---|---|---|
| Security master | `security_id` | ticker, issuer, exchange, asset/listing type, currency/country, listing/source IDs, provenance, quality | listing interval, retrieval, availability |
| Daily market | `security_id, trading_date` | ticker, OHLC/close, volume, source, retrieval, version | exchange-local session date; no forward fill |
| Corporate actions | `security_id, action_id` | type, effective date, value, source | provider effective date |
| Macro observations | `series_id, observation_date` | value/null marker, source unit/frequency, source/retrieval | source observation; release availability only if known |
| French factors | `dataset_identifier, factor_date, factor_name` | value, original/standard units, frequency/source | published date; percent-to-decimal transformation recorded |
| SEC facts | CIK, taxonomy, concept, unit, period end, filing, accession | entity, value, form, fiscal metadata, source/retrieval/availability | filing after period; availability not before filing |

Manifest contracts contain:

- **Run:** ID/type/times/status, Git and package versions, configuration hash/snapshot, requests, outputs, warnings/errors.
- **Source:** source/request/time/status, raw path/hash, rows/date coverage, partial failures, rate-limit and terms notes.
- **Dataset:** ID/type/schema, parents/transformation, dimensions/key/date/security/missingness, validation/quarantine, Parquet/catalog, configuration/code/lineage.
- **Validation report:** dataset/source/run/schema, requested/observed range, counts, deterministic findings/status/quarantine path.

## Security identity

`SecurityId` is UUIDv5-derived from normalized source, ticker, exchange, and source identifier. It is stable for identical listing metadata, distinguishes exchanges and source identities, and never invents ISIN/CUSIP. Ticker changes still require an effective-dated mapping in later owner data; ticker alone is never the permanent key.

## Units and nullability

Prices/yields/factor values are numeric, never formatted strings. FRED DGS3MO remains percent per annum. French source percentages are preserved in metadata and standardized to decimal return explicitly. SEC facts retain provider unit. Required keys/provenance cannot be null. Source-declared missing observations remain null with an explicit indicator; they are not interpolated.

The header-only `examples/templates/security_universe.csv` is a schema aid and contains no securities or empirical values.
