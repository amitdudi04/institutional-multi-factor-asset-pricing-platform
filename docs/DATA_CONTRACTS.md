# Phase 1 Data Contracts

Tabular contracts use deterministic column order and exact PyArrow enforcement. SEC financial facts are version `3.1.0`; SEC filing submissions are version `1.1.0`; other table contracts remain `1.0.0`. Dataset manifests and DuckDB catalog state use strict schema `5.0.0`; lifecycle events/lineage and promotion envelopes use `4.0.0`; run/source envelopes and validation reports remain `2.0.0`. Earlier runtime manifest/lineage/catalog artifacts are unsupported and must be rebuilt; none is committed.

| Contract | Primary key | Required content | Temporal semantics |
|---|---|---|---|
| Security master | `security_id` | ticker, issuer, exchange, asset/listing type, currency/country, listing/source IDs, provenance, quality | listing interval, retrieval, availability |
| Daily market | `security_id, trading_date` | ticker, OHLC/close, volume, source, retrieval, version | exchange-local session date; no forward fill |
| Corporate actions | `security_id, action_id` | type, effective date, value, source | provider effective date |
| Macro observations | `series_id, observation_date` | value/null marker, source unit/frequency, source/retrieval | source observation; release availability only if known |
| French factors | `dataset_identifier, factor_date, factor_name` | value, original/standard units, frequency/source | published date; percent-to-decimal transformation recorded |
| SEC facts | CIK, taxonomy, concept, unit, period start, period end, filing, accession | entity, value, form, fiscal metadata, source/retrieval/availability and availability quality | period start ≤ end ≤ filing ≤ date-level availability ≤ retrieval |
| SEC filing submissions | CIK, accession | entity, filing/report dates, verbatim acceptance text, form, nullable primary document, XBRL flags, retrieval/availability quality | offset-bearing acceptance is normalized to UTC; naive text remains verbatim and uses conservative date-level availability |

Manifest contracts contain:

- **Run:** ID/type/times/status, Git and package versions, configuration hash/snapshot, requests, outputs, warnings/errors.
- **Source:** source/request/time/status, raw path/hash, rows/date coverage, partial failures, rate-limit and terms notes.
- **Dataset:** content/config/schema-addressed ID, schema fingerprint, parents/transformation, dimensions/key/date/security/missingness/units, mapping status and content-bound mapping authority, validation evidence, Parquet checksum/size, Git/config/temporal policy, lineage completeness and promotion eligibility.
- **Promotion:** immutable envelope identity, run/dataset-manifest binding, output checksum, lineage, eligible validation status, Git/config identity, terminal lifecycle event, terminal-run path, and promotion time.
- **Validation report:** dataset/source/run/schema, requested/observed range, counts, deterministic findings/status/quarantine path.

## Security identity

Canonical `SecurityId` values are permanently assigned 128-bit internal identifiers and become authoritative only through persisted reference/mapping evidence; direct caller-derived canonical construction is prohibited. Effective-dated provider mappings connect Yahoo/owner listing identifiers to them. SEC CIK deterministically identifies an `IssuerId`, not a share class; an explicit unique effective-dated mapping is required before issuer facts can join a listing. Caller-supplied IDs and mixed resolved/ambiguous evidence are rejected centrally at publication. `valid_to` is inclusive; a replacement interval begins strictly after the prior inclusive end. No ISIN/CUSIP is invented, and no complete commercial security master is claimed.

## Units and nullability

Prices/yields/factor values are numeric, never formatted strings. FRED DGS3MO/TB3MS remain percent per annum. French source percentages are preserved and explicitly transformed to decimal return. Market prices are USD, volume is shares, and SEC facts retain XBRL units. Request declarations, source/series authority, row units, standardized units, and persisted transformation metadata must agree; contradiction blocks publication. Required keys/provenance cannot be null. Source-declared missing observations remain null with an explicit indicator; they are not interpolated.

The header-only `examples/templates/security_universe.csv` is a schema aid and contains no securities or empirical values.

## Schema v5 publication and identity

