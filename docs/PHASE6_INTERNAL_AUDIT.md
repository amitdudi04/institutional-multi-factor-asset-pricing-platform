# Phase 6 Independent Internal Audit

## Method

The audit attempted authentication bypass, anonymous non-loopback binding, wildcard CORS, untrusted hosts, oversized bodies, excessive pagination, malformed IDs, path traversal, arbitrary API/dashboard paths, report traversal and injection, publication/artifact substitution, restart collision, error/secret leakage, unsafe model access, Docker boundary weakening, CI omission, and vulnerable dependency retention.

## Findings

| ID | Severity | Evidence and root cause | Remediation | Final status |
|---|---|---|---|---|
| P6-AUD-H01 | High | A CLI-selected container configuration was validated by the launcher but was not guaranteed to reach the module-global FastAPI factory imported by Uvicorn. | The CLI now exports the resolved delivery-config identity before Uvicorn imports the application; regression and Compose checks added. | CLOSED |
| P6-AUD-H02 | High | Initial report restart used a new wall-clock timestamp, and read verification compared configuration identity without the full artifact inventory. | Generation time is deterministic from source evidence; restart is byte-stable; Git and exact artifact checksums are reauthenticated at every read. | CLOSED |
| P6-AUD-H03 | High | Installed-environment audit found `PYSEC-2026-113` in PyArrow 21.0.0 and `PYSEC-2026-1845` in pytest 8.4.2. | Upgraded to PyArrow 23.0.1 and pytest 9.1.1; repeated audit found no known vulnerabilities. | CLOSED |
| P6-AUD-M01 | Medium | Plotly rejected the initial unsupported `animations` layout key. | Removed the invalid property and added chart smoke coverage. | CLOSED |
| P6-AUD-M02 | Medium | Initial Phase 1 discovery labeled catalog `dataset_type` as `schema_version`. | Discovery now authenticates each handle and reports its actual schema, validation, configuration, and Git identities. | CLOSED |
| P6-AUD-M03 | Medium | Initial factor diagnostics routing used a generic document reader that deliberately rejected factor storage. | Added checksum-verified reads for authenticated factor diagnostics, validation, configuration, and lineage documents. | CLOSED |
| P6-AUD-M04 | Medium | Framework request-validation responses could expose inconsistent detailed envelopes. | Added a redacted uniform request-validation handler and regression assertion. | CLOSED |
| P6-AUD-L01 | Low | Docker executable is unavailable on the audit host. | Static validation passed and CI performs an actual image build. | OPEN - NON-BLOCKING |
| P6-AUD-L02 | Low | Ignored local environment reports stale NumPy metadata while resolving the locked version. | Disclosed as local environment noise; no stale package is tracked. | OPEN - NON-BLOCKING |
| P6-AUD-L03 | Low | FastAPI's supported test client emits an upstream transition deprecation warning. | Tests remain supported and passing; monitor upstream migration. | OPEN - NON-BLOCKING |

No Critical finding was discovered. No High finding remains open. No merge blocker remains.
