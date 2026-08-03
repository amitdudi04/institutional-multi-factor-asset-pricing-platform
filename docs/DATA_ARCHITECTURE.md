# Phase 1 Data Architecture

## Data flow

```text
Validated configuration
  -> source adapter request
  -> provider-native immutable raw artifact + source manifest
  -> source-specific standardization
  -> PyArrow contract + quality validation
  -> quarantine on blocking failure
  -> content/config/schema-addressed immutable Zstandard Parquet on pass/warning
  -> persisted v3 lineage and authenticated registered/promoted manifest revisions
  -> persisted-evidence-authenticated DuckDB promotion
  -> promotion and final run evidence + JSON/Markdown quality report
```

Parquet, manifests, and persisted lineage are authoritative. DuckDB registration does not create research visibility; promotion rebuilds `validated_*` views only from checksum-verified `PASS` or `PASS_WITH_WARNINGS` entries. DuckDB remains a local query catalog, not competing truth.

## Package responsibilities

| Module | Responsibility |
|---|---|
| `data.config` | Strict Pydantic v2 models, environment overlays, redaction, canonical hashes/snapshots |
| `data.domain` | Immutable enums, identifiers, requests/results, temporal and security records |
| `data.contracts` | Versioned PyArrow tabular schemas and keys |
| `data.sources` | Approved provider retrieval and source-specific normalization only |
| `data.validation` | Common/source checks, statuses, machine/human reports |
| `data.storage` | Raw checksums, atomic Parquet, quarantine, DuckDB registry |
| `data.manifests` | Validated run/source/dataset metadata |
| `data.lineage` | Immutable machine-readable artifact/relationship evidence and restart reconstruction |
| `data.security_master` | Canonical listing identity, effective-dated provider mapping, and eligibility checks |
| `data.calendar` | XNYS session-date abstraction |
| `data.services` | End-to-end orchestration and promotion control |
| `cli` | Explicit operator commands and nonzero failure status |

Dependencies point from CLI to services to adapters/domain/storage, then to configuration/core primitives. Adapters do not control DuckDB, CLI presentation, factors, or research calculations.

## Storage decisions

Raw bytes retain provider-native form where practical. Standard tables use exact PyArrow schemas and Zstandard Parquet with atomic temporary writes, read-back verification, manifested checksums, idempotent same-content reuse, and conflict refusal. Dataset manifests use relative paths; the local DuckDB catalog resolves physical paths and can be rebuilt because no empirical catalog is committed. Dataset-manifest, lifecycle-lineage, and catalog schema v3 intentionally reject earlier uncommitted runtime artifacts.

## Adapter lifecycle and network policy

Adapters validate explicit requests, retrieve from one approved source, return native payloads, and standardize to a source contract. HTTPX implements positive timeouts, bounded retry count, exponential backoff, optional jitter, no retry for invalid requests, explicit 429 failure, and no provider switching. Yahoo uses yfinance rather than page scraping. Unit tests inject transports/download functions and never use live internet.

## Temporal architecture

Trading dates are exchange-local session dates; storage timestamps are UTC. FRED retains source frequency and missing markers. SEC facts retain period, filing, accession, form, taxonomy, unit, and availability no earlier than filing. Phase 1 does not create factor lags, excess returns, portfolio returns, or analytical features.

## V3 authenticated publication update

Dataset-manifest, lifecycle-lineage, and DuckDB catalog schema v3 replace earlier uncommitted runtime forms. Immutable registered and promoted manifest revisions cryptographically link validation report, lineage, configuration snapshot, source manifest/raw parent, and Parquet evidence. Promotion accepts only dataset ID plus persisted manifest path and reloads all authority. Registration is not visible; verified promotion is the final gate. Post-promotion failure demotes the view and journals the event. Rebuild authenticates both manifest revisions and requires no raw redownload.
