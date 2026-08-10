# Empirical Data Quality Report

## Status

`PARTIAL — END-TO-END EQUITY STUDY BLOCKED`

This report records only data actually retrieved and authenticated during the first post-v1.0 empirical attempt. It is not an equity-universe data-quality report and contains no factor, asset-pricing, portfolio, or machine-learning result.

## Authenticated FRED evidence

| Field | Observed value |
|---|---:|
| Provider | Federal Reserve Economic Data (FRED) |
| Series | DGS3MO |
| Requested sample | 2010-01-01 through 2026-08-07 |
| Actual source observations | 2010-01-04 through 2026-08-06 |
| Authenticated publication | `macro_observations-62a503378065618009d5e7e9` |
| Rows | 4,329 |
| Non-null values | 4,151 |
| Explicit source-missing values | 178 (4.1118%) |
| Duplicate primary keys | 0 |
| Business dates absent from provider response | 0 |
| Unit | percent per annum |
| Frequency | daily |
| Validation | PASS |

The source-missing values remain null and were not interpolated. Phase 1 preserved percent-per-annum units and did not convert the series to daily returns. The publication passed manifest, checksum, lifecycle, lineage, configuration, validation, restart-read, and rebuilt-catalog authentication.

## Equity data unavailable

The following required equity-quality dimensions could not be measured: security coverage, historical eligibility, listing history, delistings, mapping failures, price staleness, zero volume, extreme returns, corporate actions, point-in-time shares, fundamentals and their availability lags, benchmark alignment, and survivorship bias. No approved authenticated equity publication was available.

The absence is not treated as zero missingness or acceptable coverage. It blocks Phase 2 and every connected downstream empirical phase.

