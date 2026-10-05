# Contributing

This repository is primarily an independent research project, but well-scoped corrections and improvements are welcome.

When changing research logic:

- preserve point-in-time timing and security-identity rules;
- do not introduce future information into historical decisions;
- add or update tests for finance and statistical behavior;
- keep transaction-cost and portfolio-accounting assumptions explicit;
- do not commit third-party raw data, credentials, local databases, generated model files or private source material;
- keep README and `docs/RESULTS.md` numerical claims consistent with the reported empirical release.

For implementation changes, run:

```shell
uv run pytest
uv run ruff check .
uv run ruff format --check .
uv run mypy src
```

Research extensions that change data, factor definitions, model specifications, costs or temporal splits should be reported as a new experiment rather than silently replacing the existing result set.
