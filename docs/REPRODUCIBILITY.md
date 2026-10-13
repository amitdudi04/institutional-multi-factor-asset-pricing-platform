# Reproducibility

## Release Identity

The empirical research release is identified by:

- `project-complete-public-data-v1`
- `research-empirical-public-v1`
- commit `5a3e930665756fa7aaedeceb5f9ab90792bcf849`

These identifiers refer to the previous empirical state used for the reported factor, asset-pricing, portfolio and machine-learning results.

## Current Audit Status

The previous release's asset-pricing statistics and dependent portfolio/ML metrics are not validated under the corrected calculations. See [RESULTS_RECONCILIATION.md](RESULTS_RECONCILIATION.md) for the result-by-result interpretation and status. The audit branch aligns portfolio and factor returns over the same formation-to-realization interval, compounds daily risk-free returns to that interval, computes Jensen alpha from portfolio and market excess returns, and treats constant ML predictions as a neutral equal-weight baseline. Targeted regression tests cover these cases, and the full repository CI workflow has passed on the current audit commit. This validates the software checks, not the corrected empirical results: the data-backed pipeline still needs to be rerun before the numerical tables can be treated as current.

The raw provider data are absent from Git. Until the original lawful data inputs are restored or reacquired, the corrected pipeline cannot regenerate the empirical outputs. The numbers in [RESULTS.md](RESULTS.md), README tables, and the associated paper must remain labeled as historical pre-correction results; do not silently carry them forward as corrected findings.

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

The previous verified research release recorded 301 tests passing with 90.52% branch-aware coverage; this is a historical software-validation record, not evidence that the corrected empirical tables have been regenerated.

## What Can Be Reproduced from Git Alone?

A reviewer can inspect and run the code, tests, configuration, schemas, methodology, factor/model logic, portfolio accounting, temporal split logic and delivery software.

The exact third-party empirical bytes are not contained in Git, so the complete numerical study cannot be reconstructed from the repository alone without reacquiring the required data under the relevant provider terms.
