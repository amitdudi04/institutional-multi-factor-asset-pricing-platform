# Final Reproducibility Guide

Reproduction requires the ignored local source cache, mapping authorities, governed YAML configuration, repository revision, and locked Python environment. Third-party raw data must not be committed or redistributed.

## Released research identity

- Validated merged commit: `5a3e930665756fa7aaedeceb5f9ab90792bcf849`
- Empirical tag: `research-empirical-public-v1`
- Project-complete tag: `project-complete-public-data-v1`

The tags identify the audited empirical state. Later documentation-only commits must not move them.

## Environment setup

Install Python 3.11 or newer and `uv`, check out one of the empirical tags, and run `uv sync --all-groups`. Configuration lives under `config/`; dependency identity is locked in `uv.lock`. Do not substitute package versions silently when attempting an exact reproduction.

## Data-source and credential requirements

The study depends on locally retained, lawfully obtained HF Data Library market evidence, Alpha Vantage listing/lifecycle evidence, SEC EDGAR submissions and XBRL evidence, FRED macro/risk-free evidence, Kenneth French Library factors, and the persisted issuer/listing mapping authorities. Availability and licence terms remain source-specific.

Credentials, where a provider requires them, are supplied only through environment variables described by `.env.example`. Never place live values in YAML, Markdown, command history, manifests, or committed `.env` files. A reviewer without the original source cache can audit code, configuration, tests, schemas, and publication identities but cannot reconstruct third-party empirical bytes from Git alone.

## Pipeline order

1. Validate configuration and confirm the checked-out empirical tag.
2. Place immutable source evidence in the configured ignored raw paths.
3. Rebuild or authenticate effective-dated security, issuer/listing, lifecycle, share, and fundamental authorities.
4. Authenticate the two Phase 1 research inputs.
5. Reproduce/authenticate Phase 2 factors, then Phase 3 asset-pricing publications.
6. Reproduce/authenticate Phase 4 portfolios and scenarios using frozen 5/10/20 bps costs.
7. Reproduce/authenticate Phase 5 monthly walk-forward models using the exact Phase 4 parent.
8. Verify Phase 6 delivery and reports, then run catalog, test, restart, and tamper gates.

No phase should be run against an unauthenticated or identity-mismatched parent.

## Canonical chain

- Phase 1 market: `factor_market_input-89848f8e3c34d53d0432f6e0`
- Phase 1 fundamentals: `factor_fundamental_input-962c8ada3e74e32b00568cd7`
- Phase 2: `factor-5a73616f131fca2102fa2ca4141ad64f`
- Phase 3: `asset-pricing-c0a72fae5349f1048e18557250da1927`
- Phase 4 BASE equal weight: `portfolio-dfef8d60d8a771e61224f0b314efd86c`
- Phase 4 scenario: `portfolio-2bbcdff643c1ca3e00f579e0011180fa`
- Phase 5 definitive models: `ml-bcbbaff3cd9f024d49938b1aed5dfd37`, `ml-46b546a56162bb6daf900678c9e330ad`, `ml-9e9d520fc0113ef49d7ad1dbd6dfdcb7`, `ml-dff42ab45ac3b36a981760610f398e08`, `ml-ecf5c69a336bd8f98ea7391eb2dd6bae`, `ml-e76a9235dabcfb2813d0fb8e7a7e2b66`, `ml-254e61bf6b12db81998d4dd14ea3620b`, `ml-5388bdaccc65ee409cbd9fbc447c1294`
- Phase 6 reports: `report-aad813665bff9552e3ebe8ff735c5248`, `report-6a8c1ed3dcd185b18d89a0587785a991`, `report-56a9fd450dc573d6785585f1e2a8f1d4`, `report-08bc1e78b4f264be03165081c47e92b4`

## Frozen empirical design

Phase 4 one-way LOW/BASE/HIGH costs are 5/10/20 bps. Phase 5 uses book-to-market and 12-minus-1 momentum; 21-session future excess return versus SPY; monthly decisions; 60/12/1-month train/validation/test; purge plus one-month embargo; monthly retraining; seed 17; and one thread. Do not change these values during reproduction.

## Validation commands

```shell
uv sync --all-groups
uv run pytest
uv run coverage report --fail-under=90
uv run ruff check .
uv run ruff format --check .
uv run mypy src
uv lock --check
uv run --with pip-audit pip-audit
uv run institutional-factor-platform validate-catalog
uv run institutional-factor-platform verify-delivery-platform
git diff --check
```

Identical source bytes, mappings, configuration, and code identity must authenticate the same immutable publications. A new analytical code commit intentionally produces new publication IDs; historical publications remain immutable. `equity_issuance` must remain non-estimable unless defensible source inputs and policy are added through governance.

## Expected limitations during reproduction

The source-selected universe is not CRSP/Compustat or historical-index replication. Early point-in-time breadth is limited, third-party data cannot be redistributed through this repository, and exact reproduction depends on retaining the licensed/permitted local evidence. Test fixtures demonstrate software behavior only and must never be reported as empirical replication.
