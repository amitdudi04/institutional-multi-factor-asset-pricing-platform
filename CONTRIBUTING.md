# Contributing

Read `docs/DEVELOPMENT_CONSTITUTION.md` and `docs/PROJECT_SPECIFICATION.md` before changing the repository. Preserve immutable evidence, temporal integrity, explicit assumptions, historical reports, and phase boundaries. Never commit data, runtime models, reports, credentials, caches, or fabricated financial results.

Run before review:

```shell
uv sync --all-groups
uv run pytest
uv run coverage report --fail-under=90
uv run ruff check .
uv run ruff format --check .
uv run mypy src
uv lock --check
```

Changes require focused tests, documentation, an evidence-based risk statement, and a clean diff. Security issues should follow `SECURITY.md` rather than a public exploit disclosure.
