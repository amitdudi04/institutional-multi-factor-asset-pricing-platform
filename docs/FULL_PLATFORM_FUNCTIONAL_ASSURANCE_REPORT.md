# Full Platform Functional Assurance Report

Audit date: 2026-08-10
Starting research branch/commit: `research/v1-empirical-validation` / `d4849a2dca2d6d6229dc3bebb6e3bc05701b1d8e`
Audit branch: `audit/full-platform-functional-assurance`
Released main/origin/main/tag v1.0.0: `06ba307aa8eed92c17f1a3dfe91882f54b94fbdc`

All temporary inputs and outputs in this report are **SYNTHETIC SOFTWARE FUNCTIONAL EVIDENCE — NOT EMPIRICAL RESEARCH**.

## A. Executive Summary

The platform has strong authenticated storage, numerical primitives, fail-closed publication repositories, delivery security, and test discipline. The audit independently produced two authentic Phase 1 owner-input publications, a 48-factor Phase 2 publication, delivered that evidence through the API, and generated/re-authenticated Markdown, HTML, JSON and CSV reports.

The complete supported pipeline does not work. Phase 3 rejects the authentic Phase 2 schema because `MOM` is configured as `momentum_12_1` while Phase 2 publishes `momentum_12_1m`. This is a High-severity bridge defect and stops the unbypassed chain. Independent Phase 5 source/formula review found additional High defects: application targets are sourced from market-wide factor values rather than security returns, risk targets are financially misdefined, multi-fold validation evaluates only one fold, and Phase 4 economic evaluation is a placeholder. Prior fixture-based tests do not expose these connected defects.

| Phase | Functional | Produces Output | Authenticated | Restart Safe | End-to-End Connected | Live Empirical Status | Overall |
|---|---|---|---|---|---|---|---|
| Phase 1 | PASS | PASS | PASS | PASS | PASS to Phase 2 | FRED/French live pass; equity inputs blocked | PASS WITH EXTERNAL INPUT BLOCKERS |
| Phase 2 | PASS | PASS | PASS | PASS | FAIL to Phase 3 | No lawful equity input | FAIL — bridge defect |
| Phase 3 | PASS in isolation | PASS in isolation | PASS in isolation | PASS in isolation | FAIL | Externally blocked and software blocked | FAIL |
| Phase 4 | PASS in isolation | PASS in isolation | PASS in isolation | PASS in isolation | FAIL | Upstream blocked | PASS WITH WARNING / scenario service fail |
| Phase 5 | Primitive tests pass | Publication fixture only | PASS in isolation | PASS in isolation | FAIL | Upstream blocked | FAIL — target/workflow defects |
| Phase 6 | PASS | PASS for Phase 2 | PASS | PASS | FAIL for full chain | Empty/live equity state supported | PASS WITH DOWNSTREAM WARNING |

## B. Repository and Git State

The audit began clean at the required research commit and created the required audit branch. `main`, `origin/main`, and `v1.0.0` resolve to `06ba307aa8eed92c17f1a3dfe91882f54b94fbdc`; the research/audit commit descends from it. Milestone history and historical reports remain present. `git fsck` reported only unreachable/dangling objects, not repository corruption. No history was rewritten and main was not changed.

## C. Baseline Quality Gates

| Gate | Result |
|---|---|
| Tests | 224 passed; 0 failed; 0 skipped; 0 xfailed |
| Branch-aware coverage | 90.49% |
| Ruff | clean |
| Ruff format | 181 files already formatted |
| Strict Mypy | success across 105 source files |
| Lock | valid; 96 resolved packages |
| Alternate hash seed | 120 focused Phase 1–6 tests passed with `PYTHONHASHSEED=777` |
| Warning | one upstream Starlette TestClient deprecation warning |

Commands executed:

- `git status --short --branch`; branch/hash/tag/log/fsck verification
- `uv sync --all-groups`
- `uv run pytest`; `uv run coverage report`
- `uv run ruff check .`; `uv run ruff format --check .`; `uv run mypy src`; `uv lock --check`
- all 38 CLI commands with `--help`, plus safe config/list/verification paths and invalid-input probes
- direct authenticated Phase 1→2→3 temporary pipeline
- live bounded FRED DGS3MO and Kenneth French adapter probes
- FastAPI TestClient actual Phase 2 delivery, bearer/path/pagination probes, and four report formats
- `PYTHONHASHSEED=777` focused Phase 1–6 suite
- `uvx pip-audit` against a frozen production export
- repository-wide AST/TOML/link/mojibake/secret/generated-artifact/large-file scans
- Docker and GitHub CLI availability checks

