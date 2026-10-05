# Reproducibility

## Release Identity

The empirical research release is identified by:

- `project-complete-public-data-v1`
- `research-empirical-public-v1`
- commit `5a3e930665756fa7aaedeceb5f9ab90792bcf849`

These identifiers refer to the empirical state used for the reported factor, asset-pricing, portfolio and machine-learning results.

## Environment

Python 3.11 or newer and `uv` are required.

```shell
uv sync --all-groups
```

Dependency versions are recorded in `uv.lock`.

## Data Requirements

Exact empirical reproduction requires lawful local access to the source material described in [DATA_AND_SOURCES.md](DATA_AND_SOURCES.md), including the market history, lifecycle evidence, SEC evidence and mapping information used by the original run.

Third-party raw data are not redistributed through this repository.

## Research Order

A reproduction should follow the analytical dependency order:

1. validate configuration;
2. acquire or restore the required source evidence;
3. build security/issuer mappings and point-in-time market/fundamental inputs;
4. construct factors;
5. estimate asset-pricing models;
6. run portfolio/cost/scenario analysis;
7. run the temporal ML experiment;
8. verify delivery/reporting outputs.

Later stages should not be run against a different upstream data identity while being described as the same empirical release.

## Key Frozen Research Settings

Portfolio cost sensitivity:

- LOW: 5 bps one way
- BASE: 10 bps one way
- HIGH: 20 bps one way

Reported ML design:

- features: book-to-market and 12-minus-1 momentum;
- target: 21-session security return minus SPY return;
- monthly decisions;
- 60 months training;
- 12 months validation;
- 1 month test;
- purging plus a 1-month embargo;
- monthly retraining;
- seed 17;
- single-thread estimators.

## Validation Commands

```shell
uv run pytest
uv run coverage report --fail-under=90
uv run ruff check .
uv run ruff format --check .
uv run mypy src
uv lock --check
uv run institutional-factor-platform validate-catalog
uv run institutional-factor-platform verify-delivery-platform
git diff --check
```

The verified research release passed 300 tests with 90.59% branch-aware coverage.

## What Can Be Reproduced from Git Alone?

A reviewer can inspect and run the code, tests, configuration, schemas, methodology, factor/model logic, portfolio accounting, temporal split logic and delivery software.

The exact third-party empirical bytes are not contained in Git, so the complete numerical study cannot be reconstructed from the repository alone without reacquiring the required data under the relevant provider terms.
