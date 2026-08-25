# Final Reproducibility Guide

Reproduction requires the ignored local source cache, mapping authorities, governed YAML configuration, repository revision, and locked Python environment. Third-party raw data must not be committed or redistributed.

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

Identical source bytes, mappings, configuration, and code identity must authenticate the same immutable publications. A new analytical code commit intentionally produces new publication IDs; historical publications remain immutable. `equity_issuance` must remain non-estimable unless defensible source inputs and policy are added through governance. Docker and GitHub/merge/tag operations were deferred and are not evidence from this run.
