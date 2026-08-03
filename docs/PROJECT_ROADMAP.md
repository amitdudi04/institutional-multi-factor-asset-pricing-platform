# Project Roadmap

This roadmap summarizes the boundaries defined in `docs/PROJECT_SPECIFICATION.md`. It does not authorize implementation, settle proposed/open assumptions, or claim completed analytical functionality. Each phase requires approved prerequisite decisions, acceptance criteria, and evidence-based closeout.

## Phase 1 — Institutional Data Platform

Implemented through a second focused remediation, pending final independent re-audit: approved adapters, immutable raw and standardized storage, authenticated v3 publication manifests, complete promotion lifecycle evidence, stable listing identity and symbol history, validated-only DuckDB promotion, calendars, fundamentals, and macro/published-factor inputs. Corporate-action fields are retained by the market adapter and a separate action contract is defined; no issuer-scale live dataset is claimed. No research model may precede a passing re-audit of validated, provenance-controlled inputs.

## Phase 2 — Multi-Factor Research Engine

Implement financially motivated observable factors, standardization and neutralization, factor portfolios and diagnostics, latent PCA factors, and validation. Factor definitions, universe, timing, weighting, and bias controls must be explicit.

## Phase 3 — Asset-Pricing Research Platform

Implement approved CAPM and multifactor specifications, rolling estimation, robust inference, diagnostics, and cross-model comparison. Models are conditional on data availability and documented identification assumptions.

## Phase 4 — Portfolio Construction and Institutional Backtesting

Implement approved benchmark portfolios and optimizers with realistic constraints, execution lags, transaction costs, and walk-forward evaluation. Infeasibility and missing inputs must never trigger silent constraint relaxation.

## Phase 5 — Risk Analytics and Explainable Machine Learning

Implement approved risk, scenario, stress, simulation, and interpretable predictive or ranking methods with time-aware validation. Machine learning must answer a defined investment-research question and expose limitations.

## Phase 6 — API, Dashboard, and Research Workspace

Expose stable core services through approved API and dashboard interfaces, with provenance, freshness, and downloadable research artifacts. User interfaces must not duplicate or bypass core analytical logic.

## Phase 7 — Production Hardening and Research Publication

Complete continuous integration, packaging and deployment controls, performance and security reviews, documentation, model and data cards, research reporting, and the final reproducibility audit.

## Stage gates

Every phase begins with governance/specification review, repository and Git inspection, reusable-component assessment, unresolved-risk review, and confirmation of scope. It ends with validation evidence, documentation updates, acceptance-criteria evaluation, unresolved-risk disclosure, and explicit confirmation that neither data nor results were fabricated.