## D. Phase 1 Functional Assessment

Configuration, all eight contracts, synthetic adapter behavior, immutable raw/standardized storage, validation/quarantine, security mapping, lifecycle authentication, crash recovery, catalog rebuild and authenticated research reads passed their executed tests. The connected probe published `factor_market_input-e4fbcea447b4182d030c4b73` (24 rows, PASS, PUBLISHED) and `factor_fundamental_input-bc48c854481811d54cb9ba34` (57 rows, PASS, PUBLISHED), then retrieved both through `ResearchDatasetRepository` after publication.

Live FRED DGS3MO returned header `observation_date,DGS3MO`, 88 bytes and four rows for 2026-08-03 through 2026-08-06. Both `DATE` and `observation_date` paths and malformed responses pass tests. Kenneth French live retrieval also succeeded: 149,894 bytes and 95,124 standardized factor rows. Yahoo live equity research is blocked by missing lawful universe/mapping; SEC is blocked by missing owner contact identity; owner input is blocked by absent lawful files. These are external, not adapter software failures.

## E. Phase 2 Functional Assessment

Code and authenticated output independently confirm exactly 48 factors across market, size, value, momentum, quality, investment, leverage/risk, low-volatility and liquidity families. All seven preprocessing modes and temporal attacks execute/reject as designed. The connected publication `factor-1950aba1deb9d8643ed8bf7262b97d6a` contains 1,104 factor rows, 48 factor IDs, authenticated parents, diagnostics and portfolio output. Restart authentication returned `PASS_WITH_WARNINGS`, appropriate for the tiny three-security audit cross-section.

## F. Phase 3 Functional Assessment

CAPM, Fama-French 3, Carhart 4, Fama-French 5, Hou-Xue-Zhang q and the custom framework; OLS, WLS, rolling, expanding, panel and Fama-MacBeth estimators; classical/HC0–HC3/HAC inference; and the documented diagnostics pass direct numerical tests. Publication restart/tamper tests also pass against a Phase 2-shaped fixture.

Connected execution fails. Even a CAPM request calls `build_research_panel` with every mapping and raises `DataQualityError: Mapped Phase 2 factor is unavailable: MOM=momentum_12_1`. No supported Phase 3 publication ID exists for the connected run.

## G. Phase 4 Functional Assessment

Equal/market-cap weighting, seven constrained optimizers, Black-Litterman/Bayesian posteriors, four covariance paths, nine constraint families, exact costs, multi-period drift/accounting, 19 risk measures and six scenario types all produce direct synthetic results or explicit rejections in the executed suite. Component risk reconciliation and gross/net/benchmark identities pass.

The publication service passes restart/tamper tests with connected-shaped fake repositories but cannot be reached from the actual Phase 2 evidence because Phase 3 fails. Separately, the application service always publishes `FRAMEWORK_AVAILABLE_NOT_RUN` with no scenarios, despite the scenario primitive being functional.

## H. Phase 5 Functional Assessment

All ten implemented model families/variants, temporal split primitives, training-only preprocessing, predictive/classification/ranking metrics, calibration primitives, explanation primitives, drift and immutable bundle authentication pass direct tests.

The application workflow is not functionally equivalent to those primitives. It uses Phase 2 `excess_return`—a market-wide value with one unique value per date in the real factor output—as a security target source; volatility targets use `rolling_volatility` as though it were a return series. Benchmark-relative targets are deliberately mapped to `future_return`. Downside volatility, drawdown and risk-quantile branches compute different quantities from their names. Only `folds[-1]` is evaluated. Search, sigmoid/isotonic calibration, permutation/SHAP service output, challenger/stability comparison, complete model cards and Phase 4 economic evaluation are placeholders or omitted. No connected Phase 5 publication was fabricated.

## I. Phase 6 Functional Assessment

