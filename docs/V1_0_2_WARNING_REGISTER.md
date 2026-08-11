# V1.0.2 Warning Register

SYNTHETIC SOFTWARE FUNCTIONAL EVIDENCE — NOT EMPIRICAL RESEARCH

## Historical capability-warning reconciliation

All 56 v1.0.1 `PASS WITH WARNING` rows were classified before the v1.0.2 matrix was regenerated.

| Category | Prior capability IDs | Count | v1.0.2 disposition |
|---|---|---:|---|
| A — legitimate design/scope warning | P4-OPT-02, P4-OPT-10, P4-OPT-11 | 3 | Retained. These are authenticated domain primitives, not application optimizer methods. |
| B — synthetic-data limitation | P2-E2E-01 | 1 | Retained. Software completeness is demonstrated; empirical fitness is not claimed. |
| C — external input limitation | None among the 56 warnings | 0 | External-input capabilities remain separately blocked, not warnings. |
| D — external infrastructure limitation | None among the 56 warnings | 0 | Docker and remote CI remain separately blocked. |
| E — stale pre-remediation evidence | P3-MOD-01–05, P3-PUB-01–07, P4-PUB-01–07, P5-TGT-01, P5-TGT-03–05, P5-SVC-07 | 29 | Removed after fresh connected service execution. |
| F — insufficient connected test evidence | P3-MOD-06, P6-API-12–13, P6-API-19–39, P6-UI-04–07 | 23 | Removed after fresh custom-model, API, and nine-page dashboard execution. |
| G — actual software defect | None classified directly from a historical warning | 0 | New defects exposed by execution are recorded separately in the defect register. |

Total: **56**.

## Final pytest warning inventory

The final complete run produced exactly 103 warnings.

| ID | Source and exact condition | Count | Category | Expected? | Software/financial/release impact | Action and final status |
|---|---|---:|---|---|---|---|
| W-PY-01 | `StarletteDeprecationWarning`: Starlette `TestClient` reports the current `httpx` integration is deprecated and recommends `httpx2`. | 1 | Upstream dependency | Yes | No runtime or financial effect; test client only. | FP-L01 remains open, non-blocking; migrate when the supported FastAPI/Starlette stack is compatible. |
| W-PY-02 | pandas `ConstantInputWarning`: Spearman correlation is undefined for constant synthetic fixture vectors. | 95 | Synthetic fixture limitation | Yes | Metrics correctly become unavailable; no empirical conclusion is drawn. | Retained and disclosed; do not distort fixtures merely to suppress a valid statistical warning. |
| W-PY-03 | The same SciPy/pandas `ConstantInputWarning` emitted at `ml/evaluation.py:155`, where the guarded project call records undefined correlation. | 5 | Project callsite / synthetic fixture | Yes | The application handles the undefined result; no silent numeric substitution. | Investigated, non-blocking, retained as explicit evidence of fail-transparent behavior. |
| W-PY-04 | scikit-learn warns that the least-populated synthetic calibration class has 4 observations versus 5 folds. | 1 | Synthetic fixture limitation | Yes | Calibration path still executes; not empirical calibration evidence. | Retained and disclosed. |
| W-PY-05 | scikit-learn warns that the least-populated synthetic calibration class has 3 observations versus 5 folds. | 1 | Synthetic fixture limitation | Yes | Same as W-PY-04. | Retained and disclosed. |

## Host/runtime warnings outside pytest

| ID | Source | Classification | Impact | Disposition |
|---|---|---|---|---|
| W-HOST-01 | `uv` repeatedly finds stale `.venv/Lib/site-packages/numpy-2.5.1.dist-info` without `RECORD`, then restores locked NumPy 2.2.6. | Host-local environment metadata | No tracked dependency mismatch; imports, tests, lock and audit pass. | FP-L02 remains open, local and non-blocking. No `.venv` workaround is committed. |
| W-GIT-01 | Git reports LF will be converted to CRLF on future Windows checkout operations. | Host line-ending policy | `git diff --check` passes; no content corruption. | Non-blocking informational warning. |

## Release conclusion

No unexplained runtime warning remains. None is Critical, High, financially material, or merge-blocking.
