# Approved Data Source Guide

## Configuration and commands

Validate configuration and initialize ignored local storage:

```shell
uv run institutional-factor-platform validate-config
uv run institutional-factor-platform init-storage
uv run institutional-factor-platform validate-catalog
uv run institutional-factor-platform list-datasets --research-ready
```

Integrity operations also include `verify-raw`, `verify-standardized`, `inspect-lineage`, `inspect-dataset-manifest`, and `reprocess-raw`. Use command help for required explicit paths/checksums/contracts. Reprocessing supports verified byte-native FRED, French, SEC, and owner artifacts without provider retrieval; Yahoo's DataFrame-derived raw representation is not accepted by that byte workflow.

Live commands require explicit arguments and may download external data into ignored raw storage:

```shell
uv run institutional-factor-platform ingest-fred DGS3MO --start 2024-01-01 --end 2024-01-31
uv run institutional-factor-platform ingest-french F-F_Research_Data_5_Factors_2x3_daily
uv run institutional-factor-platform ingest-sec 0000000000
```

The SEC example CIK is format-only and is not a valid request recommendation. Set `IFP_SEC_CONTACT_EMAIL` to the owner's real contact before live SEC use. Do not invent it. `.env.example` documents variables; `.env` is ignored and not automatically loaded.

## Yahoo Finance

The adapter uses yfinance for explicit approved tickers, dates, daily OHLCV, adjusted close, dividends, and splits. It requires internal security-ID mappings and reports empty or partial ticker failures. Yahoo is research-accessible public data, not institutionally licensed data. Adjustment revisions, currency metadata, coverage, outages, and redistribution restrictions remain limitations. Extreme observations are flagged, not removed; prices are never blindly forward-filled.

## FRED

The default is `DGS3MO`, Market Yield on U.S. Treasury Securities at 3-Month Constant Maturity, retained as daily source observations in percent per annum. `TB3MS` is an explicit monthly alternative and is never substituted automatically. Missing markers remain null; Phase 1 performs no yield-to-return conversion or daily forward fill.

## Kenneth French Data Library

The initial approved dataset is `F-F_Research_Data_5_Factors_2x3_daily`; daily momentum is supported as a bounded optional dataset. Original percent units and the explicit decimal-return conversion are both recorded. These are published comparison series, not factors constructed by this project.

## SEC EDGAR

The narrow adapter retrieves company facts for an explicit valid CIK using a compliant owner-supplied user agent. Raw JSON is preserved. When SEC provides only filing date, availability is represented conservatively as UTC end-of-filing-date with `INFERRED_DATE_LEVEL`; it does not claim intraday precision or same-day tradability. Phase 2 must decide the next-session use rule. Impossible period/filing/availability/retrieval chronology blocks promotion. Restatements/amendments remain separate facts; no ratios or factors are calculated.

## Owner-supplied data

CSV, Parquet, and record-list JSON require exact columns plus explicit dataset/contract version, source/ownership, units, date semantics, and identifier semantics. Unknown/extra columns, corrupt files, wrong versions/types, and ambiguous metadata fail; original bytes are never edited. Existing raw bytes may be checked and reprocessed with the explicit integrity CLI. The header-only universe template is not a universe dataset.

## Live validation policy

Unit/integration tests are offline. Live smoke checks are optional, tiny, never committed, and never research results. A missing SEC contact blocks only live SEC retrieval. Provider failure is reported; there is no silent fallback or date-range reduction.
