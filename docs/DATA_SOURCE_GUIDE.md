# Approved Data Source Guide

## Configuration and commands

Validate configuration and initialize ignored local storage:

```shell
uv run institutional-factor-platform validate-config
uv run institutional-factor-platform init-storage
```

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

The narrow adapter retrieves company facts for an explicit valid CIK using a compliant owner-supplied user agent. Raw JSON is preserved. Long-format facts retain taxonomy, concept, unit, period, filing, form, accession, frame, and availability. XBRL concepts are not assumed comparable across issuers; restatements are retained rather than silently resolved. No ratios or factors are calculated.

## Owner-supplied data

CSV, Parquet, and record-list JSON require an explicit supported contract and provenance parameters. The original is copied into immutable raw storage, hashed, manifested, validated, and only then standardized. Column meanings are never guessed. Use the header-only universe template for required field names; it is not a universe dataset.

## Live validation policy

Unit/integration tests are offline. Live smoke checks are optional, tiny, never committed, and never research results. A missing SEC contact blocks only live SEC retrieval. Provider failure is reported; there is no silent fallback or date-range reduction.
