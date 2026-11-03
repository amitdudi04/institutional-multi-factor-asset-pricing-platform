# Reproducibility

## Release Identity

The current results are supported by the documented validation and reconciliation evidence. Exact historical identifiers remain in the research manifests linked from the [research evidence index](research_audit/INDEX.md).

Current corrected results follow the accepted research lineage pinned above. The final-candidate PDF and cross-document claim/checksum matrices are in [outputs/audit/final_correction](../outputs/audit/final_correction/); the editable DOCX is private author delivery.

### Historical original release

The empirical research release is identified by:

- `project-complete-public-data-v1`
- `research-empirical-public-v1`

These tags refer to the historical original experiment, not the corrected results. The exact factor, asset-pricing, portfolio, and machine-learning publication identifiers are retained in the [research source manifest](../outputs/audit/phase3/PHASE3_SOURCE_MANIFEST.json) for technical verification. Historical intermediate results are not the final reported findings. The machine-learning experiment retains its actual historical feature, label and cost inputs rather than using the corrected quantile returns from the separate portfolio study.

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

A reproduction first restores the common evidence and then evaluates three related research components. The asset-pricing, portfolio and machine-learning analyses do not form a single sequence of model outputs:

1. Validate configuration and restore the required source evidence.
2. Build security/issuer mappings and market/fundamental inputs under the recorded availability controls.
3. Construct the relevant factor scores, portfolio returns and historical features.
4. Run the asset-pricing regressions using the matched holding-period research panel.
5. Independently evaluate portfolio allocation, transaction costs and scenarios using the documented quantile-return inputs.
6. Independently run the temporal machine-learning study using its historical features and labels.
7. Verify the associated outputs and research reporting.

These analyses share documented source inputs but must retain their respective timing and publication identities. Outputs from different data vintages must not be presented as the same empirical release.

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