The application registers 42 routes including OpenAPI: 40 GET routes, one POST report route, and the GET/HEAD OpenAPI route. Actual authenticated Phase 2 discovery, manifest, definitions and observation endpoints returned 200; `/health`, `/ready`, and `/version` returned 200. Required-auth probes returned 401 for missing/wrong tokens and 200 for a valid token. Traversal returned 404 and oversized pagination 422. Security headers, correlation IDs, throttling, request limits, trusted hosts, CORS and error redaction pass tests.

The nine dashboard pages are registered and their empty-state/presentation transformations pass without duplicated analytics. No screenshot is claimed. Downstream pages were only exercised with authenticated fixtures because no connected Phase 3–5 publication exists.

## J. CLI Assessment

All 38 registered commands are listed separately in the capability matrix and all `--help` calls exited successfully. Configuration, storage, catalog, list, verification, FRED and delivery paths produced valid results; invalid identifiers/paths fail closed. Asset-pricing and downstream analytical commands cannot complete through the supported chain because of the Phase 2→3 defect. SEC/owner live ingestion remains externally blocked.

## K. API Assessment

Every route is listed separately in the matrix. Stable schemas/pagination, authenticated lookup, lineage/artifact inventory, typed family endpoints and deterministic report endpoints pass executed TestClient coverage. Actual synthetic evidence was delivered for Phase 2; downstream route contracts used authenticated catalog fixtures and are marked with warning rather than represented as end-to-end proof.

## L. Dashboard Assessment

Nine pages exist: Platform Overview, Data and Lineage Explorer, Factor Research, Asset-Pricing Research, Portfolio Construction, Risk Analytics, Machine Learning, Validation and Audit, and Report Builder. Page registration, provenance formatting, chart-data bounding, empty state, invalid evidence and report-builder handling pass. No dashboard analytical recomputation was found.

## M. Reporting Assessment

Actual reports bound to `factor-1950aba1deb9d8643ed8bf7262b97d6a` were generated and reauthenticated: Markdown `report-3d57cedd01dca3f10de1bbee7eb4a867`, HTML `report-dd6198dabe1f02936a578fa89b254ac5`, JSON `report-3742b6ceae8756a839935e138ed53263`, and CSV `report-8e385f5ea30ad5248135faef3cea9ff7`. Deterministic IDs, safe filenames, path confinement, source checksums, limitations and disclaimer pass. Mutation/security tests fail closed.

## N. Docker Assessment

Static Docker/Compose assurance passes: multi-stage frozen build, non-root runtime, loopback ports, read-only containers, dropped capabilities, no-new-privileges, bounded volumes, and `.dockerignore` exclusion of Git, data, secrets, models, tests and docs. Docker is not installed on this host, so build/Compose runtime status is `BLOCKED — EXTERNAL INFRASTRUCTURE`, not PASS.

## O. CI Assessment

The workflow statically includes frozen sync/lock, tests, 90% coverage, Ruff lint/format, Mypy, imports, delivery validation/readiness, dependency audit and Docker build with read-only permissions. GitHub CLI is unavailable; remote run status is `UNVERIFIED`.

## P. Dependency and Security Assessment

Package version is 1.0.0 with one description, 19 unique direct dependencies, valid TOML, no duplicate dependency declarations and two non-duplicate Mypy override blocks. A frozen production export audited 78 resolved environment packages and found no known vulnerabilities. Direct dependency metadata showed permissive/common scientific-stack licensing and no identified conflict; some wheel metadata uses classifiers/files rather than a concise license field. Repository scanning read 195 scoped text files, AST-parsed 122 Python files, found no broken local Markdown links, no confirmed mojibake, secrets, private keys, credentials, tracked datasets, Parquet/DuckDB/model binaries, caches, logs or >1 MB tracked files. `.env.example` is the expected non-secret template.

## Q. End-to-End Synthetic Pipeline

The unbypassed connected result is:

`factor_market_input-e4fbcea447b4182d030c4b73` + `factor_fundamental_input-bc48c854481811d54cb9ba34` → `factor-1950aba1deb9d8643ed8bf7262b97d6a` → **FAIL before Phase 3 publication**.

Because supported Phase 3 failed, the audit did not inject final artifacts into Phase 4/5 or claim a Phase 6 full-chain result. This correctly distinguishes a software bridge defect from missing live equity data.

