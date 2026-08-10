# Phase 6 API Guide

Start the loopback service:

```shell
uv run institutional-factor-platform validate-delivery-config
uv run institutional-factor-platform verify-delivery-platform
uv run institutional-factor-platform serve-api
```

The API prefix is `/api/v1`. Endpoint families cover system health/readiness/version/governance/limitations; unified and phase-specific publications; lineage and artifact inventories; factors; asset-pricing estimates; portfolio, performance, risk, scenarios and costs; ML model cards, predictions, evaluation, explanations, drift and economic evaluation; and deterministic reports.

Pagination uses validated `offset` and `limit` parameters with a configured maximum. Publication and artifact identifiers use a constrained identifier grammar. Unknown fields in report requests are rejected. Mutation endpoints require JSON. Errors use redacted envelopes and never include tracebacks.

Loopback anonymous review is the safe default. If `IFP_API_TOKEN` is set under optional mode, bearer authentication becomes mandatory. Required mode fails startup without a non-empty token. Non-loopback binding requires explicit authorization and bearer protection unless the separately named unsafe development override is deliberately enabled. This is local single-owner access control, not multi-tenant identity management.

The process health endpoint does not require a token so container health checks can function. Readiness validates configuration, repository access, and authenticated discovery; zero empirical publications is a valid ready empty state.
