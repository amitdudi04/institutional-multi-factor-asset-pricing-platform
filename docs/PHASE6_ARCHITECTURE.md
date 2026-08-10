# Phase 6 Delivery Architecture

## Purpose

Phase 6 is the final research-delivery layer. It exposes existing authenticated Phase 1-5 evidence without reimplementing factor, regression, optimization, risk, backtest, or machine-learning calculations.

```text
FastAPI / Streamlit / CLI
          |
DeliveryService, DeliveryCatalog, ReportService
          |
Existing Phase 1-5 authenticated repositories
          |
Immutable manifests, artifacts, lineage, checksums
```

## Trust boundary

`DeliveryCatalog` calls the existing `ResearchDatasetRepository`, `FactorRepository`, `AssetPricingRepository`, `PortfolioRepository`, and `MLRepository`. Publication authentication occurs before discovery or artifact reading. Artifact paths come only from authenticated manifests and are resolved against the project root. User-provided filesystem paths, SQL, Python expressions, templates, and model uploads are not accepted.

The API and dashboard perform display-only formatting, filtering, stable pagination, and chart preparation. Analytical values retain publication identity, units, configuration identity, Git identity, validation status, and limitations.

## Components

| Component | Responsibility |
|---|---|
| `delivery.config` | Strict host, authentication, CORS, request, pagination, report, cache, and logging policy |
| `delivery.catalog` | Unified authenticated discovery and bounded artifact reads |
| `delivery.reporting` | Deterministic checksum-bound Markdown, HTML, JSON, and CSV reports |
| `api` | Versioned read-oriented FastAPI routes and request security policy |
| `dashboard` | Nine-page Streamlit review workspace with explicit empty states |
| `observability` | Redacted structured events and bounded in-process counters |

No Phase 6 component is an alternative analytical source of truth.
