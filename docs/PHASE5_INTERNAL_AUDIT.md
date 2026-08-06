# Phase 5 Independent Internal Audit

## Method

The audit traced authenticated source IDs through lineage connection, feature availability, target windows, split assignment, preprocessing fit scope, model fitting, held-out prediction, explanation background, economic evaluation, staging, activation, restart, and read-time checksum validation. Independent substitutions and temporal bypasses were attempted rather than inferred from test names.

## Findings

| ID | Severity | Evidence and root cause | Impact | Remediation | Final status |
|---|---|---|---|---|---|
| P5-AUD-H01 | High | A first restart probe regenerated `created_at`, producing different manifest bytes for the same deterministic run identity. | Restart could conflict instead of authenticating immutable prior evidence. | Existing authority is authenticated first and every supplied artifact checksum is compared before reuse; altered content is rejected. | CLOSED |
| P5-AUD-M01 | Medium | The initial calibration wrapper used scikit-learn's removed `cv="prefit"` interface. | Calibration failed under the locked current scikit-learn version. | Wrapped the already-fitted estimator with `FrozenEstimator`; temporal ordering remains enforced before calibration. | CLOSED |
| P5-AUD-M02 | Medium | Initial target-source validation did not reject missing identity/value cells before grouping. | A malformed target row could be silently excluded by downstream operations. | Required target identity/value fields now fail before construction; regression coverage added. | CLOSED |
| P5-AUD-M03 | Medium | Initial expanded suite measured 89.22% branch coverage. | The repository gate was not met. | Added direct fail-closed tests for previously unexercised temporal, identity, configuration, model, drift, explanation, and publication branches. The complete rerun passed 209 tests at 90.00% branch-aware coverage. | CLOSED |
| P5-AUD-L01 | Low | The ignored local `.venv` repeatedly reports stale NumPy 2.5.1 metadata while `uv` repairs execution to locked NumPy 2.2.6. | Local setup noise; tracked lock and executed environment remain pinned. | Reinstall/repair was performed; warning documented as an environment-only limitation. | OPEN — NON-BLOCKING |
| P5-AUD-L02 | Low | No authenticated empirical ML input was supplied. | Software cannot support an empirical incremental-value conclusion. | Status is explicitly `LIVE EMPIRICAL ML VALIDATION PENDING`; no result was fabricated. | OPEN — NON-BLOCKING |

No Critical finding was discovered. No High finding remains open. Historical Phase 1–4 reports were not modified.
