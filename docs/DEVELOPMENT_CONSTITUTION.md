# Development Constitution

## Mission and standard

This repository will become an institutional-quality, research-driven platform for multi-factor asset pricing, portfolio analytics, risk attribution, explainable machine learning, and investment decision support. Financial and statistical correctness, data integrity, reproducibility, and research defensibility take priority over speed, feature count, appearance, or architectural novelty.

The controlling sequence is: research question; data provenance and integrity; financial theory; statistical methodology; validation and bias control; software architecture; reproducible outputs; visualization and deployment.

## Authority hierarchy

Implementation authority descends from: (1) explicit repository-owner instructions; (2) this constitution; (3) `docs/PROJECT_SPECIFICATION.md`; (4) phase specifications; (5) architecture and methodology documents; (6) configuration; and (7) documented code defaults. A lower authority may not silently override a higher one.

Data authority flows only downstream: immutable raw data; source manifests and checksums; validated standardized data; features and factors; model-ready data; model outputs; portfolio outputs; reports and interfaces. Downstream processes must not overwrite upstream sources or establish competing truth. UI and notebook layers may not independently reimplement core research logic.

## Data ownership and non-fabrication

Owner-supplied datasets are authoritative. Raw inputs are immutable by default; validation, cleaning, and transformation produce separate, versioned artifacts with lineage. Existing raw files must never be altered in place.

The project must never fabricate, infer merely for convenience, or present as empirical any financial observation, classification, identifier, assumption, factor, forecast, coefficient, diagnostic, portfolio weight, risk metric, performance series, chart, or conclusion. Missing required data causes a safe, actionable failure identifying the absent input, purpose, expected schema, and approved acquisition path. Workflows may not silently substitute values, benchmarks, securities, dates, or reduced universes.

Synthetic data is prohibited except when an owner-approved later task requires an isolated, clearly labeled software-test fixture. Such fixtures must remain outside research inputs and outputs and must never support investment claims.

Future approved adapters must record source identity, URL or identifier, retrieval time, universe and date request, raw response location, schema version, lineage, licensing limitations, failures, and partial retrievals. Free sources must not be described as equivalent to institutional licensed data.

## Research integrity and assumptions

Every model requires a defined research question, financial motivation, mathematical formulation, inputs, assumptions, estimation method, validation, interpretation, limitations, failure conditions, and comparison benchmark. Established theory, implementation choices, empirical extensions, exploratory work, and original contributions must be distinguished accurately.

Investment universe, benchmark, currencies, classifications, calendars, timestamps, prices, corporate actions, survivorship, missingness, outliers, return definitions, frequencies, windows, execution, costs, constraints, weighting, hyperparameters, seeds, and inference thresholds may not be assumed silently. Material assumptions must be explicit, configurable, documented, validated where possible, and attached to output metadata. Unresolved material choices belong in specifications or fail-fast configuration requirements.

## Configuration and secrets

Material settings belong in validated, structured configuration rather than paths, tickers, dates, parameters, or magic numbers embedded in code and notebooks. Configuration must use project-relative paths, explicit defaults, clear errors, deliberate environment-variable interpolation for secrets, and reproducibility snapshots. Duplicate configuration authorities are prohibited.

Secrets are never committed, logged, embedded in example files, or exposed in reports. `.env.example` may list empty documented variable names; populated `.env` files remain untracked. A discovered credential must not be used or repeated: identify only its location and variable, recommend rotation, and remediate without discarding user work.

## Reproducibility

Every empirical result must be reproducible from identified source data, configuration, code revision, environment, execution time, and deterministic seed where applicable. Pipelines must record code and configuration identity, dataset manifests or hashes, library versions, start/end times, status, warnings, and output locations. Hardware or library nondeterminism must be disclosed rather than overstating guarantees.

## Temporal integrity and bias control

Research must use point-in-time information where available and explicit observation, availability, decision, execution, and holding timestamps. It must prevent future-price use, future-informed normalization, selection or imputation, unjustified random time-series splits, same-period execution errors, future constituent leakage, and future covariance use.

Walk-forward or expanding-window validation is preferred. Specifications and tests must address look-ahead, survivorship, selection, data-snooping, multiple-testing, publication-lag, stale-data, delisting, benchmark-reconstitution, and transaction-cost biases. The relationship between information at time `t` and outcomes at `t+1` must be documented and tested.

## Architecture and engineering

Architecture must be layered, cohesive, explicitly dependent, testable, and reusable. Configuration, contracts, ingestion, validation, transformation, factors, asset pricing, machine learning, portfolios, risk, backtesting, attribution, scenarios, reporting, API, dashboard, and utilities remain separated when implemented. Circular imports, duplicated business logic, monoliths, notebook-order dependencies, uncontrolled global state, and interface-specific analytical logic are prohibited.

Public Python interfaces use type hints, meaningful names, explicit returns, consistent docstrings, controlled side effects, structured exceptions, and immutable records or pure transformations where practical. Bare exception handling, wildcard imports, hidden caches, print-based primary logging, silent coercion, dead code, speculative abstraction, and mixed-responsibility functions are not acceptable.

Dependencies must be necessary for the active stage, maintained, acceptably licensed, documented, and minimally constrained. Future quantitative, ML, database, API, or dashboard libraries are added only when their active phase requires them. The repository uses one coherent dependency authority.

Logging must be structured and may capture time, severity, component, event, execution identity, counts, locations, duration, validation status, and exception context. It must not capture credentials, private tokens, entire sensitive payloads, or excessive datasets.

## Errors and validation

Correctness-threatening conditions fail loudly with what failed, why it matters, the relevant input, the expected condition, and remediation. Failures may not become empty data, fabricated columns, substitute benchmarks, unlimited forward fills, silently dropped securities, coerced invalid dates, altered frequencies, relaxed constraints, or incomplete comparisons presented as complete. Warnings are reserved for scientifically defensible continuation.

Tests must cover implemented behavior and, as phases grow, unit, integration, schema, temporal, data-quality, numerical, regression, constraints, accounting, API, reproducibility, and critical performance properties. Default tests do not require live internet. Placeholder tests and tests that merely assert success are prohibited.

## Documentation and phase discipline

Documentation is part of the product and must match implemented behavior, methodology, assumptions, configuration, inputs, outputs, validation, limitations, and failures. No document may claim unavailable functionality or evidence.

Only the owner-designated phase may be implemented. No temporary future engine, placeholder model, invented demo, or empty package is permitted. Every phase begins by reading this constitution, the project and phase specifications, current code/tests, Git state, prior risks, and active boundaries. Every phase ends with executed validation, updated documentation, a change and risk summary, acceptance evidence, and a non-fabrication confirmation.

## Definition of done

Work is complete only when applicable requirements and acceptance criteria are met; architecture is coherent; imports, tests, lint, formatting, and types are validated; errors are meaningful; configuration is externalized; provenance and temporal controls are preserved; outputs are reproducible; documentation is accurate; no fabricated input or output, silent scientific fallback, unapproved placeholder, or unresolved critical defect remains. Failed or unavailable checks must be disclosed exactly.

## Prohibited practices

Prohibited practices include fake or randomly generated market history; placeholder data files; hardcoded outputs; invented charts, citations, integrations, or research claims; silent demo or cache fallbacks; mutable raw data; automatic deletion of user files; broad exception suppression; hidden import-time fitting; notebook-only production logic; duplicated metrics; UI-bypassed analytics; global mutable state; speculative deep learning; TODO-only files, empty shells, or `pass` standing for research features; success claims without evidence; and commits, pushes, destructive Git operations, or history rewriting without explicit authorization.
