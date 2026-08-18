# Phase 2 Input Guide

## Boundary

Phase 2 never accepts caller-supplied data frames or unregistered paths. Prepare the two exact input contracts, ingest them through Phase 1, and pass their authenticated dataset IDs to `compute-factors`. The owner-input path records raw bytes, contract validation, units, temporal policy, mapping authority, lineage, lifecycle, and immutable promotion evidence before factor computation.

## Market input

`factor_market_input` has one row per canonical security and date. Required identity and timing fields are `security_id`, `date`, `available_at`, `eligible`, `eligibility_available_at`, `sector`, `industry`, `classification_available_at`, and `exchange`. Numeric fields are simple total `return`, split-adjusted `price`, consistently based `high` and `low`, `volume`, point-in-time `shares_outstanding`, broad-market total `market_return`, daily simple `risk_free`, and benchmark total `benchmark_return`.

The metadata unit object must exactly declare:

```json
{
  "price_basis": "split_adjusted",
  "return_basis": "total_return",
  "return": "decimal_return",
  "price": "USD",
  "high": "USD",
  "low": "USD",
  "volume": "shares",
  "shares_outstanding": "shares",
  "market_return": "decimal_return",
  "risk_free": "decimal_return",
  "benchmark_return": "decimal_return"
}
```

## Fundamental input

`factor_fundamental_input` is long form with `security_id`, `period_end`, actual or owner-evidenced `available_at`, `field`, `value`, and `unit`. Version 1 permits a non-empty subset of this approved USD vocabulary: `book_equity`, `net_income`, `operating_cash_flow`, `dividends`, `shareholder_equity`, `total_assets`, `gross_profit`, `operating_income`, `revenue`, `average_assets`, `total_accruals`, `total_debt`, `interest_expense`, `prior_total_assets`, `capex`, `prior_capex`, `net_equity_issuance`, `working_capital`, and `prior_working_capital`. The metadata unit object must name exactly the fields present, each with value `USD`; row units must agree. Unknown fields fail. Factors lacking defensible inputs remain null and are reported as not estimable.

## Owner metadata and ingestion

The metadata JSON also supplies non-empty `source_name`, `source_ownership`, `date_semantics`, and `security_identifier_semantics`, plus `mapping_authority_path` pointing inside the project to a persisted Phase 1 security-mapping store. The input file must be CSV, JSON, or Parquet with exact ordered columns and types.

```shell
uv run institutional-factor-platform ingest-owner-factor-input market-prepared factor_market_input market.parquet --metadata-json market-metadata.json
uv run institutional-factor-platform ingest-owner-factor-input fundamentals-prepared factor_fundamental_input fundamentals.parquet --metadata-json fundamental-metadata.json
```

After both runs finalize, compute using only the returned authenticated dataset IDs:

```shell
uv run institutional-factor-platform compute-factors --parent <market-id> --parent <fundamental-id> --market-dataset <market-id> --fundamental-dataset <fundamental-id>
```

Missing historical membership, classification, shares, actual filing availability, total-return adjustment evidence, benchmark, or RF conversion evidence must be acquired through an approved source or owner input. The engine will not reconstruct them from current membership, guess units, invent lags, or silently substitute a proxy.
