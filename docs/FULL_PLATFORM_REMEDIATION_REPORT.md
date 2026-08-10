# Full Platform Remediation Report

## Scope and baseline

Remediation branch: `remediation/full-platform-functional-repair`

Authoritative failed audit: `docs/FULL_PLATFORM_FUNCTIONAL_ASSURANCE_REPORT.md` at audit commit `ac052e718ab409c8f29a8deea791d2c54979bec9`. That report, its original defect register, and its 465-capability matrix remain unchanged historical evidence. No live dataset or empirical result was produced.

## Original software findings

| ID | Original severity | Original evidence and confirmed root cause | Files changed | Remediation | Regression and connected proof | Final status |
|---|---|---|---|---|---|---|
| FP-H01 | High | Phase 2 published `momentum_12_1m`; Phase 3 configured `momentum_12_1` and resolved every mapping even for CAPM. | `config/asset_pricing.yaml`; `asset_pricing/service.py`; `asset_pricing/inputs.py` | Corrected the governed identifier and restricted mapping resolution to factors used by selected models; empty mapped-factor sets are supported for CAPM. | Phase 3 mapping regression plus authentic Phase 1→2→3 CAPM publication in `test_full_platform_connected.py`. | CLOSED |
| FP-H02 | High | The ML service sourced labels from Phase 2 market-wide factor observations instead of security returns. | `ml/service.py`; `ml/targets.py`; `ml/contracts.py`; CLI | Resolves the unique Phase 1 market parent bound in the authenticated Phase 2 manifest; verifies parent checksum and decimal-return units; persists target-source identity. | Security targets vary cross-sectionally; source/checksum assertions; authentic connected Phase 5 publication. | CLOSED |
| FP-H03 | High | Downside volatility, drawdown, and risk quantile reused unrelated standard-deviation/return logic. | `ml/targets.py`; `ml/config.py`; `ml/contracts.py` | Added explicit compounded-return, annualized sample/downside deviation, cumulative-wealth maximum drawdown, and positive-loss historical quantile formulas with recorded conventions. | Hand-calculated path tests for every risk target and invalid-convention guards. | CLOSED |
| FP-H04 | High | The service evaluated only `folds[-1]`; `retrain_every` was unused. | `ml/service.py`; `ml/contracts.py` | Executes every fold, records all assignments/predictions/metrics and actual model-training intervals, and applies deterministic retraining/reuse cadence. | Expanding publication fold-count assertions; rolling multi-fold/retrain-cadence regression; connected holdout publication. | CLOSED |
| FP-H05 | High | Economic evaluation was placeholder JSON and had no Phase 4 repository or parent. | `ml/service.py`; CLI | Requires an authenticated Phase 4 parent with matching Phase 2/3 hashes, reads its bound costs, and delegates fold-level long-only evaluation to the Phase 4 engine with cost/return reconciliation. | Dedicated Phase 5→4 test plus authentic connected Phase 4→5 publication. | CLOSED |
| FP-M01 | Medium | Phase 4 always published an empty `FRAMEWORK_AVAILABLE_NOT_RUN` scenario report. | `portfolio/service.py` | Added explicit scenario requests, publication-identity binding, authenticated factor-portfolio exposure mapping, impact/contribution output, and unmapped-shock limitations. | All supported scenario kinds executed; no-request and partial-mapping states asserted; connected value stress published. | CLOSED |
| FP-M02 | Medium | Validation arrays were unused and the trials artifact was empty. | `ml/config.py`; `config/machine_learning.yaml`; `ml/service.py` | Added bounded configured search spaces and per-fold trial parameters, metric, failure, duration bucket, and selected-model evidence using train/validation only. | Search primitive isolation tests and service artifact assertions. | CLOSED |
| FP-M03 | Medium | Calibration configuration did not affect probabilities. | `ml/service.py` | Applies sigmoid or isotonic calibration only after validation and before test, with period and calibrator identity evidence. | Primitive sigmoid/isotonic tests and classification service calibration publication. | CLOSED |
| FP-M04 | Medium | Tree publications emitted only native importance. | `ml/service.py`; `ml/validation.py` | Publishes permutation and bounded local SHAP evidence using training-only backgrounds, bound to model, preprocessing, feature/prediction artifact, background, config, seed, dependency, and Git identities. | Tree service publication asserts both methods and identity hashes; future-background attack still fails. | CLOSED |
| FP-M05 | Medium | Model card contained only status, horizon, and limitations. | `ml/contracts.py`; `ml/service.py` | Constructs the strict `ModelCard` with source/target identity, all fold intervals, features, preprocessing, search rationale, metrics, economic/explanation/drift evidence, limitations, dependencies, checksums, config, Git, and status. | Service restart test validates mandatory card sections and authenticated target source. | CLOSED |
| FP-M06 | Medium | Challenger, ablation, and stability output was a placeholder. | `ml/service.py`; `ml/evaluation.py` | Runs configured baselines/challengers and feature-family ablations on each test fold; publishes block-bootstrap IC and fold-metric stability. | Comparison artifact generated on all service regressions; unit tests cover bootstrap/ablation guards. | CLOSED |
| FP-M07 | Medium | Active documents overstated capabilities and repeated the bad momentum identifier. | README; specification; roadmap; data/Phase 3/5 methodology documents; changelog | Corrected operational descriptions only after the connected suite passed; retained failed historical audit and reports. | Documentation/link/UTF-8 consistency gates and Git history review. | CLOSED |

## Additional defects exposed by the connected repair

| ID | Severity | Evidence/root cause | Remediation | Proof | Status |
|---|---|---|---|---|---|
| FP-H06 | High | Authentic Phase 2→4 execution rejected benchmark values differing only by floating-point aggregation roundoff because it required bitwise equality. | Accepts at most `1e-12` within-date spread and reconciles by mean; material discrepancies still fail closed. | Dedicated roundoff/material-conflict regression and successful authentic Phase 1→6 test. | CLOSED |
| FP-M08 | Medium | `DeliveryCatalog(root)` constructed Phase 1 access at the process project root rather than its supplied root, breaking isolated restart/catalog assurance. | Passes the catalog root into `DataIngestionService`. | Connected restart discovers both Phase 1 datasets and all Phase 2–5 publications. | CLOSED |

## Validation result

The remediation broad gate completed 233 tests with 90.51% branch-aware coverage. The authentic synthetic chain created real Phase 1 market/fundamental datasets, Phase 2 factors, Phase 3 CAPM evidence, Phase 4 scenario/economic parent evidence, Phase 5 ML evidence, and Phase 6 API/report delivery; restart authentication and Phase 1 parent tampering were tested. Synthetic evidence proves software behavior only.

All original Critical/High/Medium software findings are closed. FP-L01 and FP-L02 remain non-blocking dependency/host warnings. Lawful live-data and external infrastructure blockers remain separate.
