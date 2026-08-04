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
  -> persisted v4 connected lineage and authenticated schema-v5 registered/published manifests
  -> registered and staged DuckDB state (not visible to research)
  -> append-only FINALIZED lifecycle evidence and catalog activation
  -> authenticated research-read handle
```

Parquet, manifests, connected lineage, and the append-only lifecycle journal are authoritative. Registration and staged promotion do not create research visibility; `validated_*` views require finalized authenticated evidence. The supported read repository re-authenticates the evidence bundle and checksum before returning a handle or table. DuckDB remains a replaceable local query catalog, not competing truth.

## Package responsibilities

| Module | Responsibility |
|---|---|
| `data.config` | Strict Pydantic v2 models, environment overlays, redaction, canonical hashes/snapshots |
| `data.domain` | Immutable enums, identifiers, requests/results, temporal and security records |
| `data.contracts` | Versioned PyArrow tabular schemas and keys |
| `data.sources` | Approved provider retrieval and source-specific normalization only |
| `data.validation` | Common/source checks, statuses, machine/human reports |
| `data.storage` | Raw checksums, atomic Parquet, quarantine, DuckDB registry |
| `data.evidence` | Canonical JSON, atomic evidence writes, and project-root path resolution |
| `data.access` | Authenticated research reads, startup reconciliation, and atomic rebuild control |
| `data.manifests` | Validated run/source/dataset metadata |
| `data.lineage` | Immutable machine-readable artifact/relationship evidence and restart reconstruction |
| `data.security_master` | Canonical listing identity, effective-dated provider mapping, and eligibility checks |
| `data.calendar` | XNYS session-date abstraction |
| `data.services` | End-to-end orchestration and promotion control |
| `cli` | Explicit operator commands and nonzero failure status |

Dependencies point from CLI to services to adapters/domain/storage, then to configuration/core primitives. Adapters do not control DuckDB, CLI presentation, factors, or research calculations.

## Storage decisions

Raw bytes retain provider-native form where practical. Standard tables use exact PyArrow schemas and Zstandard Parquet with atomic temporary writes, read-back verification, manifested checksums, idempotent same-content reuse, and conflict refusal. Authoritative JSON uses same-directory atomic replacement and fsync. Dataset manifests use project-root-constrained paths. Catalog rebuild authenticates every candidate in a temporary DuckDB file and replaces the active catalog only after complete success. Dataset-manifest/catalog schema v5 and lifecycle/promotion schema v4 intentionally reject earlier uncommitted runtime artifacts.

## Adapter lifecycle and network policy

Adapters validate explicit requests, retrieve from one approved source, return native payloads, and standardize to a source contract. HTTPX implements positive timeouts, bounded retry count, exponential backoff, optional jitter, no retry for invalid requests, explicit 429 failure, and no provider switching. Yahoo uses yfinance rather than page scraping. Unit tests inject transports/download functions and never use live internet.

## Temporal architecture

Trading dates are exchange-local session dates; storage timestamps are UTC. FRED retains source frequency and missing markers. SEC facts retain period, filing, accession, form, taxonomy, unit, and availability no earlier than filing. Phase 1 does not create factor lags, excess returns, portfolio returns, or analytical features.

## V4 authenticated publication update

Dataset manifests and DuckDB catalog schema `5.0.0` replace earlier uncommitted runtime forms; lifecycle/lineage and promotion manifests use `4.0.0`. Immutable evidence binds the exact dataset, artifact, registration, manifest revision, complete validation report, canonical redacted configuration snapshot, lineage, units, mapping authority, catalog identity, Git commit, promotion-envelope hash, terminal run, and predecessor event. A separately persisted lifecycle-head checkpoint detects tail deletion. The journal validator reconstructs only legal ordered transitions. Publication stays invisible through registration and staging; only a durable `FINALIZED` event plus successful terminal run permits supported reads. Startup reconciliation demotes incomplete transitions, integrity failure invalidates visibility, and ambiguous stale locks remain for manual review. No raw redownload is required for an authenticated rebuild.

## Phase 3 research architecture

Phase 3 does not read raw, interim, DuckDB, or caller-supplied analytical frames through its application service. It authenticates a complete Phase 2 factor publication, then reads the checksum-verified characteristic and realized quantile-portfolio Parquet artifacts. Exact-date joins provide market excess and risk-free values; project-specific high-minus-low factor returns are derived only from configured Phase 2 factor identifiers. Missing, conflicting, future-available, constant, rank-deficient, or insufficient inputs fail closed.

Model definitions, regression estimators, statistical tests, diagnostics, validation, service orchestration, and research-output authentication are separate packages. A Phase 3 publication binds its parent manifest hash, configuration hash, Git commit, models, observation coverage, exact artifact set, checksums, byte sizes, and JSON identities. Parquet schemas are authenticated at read time. Staging evidence is invisible until atomic manifest-directory activation; unreferenced interrupted artifacts are not research-visible, and deterministic retry either reuses identical content or refuses a collision.