## R. Lineage Continuity

Phase 1→2 lineage, hashes and restart authentication pass. Phase 2→3 is disconnected by FP-H01. Therefore Phase 6 cannot trace a delivered Phase 5 result backward through Phase 4/3/2/1. The disconnected link is High severity.

## S. Restart and Recovery

Phase 1 and Phase 2 connected evidence reauthenticated after repository reconstruction. Isolated Phase 3–5 publication repositories pass restart tests. Reports reauthenticated. A complete connected restart could not be executed beyond Phase 2 and is FAIL, not external-blocked.

## T. Determinism

Idempotent Phase 1/2 publication and isolated Phase 3–5 publication tests pass. The focused Phase 1–6 suite passed under `PYTHONHASHSEED=777`. Complete-pipeline determinism is not obtainable because the first run fails at Phase 3.

## U. Tamper Resistance

Independent tests mutate bound Phase 1 manifests/config/validation/lineage/artifacts/lifecycle, Phase 2 factors, isolated Phase 3 coefficients, Phase 4 returns, Phase 5 model/predictions/explanations and report sources; supported reads fail closed. No bypass was found. Cross-phase downstream tamper propagation cannot be proven past the disconnected bridge.

## V. Documentation Truthfulness

Active documentation is materially optimistic. README and roadmap call all phases implemented/assured; Phase 5 docs claim integrated tuning, calibration, permutation/SHAP, model cards and economic evaluation that the service replaces with partial output/placeholders. Phase 3 methodology/config use the wrong momentum identifier while Phase 2 methodology correctly documents `momentum_12_1m`. Historical reports were not changed.

## W. Live Empirical Readiness

Software adapters: FRED and Kenneth French live paths currently work; all five adapters pass synthetic contract tests. Live equity study: blocked by missing lawful historical universe/mapping, owner market/fundamental evidence, and SEC contact identity. Independently, software defects would still stop the supported chain even if those inputs arrived.

## X. External Blockers

- Missing lawful Yahoo equity universe and effective-dated mapping authority.
- Missing owner-supplied market/fundamental evidence and metadata.
- Missing real SEC contact identity.
- Docker engine unavailable locally.
- GitHub CLI/authenticated remote CI inspection unavailable locally.

Kenneth French DNS is no longer a current blocker; the bounded live retry succeeded.

## Y. Defect Summary

- Critical: **0**
- High: **5**
- Medium: **7**
- Low: **7**
- External blockers: **5**

High findings are the Phase 2→3 identifier bridge, Phase 5 target identity, incorrect risk-target semantics, single-fold application evaluation, and missing Phase 4 economic integration. The complete register is `docs/FULL_PLATFORM_DEFECT_REGISTER.md`.

## Z. Capability Summary

Total capabilities audited: **465**

- PASS: **375**
- PASS WITH WARNING: **56**
- FAIL: **27**
- BLOCKED — EXTERNAL INPUT: **5**
- BLOCKED — EXTERNAL INFRASTRUCTURE: **1**
- NOT APPLICABLE: **0**
- NOT IMPLEMENTED: **0**
- UNVERIFIED: **1**

The detailed per-capability evidence is in `docs/FULL_PLATFORM_CAPABILITY_MATRIX.md`.

## AA. Overall Platform Readiness

Phase 1, Phase 2, analytical primitives and delivery controls are structurally strong. The released platform is not end-to-end operational through supported interfaces and must not be represented as fully assured. The defects are bounded and remediable, but several can materially mislabel financial ML outputs.

## AB. Recommended Next Actions

1. Correct the governed Phase 2→3 identifier mapping and add a real authenticated bridge regression test.
2. Redesign Phase 5 target input binding around authenticated security returns; correct each target formula with hand-calculable tests.
3. Execute all temporal folds and bind tuning, calibration, explanation, challenger, model-card and economic-evaluation evidence in the application publication.
4. Integrate explicit scenario execution into Phase 4 publication.
5. Re-run this audit from clean inputs, then update active documentation while preserving historical reports.

## AC. Final Verdict

FULL PLATFORM FUNCTIONAL ASSURANCE FAILED — MATERIAL SYSTEM DEFECTS REMAIN