Dataset manifests and DuckDB catalog state use `5.0.0`; lifecycle events/lineage and promotion envelopes use `4.0.0`; SEC facts use `3.1.0`; SEC filing submissions use `1.1.0`; SEC inline-XBRL listing facts use `1.0.0`; run/source envelopes and validation reports remain `2.0.0`; other tabular contracts remain `1.0.0`. The inline-XBRL contract preserves filing identity, exact DEI concept/value, context, dimensions, availability, and raw complete-submission/primary-document evidence. Only registered cover concepts are admitted; a mismatched accession, CIK, document type, context, continuation, or archive layout fails closed. Every adapter standardization binds the raw artifact's exact retrieval timestamp, including raw-only restart, so provider bytes cannot acquire a new temporal identity during reprocessing. Runtime earlier forms are rejected and rebuilt because no empirical artifacts are committed. The final lifecycle event authenticates the promotion-envelope content hash and expected terminal run; the lifecycle head checkpoint detects tail deletion. Listing ID, issuer ID, and effective-dated symbol history are distinct. Owner-supplied units must exactly cover unit-bearing fields and reconcile with source and row semantics; percent and decimal are never interchangeable without an explicit transformation.

## Phase 3 asset-pricing contracts

The Phase 3 service accepts only an authenticated Phase 2 publication identifier. Its research panel requires Phase 2 `risk_free_rate` and `excess_return` characteristic rows plus exact-date realized quantile portfolios for every configured model-factor mapping. Returns are decimal simple returns. A test asset's dependent variable is its realized portfolio return minus the authenticated same-date risk-free return. Project factors are high-minus-low extreme quantile returns; they are explicitly project-specific and are not relabeled as official provider factors.

Each immutable Phase 3 publication contains exact-schema Parquet tables for coefficients, residuals, model comparison, rolling/expanding coefficients, and influence diagnostics, plus JSON documents for diagnostics, statistical assumptions, validation, configuration, and lineage. The manifest binds every path, checksum, byte size, parent identity, configuration, Git commit, model set, asset set, date range, and validation status. The publication pointer binds the manifest hash. Supported reads authenticate the complete bundle and reject path escape, missing or additional artifacts, schema substitution, content mutation, JSON identity mismatch, and publication/path identity mismatch.

## Phase 4 portfolio contracts

Phase 4 inputs are connected authenticated Phase 2 portfolio/characteristic artifacts and their Phase 3 child manifest. Returns and costs are decimal simple returns; weights and turnover are fractions; basis-point inputs divide by 10,000; half-spread divides by 20,000; VaR/ES are positive losses. Explicit scenario requests support market-crash, interest-rate, volatility, inflation, liquidity, and custom kinds. Exposure vectors derive from authenticated Phase 2 factor-portfolio identity; unmapped shocks and zero contribution are disclosed, and scenario definitions enter publication identity. Output tables contain allocations, transactions, returns, and optimizer diagnostics. JSON reports contain constraints, performance, risk, benchmark reconciliation, executed scenario evidence or `NOT_REQUESTED`, configuration, lineage, and validation. The manifest binds exact columns and every artifact checksum/size; the publication pointer binds the manifest hash.
## Phase 5 contracts

Phase 5 defines versioned feature-schema, target, split-assignment, prediction, explanation, model-card, artifact, manifest, and publication-authority contracts. Target specifications bind the authenticated Phase 1 market dataset/checksum/unit plus benchmark and risk conventions. Evaluation artifacts cover every configured temporal fold and distinguish model-training from evaluation intervals. Calibration, explanations, challengers, feature-family ablations, bootstrap stability, drift, and optional connected Phase 4 economic evidence retain model/fold/configuration identities. Unknown, reordered, late, missing, disconnected, or substituted critical evidence fails closed.

## Phase 6 contracts

Phase 6 defines strict publication references, summaries, deterministic pages, report requests, report records, delivery configuration, error envelopes, and API response identities. Delivery discovery reauthenticates the underlying Phase 1–5 contract. Report manifests bind selected publication kind/ID, exact artifact checksums, configuration and Git identities, software/template versions, generation timestamp, limitations, disclaimer, output filename, and output checksum. API/dashboard clients cannot supply artifact paths, SQL, Python expressions, model files, or template code.
