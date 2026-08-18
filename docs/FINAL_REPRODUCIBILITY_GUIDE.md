# Final Reproducibility Guide

The empirical publications require the local ignored source cache, mapping authorities, governed YAML configuration, repository revision, and locked Python environment. Third-party raw data must not be committed or redistributed.

Key authenticated publications:

- Phase 1 market: `factor_market_input-89848f8e3c34d53d0432f6e0`
- Phase 1 fundamentals: `factor_fundamental_input-962c8ada3e74e32b00568cd7`
- Corrected Phase 2: `factor-5a73616f131fca2102fa2ca4141ad64f`
- Corrected Phase 3: `asset-pricing-c0a72fae5349f1048e18557250da1927`

Run the configured local validation commands:

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

Re-ingestion must reproduce the two Phase 1 dataset IDs from identical input bytes and mapping authority. Recomputing an analytical phase after a code commit intentionally produces a new publication ID; older publications remain immutable. Phase 4 or Phase 5 must not be run until their open owner decisions are made explicitly in configuration.

Docker and GitHub operations are outside this local run: `DOCKER = DEFERRED BY OWNER — NOT PART OF THIS RUN`; `GITHUB / MERGE / TAGS = DEFERRED BY OWNER — NOT PART OF THIS RUN`.
