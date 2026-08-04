# Phase 3 Asset-Pricing Architecture

## Boundary and flow

The application service accepts a Phase 2 publication identifier, not data frames or file paths. `FactorRepository` authenticates the Phase 2 publication pointer, manifest, characteristic table, quantile-portfolio table, configuration, validation, diagnostics, and lineage before any estimation. The research-panel builder then enforces date and availability alignment, reconciles market excess and risk-free values across securities, constructs explicitly mapped project-factor spreads, and computes portfolio excess returns.

```text
authenticated Phase 2 publication
  -> exact-date and availability validation
  -> test-asset excess returns + configured factor-return matrix
  -> rank/covariance/missingness/observation validation
  -> model estimator + robust inference
  -> residual, assumption, influence, and stability diagnostics
  -> immutable Parquet/JSON artifacts
  -> checksum-bound manifest and publication pointer
  -> authenticated read repository
```

## Package responsibilities

| Package | Responsibility |
|---|---|
| `asset_pricing` | Model registry, strict configuration, authenticated input construction, orchestration |
| `regression` | OLS, WLS, rolling, expanding, pooled/fixed-effect panel, Fama-MacBeth |
| `model_validation` | Missingness, finite values, constants, rank, covariance, observations |
| `statistical_tests` | Normality, heteroskedasticity, autocorrelation, stationarity, intervals |
| `diagnostics` | Residual, VIF, covariance, leverage, Cook's distance |
| `research_outputs` | Immutable persistence, evidence models, schema/checksum authentication |
| `cli` | Explicit configuration, compute, list, and verify commands |

The estimator layer can be tested independently with in-memory isolated fixtures. Only the application service is authorized to create institutional research publications, and it can obtain inputs only through the authenticated Phase 2 repository.

## Failure and recovery model

Missing model mappings, conflicting common-factor observations, unavailable dates, non-finite values, zero variance, rank deficiency, insufficient observations, invalid weights, excessive HAC lags, and malformed evidence raise explicit platform errors. No factor or estimator fallback exists. Artifact files are content-checked and immutable; conflicting reuse fails. The manifest directory becomes visible atomically only after all evidence is staged. An interrupted pre-activation run may leave an ignored unreferenced artifact, but supported listing and reads cannot see it. A deterministic restart reuses identical bytes or rejects a collision.

## Extension points

New custom model specifications require explicit unique factors and external configuration mapping. New approved models require registry equations, configuration, numerical tests, diagnostics, methodology, and contract review. Future APIs and dashboards must call the service/repository and may not recalculate models. Optimization and backtesting remain absent.
