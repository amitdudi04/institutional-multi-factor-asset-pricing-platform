# Phase 2 Architecture

## Scope

Phase 2 is a research-only layer over authenticated Phase 1 publications. It computes versioned security characteristics, date-local preprocessing, next-period factor-quantile diagnostics, and immutable evidence. It does not implement asset-pricing regressions, optimization, backtesting, machine learning, an API, or a dashboard.

## Dependency direction

`VerifiedDatasetHandle` → input contracts and unit checks → point-in-time alignment → characteristics → cross-sectional preprocessing → factor quantile diagnostics → validation → immutable Parquet and JSON evidence → authenticated repository reads.

The `factors` package contains separate configuration, contracts, definitions, temporal controls, preprocessing, portfolio diagnostics, validation, persistence, and orchestration modules. The CLI delegates to the service; it contains no research calculations.

## Authenticated input boundary

The service accepts only finalized Phase 1 handles whose exact artifact bytes, validation state, and security-mapping disposition re-authenticate. The two approved preparation contracts are registered in the data layer as `factor_market_input` and `factor_fundamental_input`; owner inputs pass normal immutable Phase 1 ingestion and mapping authority before Phase 2 can read them. Market, universe eligibility, sector/industry classification, and accounting availability timestamps must be no later than the computation cutoff. Canonical security IDs use the Phase 1 `sec_<32 hex>` form.

Market inputs explicitly declare total-return and split-adjusted-price semantics. Accounting inputs must exactly cover the version-1 USD field contract. Missing required inputs fail; unavailable point-in-time values remain null.

## Publication and recovery

The publication identity hashes sorted parents, canonical inputs, factor version, and configuration hash. A publication contains factor characteristics, next-period factor-quantile returns, a configuration snapshot, validation report, diagnostics, lineage, manifest, and final publication envelope. All paths are project-relative and all material artifacts are checksum-bound. Reads authenticate the complete evidence graph. An identical rerun returns the authenticated existing publication; a conflicting artifact or changed evidence fails closed. Incomplete crash remnants have no publication envelope and are not discoverable as authenticated output.

## Configuration

`config/factors.yaml` owns windows, annualization, NYSE breakpoint quantiles, preprocessing, optional point-in-time sector/industry neutralization, and publication paths. Snapshots are immutable. Open governance choices remain open; configurable implementation defaults are not relabeled as owner-approved policy.

## Extension boundary

New characteristics require a versioned `FactorDefinition`, computation, validation rules, tests, and documentation. New source fields require a new input-contract version. Phase 3 consumes only authenticated Phase 2 publications and must not reach into temporary frames or recalculate factors.
