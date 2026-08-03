# Phase 1 Data Architecture

## Data flow

```text
Validated configuration
  -> source adapter request
  -> provider-native immutable raw artifact + source manifest
  -> source-specific standardization
  -> PyArrow contract + quality validation
  -> quarantine on blocking failure
  -> atomic Zstandard Parquet on pass/warning
  -> transactional DuckDB registry/view
  -> dataset/run manifests + JSON/Markdown quality report
```

Parquet and manifests are authoritative standardized artifacts. DuckDB is a local query catalog and does not replace them as the source of truth.

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
| `data.lineage` | Acyclic parent-child relationships |
| `data.security_master` | Stable identity and owner-approved eligibility checks |
| `data.calendar` | XNYS session-date abstraction |
| `data.services` | End-to-end orchestration and promotion control |
| `cli` | Explicit operator commands and nonzero failure status |

Dependencies point from CLI to services to adapters/domain/storage, then to configuration/core primitives. Adapters do not control DuckDB, CLI presentation, factors, or research calculations.

## Storage decisions

Raw bytes retain provider-native form where practical. Standard tables use explicit PyArrow schemas and Zstandard-compressed Parquet with atomic temporary writes and read-back verification. DuckDB stores a registry and stable validated views without copying Parquet. JSON manifests are canonical, versioned, redacted, and immutable. Local paths are represented project-relatively when possible.

## Adapter lifecycle and network policy

Adapters validate explicit requests, retrieve from one approved source, return native payloads, and standardize to a source contract. HTTPX implements positive timeouts, bounded retry count, exponential backoff, optional jitter, no retry for invalid requests, explicit 429 failure, and no provider switching. Yahoo uses yfinance rather than page scraping. Unit tests inject transports/download functions and never use live internet.

## Temporal architecture

Trading dates are exchange-local session dates; storage timestamps are UTC. FRED retains source frequency and missing markers. SEC facts retain period, filing, accession, form, taxonomy, unit, and availability no earlier than filing. Phase 1 does not create factor lags, excess returns, portfolio returns, or analytical features.
