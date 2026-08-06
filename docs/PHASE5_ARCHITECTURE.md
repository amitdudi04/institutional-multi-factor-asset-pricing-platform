# Phase 5 Machine-Learning Architecture

## Trust boundary

Phase 5 starts with authenticated Phase 2 and Phase 3 publication IDs. `MLResearchService` authenticates both manifests, verifies their parent hash connection, and reads tables only through `FactorRepository` and `AssetPricingRepository`. Its institutional entry point does not accept caller-supplied DataFrames or arbitrary artifact paths.

```text
authenticated Phase 2 + connected Phase 3
  -> point-in-time feature and target contracts
  -> purged/embargoed temporal assignments
  -> training-only preprocessor
  -> baseline/linear/forest/XGBoost model
  -> held-out predictions, metrics, explanations, drift
  -> optional Phase 4 economic evaluation
  -> immutable artifact bundle, manifest, publication authority
  -> checksum-authenticated research reads
```

## Components

| Component | Responsibility |
|---|---|
| `ml.config` | Strict configuration; empirical target/horizon and input IDs remain unset until explicitly supplied |
| `ml.contracts` | Feature, target, split, prediction, explanation, and model-card identities |
| `ml.features`, `ml.targets` | Point-in-time dataset construction and exclusion reporting |
| `ml.splits`, `ml.preprocessing` | Purging, embargo, rolling/expanding/holdout assignments, training-only fitted state |
| `ml.models`, `ml.validation` | Baselines, regularized linear models, forests, XGBoost, tuning, calibration, SHAP, drift |
| `ml.evaluation`, `ml.economic` | Predictive/rank/calibration metrics and delegation to Phase 4 accounting |
| `ml.publication`, `ml.service` | Complete-bundle publication, lineage binding, authenticated restart and trusted-local loading |

Core ML code imports no API, dashboard, deployment, cloud, or Phase 6 library.

## Fail-closed publication

The manifest requires an exact artifact inventory. Every artifact records its checksum, byte size, media type, and Parquet column order. Publication authority binds model, preprocessor, feature schema, target, source manifests, configuration, Git commit, dependencies, and seed. Restart compares caller-produced artifact checksums with the authenticated existing bundle. Joblib loading occurs only after checksum authentication and is restricted to owner-generated local artifacts because Joblib/Pickle can execute code.
