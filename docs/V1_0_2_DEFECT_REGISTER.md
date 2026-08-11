# V1.0.2 Defect Register

This register supplements, but does not rewrite, the historical v1.0.0/v1.0.1 defect registers.

| ID | Severity | Evidence/root cause | Remediation and regression evidence | Final status | Merge blocking |
|---|---|---|---|---|---|
| FC-M01 | Medium | The post-remediation matrix retained 52 stale or insufficiently connected warning claims, making readiness counts unreliable. | Re-executed the supported boundaries, classified all 56 warnings, retained only four justified warnings, and regenerated all 465 rows plus this assurance capability. | CLOSED | No |
| FC-H01 | High | On Windows, path-based PyArrow verification could retain a temporary Parquet handle until atomic replacement, causing `WinError 32`. | Verification now uses an explicitly scoped binary stream and releases the table before replacement; connected Phase 1 publication passed repeatedly. | CLOSED | No |
| FC-H02 | High | Maximum-Sharpe SLSQP could fail at a legitimate long-only boundary start even when the feasible tangency portfolio existed. | Added the convex long-only tangency transformation for its valid constraint domain and deterministic bounded retries elsewhere; the service method matrix and full suite pass. | CLOSED | No |
| FC-M02 | Medium | The custom-model factory existed, but the authenticated Phase 3 application service could not accept, identity-bind, publish, restart, and authenticate a custom specification. | Added strict dependent-variable/frequency/unit contracts, collision rejection, specification-bound identity, publication metadata, and connected regression coverage. | CLOSED | No |
| FC-H03 | High | `build-ml-dataset` loaded no portfolio configuration and attempted to serialize a Pydantic target specification with plain `json.dumps`, crashing the supported CLI. | Load the governed portfolio configuration and serialize approved models/paths/dates explicitly; real connected CLI execution passes. | CLOSED | No |
| FC-H04 | High | Phase 6 report verification authenticated the output and source publications but accepted a mutated report manifest, allowing disclosures or other manifest-only evidence to change. | Verification now enforces the exact manifest schema, deterministic report identity, filename, template/software/config identity, generation time, limitations and disclaimer; a direct manifest-mutation regression fails closed. | CLOSED | No |
| FC-L01 | Low | The release version assertion still expected 1.0.1 after the 1.0.2 metadata update. | Updated the assertion; targeted and complete 254-test runs pass. | CLOSED | No |
| FP-L01 | Low | Upstream Starlette TestClient deprecation. | No compatible migration forced into this corrective release. | OPEN — NON-BLOCKING UPSTREAM WARNING | No |
| FP-L02 | Low | Host-local stale NumPy dist-info metadata. | Locked/imported NumPy 2.2.6 is restored by `uv`; no repository workaround. | OPEN — LOCAL WARNING | No |
| EXT-L01 | Low external | Lawful effective-dated Yahoo universe/mapping unavailable. | Owner/lawful input required. | OPEN — EXTERNAL INPUT | No |
| EXT-L02 | Low external | Real SEC contact identity unavailable. | Owner identity required if SEC is used. | OPEN — EXTERNAL IDENTITY | No |
| EXT-L03 | Low external | Owner empirical market/fundamental evidence unavailable. | Exact Phase 7 contracts required. | OPEN — EXTERNAL INPUT | No |
| EXT-L04 | Low external | Docker executable and Compose plugin unavailable on the host. | Host runtime required. | OPEN — EXTERNAL INFRASTRUCTURE | No |
| EXT-L05 | Low external | GitHub Actions jobs are prevented from starting by an account billing lock. | Owner must resolve GitHub account state. | OPEN — EXTERNAL INFRASTRUCTURE | No |

## Counts

- Open Critical software defects: **0**
- Open High software defects: **0**
- Open Medium merge blockers: **0**
- New v1.0.2 software/assurance defects closed: **7**
- Open non-blocking software warnings: **2 Low**
- External limitations/blockers: **5**
