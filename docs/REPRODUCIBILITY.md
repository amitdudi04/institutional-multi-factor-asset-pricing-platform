# Reproducibility

## Release Identity

Numerical authority: [accepted correction commit f22f5cb](https://github.com/amitdudi04/institutional-multi-factor-asset-pricing-platform/tree/f22f5cbe365e98c8d5fef6b5308ff765703df173/outputs/audit), with the [Phase 3 reconciliation](https://github.com/amitdudi04/institutional-multi-factor-asset-pricing-platform/tree/f22f5cbe365e98c8d5fef6b5308ff765703df173/outputs/audit/phase3/PHASE3_COMPLETE_VALIDATION.md) and [Phase 2C matched-sample checks](https://github.com/amitdudi04/institutional-multi-factor-asset-pricing-platform/tree/f22f5cbe365e98c8d5fef6b5308ff765703df173/outputs/audit/phase2c/PHASE2C_REGRESSION_VERIFICATION.md). The [final documentation candidate](https://github.com/amitdudi04/institutional-multi-factor-asset-pricing-platform/tree/research/institutional-final-documentation-corrections) is a research branch; corrected claims do not describe unmerged historical `main`.

Current corrected results are on the unmerged research lineage. The final-candidate PDF and cross-document claim/checksum matrices are in [outputs/audit/final_correction](../outputs/audit/final_correction/); the editable DOCX is private author delivery.

### Historical original release

The empirical research release is identified by:

- `project-complete-public-data-v1`
- `research-empirical-public-v1`
- commit `5a3e930665756fa7aaedeceb5f9ab90792bcf849`

These identifiers refer only to the historical original experiment. Current tables use the accepted corrected factor `factor-4ddee9ac6fb45cedfd62a2cc68676b58`, matched primary pricing `asset-pricing-d60bee7310b34976c80372a0f0f29e21`, separate supplementary pricing `asset-pricing-8c2396179c4b509796b2cab043ec31d2`, and the 24 portfolio/eight final ML identities enumerated in the [pinned Phase 3 manifest](https://github.com/amitdudi04/institutional-multi-factor-asset-pricing-platform/tree/f22f5cbe365e98c8d5fef6b5308ff765703df173/outputs/audit/phase3/PHASE3_SOURCE_MANIFEST.json). Historical intermediates are not final publications. ML retains its actual raw-score/market and original fee-context parents, not corrected quantile returns it never consumes.

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
3. build security/issuer mappings and market/fundamental inputs under the recorded availability controls;
4. construct factors;
5. estimate asset-pricing models;
6. run portfolio/cost/scenario analysis;
7. run the temporal ML experiment;
8. verify delivery/reporting outputs.

Later stages should not be run against a different upstream data identity while being described as the same empirical release.

## Key Frozen Research Settings

Portfolio cost sensitivity:

- LOW: 5 bps per absolute-traded-weight unit
- BASE: 10 bps per absolute-traded-weight unit
- HIGH: 20 bps per absolute-traded-weight unit

Half-L1 one-way turnover is distinct from L1. Initial deployment has L1=1 and a full switch L1=2. Fees are modeled assumptions; inner-sleeve execution is not verified.

Reported ML design:

- features: book-to-market and 12-minus-1 momentum;
- target: 21-session security return minus SPY return;
- monthly decisions;
- expanding training, initially 60 and finally 74 months;
- 12 months validation;
- 1 month test;
- purging plus a 1-month embargo;
- monthly retraining;
- seed 17;
- single-thread estimators;
- 27,632 rows / 89 common month ends / 15 dependent folds / 7,286 held-out observations per family;
- 100 moving-block resamples / block 3 / seed 17;
- one-session reset-to-cash economic checks, distinct from 21-session forecast labels.

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

The accepted Phase 3 correction passed 372 tests with 90.62% coverage and 91 targeted tests. These are prior checkpoint results, not a new full-suite run for this docs-only pass. Historical original 301 tests/90.52% remains an archived assurance record. Document/link/equation/source checks are recorded separately.

## What Can Be Reproduced from Git Alone?

A reviewer can inspect and run the code, tests, configuration, schemas, methodology, factor/model logic, portfolio accounting, temporal split logic and delivery software.

Original vendor/normalized Parquet bytes and model bundles are not public. Exact reproduction requires lawful access to the frozen original vintage; current vendor reacquisition is not equivalent. Stored hashes and 540 cached source guards authenticate accepted identity without resolving dividend treatment, exhaustive SEC capture, modeled-close execution or historical live forecast timing. H1/H3 original approval/decision records remain missing.
