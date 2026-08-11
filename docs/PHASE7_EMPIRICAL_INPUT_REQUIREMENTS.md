# Phase 7 Empirical Input Requirements

## Purpose

This document states the minimum lawful evidence required before Phase 7 may download equity data or produce empirical results. It is derived from the current repository contracts. It contains schemas only—no fabricated records.

The owner may supply CSV, JSON, or Parquet. Columns must appear in the exact order shown. Parquet types must exactly match. Every source must include explicit ownership/licensing and provenance metadata. Runtime empirical files belong under ignored `data/` storage and must not be committed.

## Required delivery package

1. An effective-dated US common-equity universe and canonical security master.
2. Effective-dated provider/symbol mappings for every security and requested period.
3. Market/factor input satisfying `factor_market_input`.
4. Point-in-time fundamentals satisfying `factor_fundamental_input`.
5. Corporate-action and delisting evidence sufficient to support the supplied total-return series.
6. Benchmark total-return evidence for the approved broad S&P 500 proxy, including exact instrument/index identity and methodology.
7. A rights/provenance statement covering local research use, retention and non-redistribution.
8. A real SEC contact identity only if SEC EDGAR will be used.

## Universe and security-master authority

The historical universe cannot be a present-day ticker list. It must identify inclusion/exclusion intervals, security type, listing venue and delisting where applicable. The exact `security_master` table schema is:

| Column | Arrow type | Nullable | Requirement |
|---|---|---:|---|
| `security_id` | string | No | Stable owner-assigned canonical security identity; never a reusable ticker. |
| `ticker` | string | No | Effective ticker for this record. |
| `normalized_ticker` | string | No | Normalized provider-independent ticker. |
| `issuer_name` | string | No | Issuer legal/display name. |
| `exchange` | string | No | Exchange code. |
| `mic` | string | Yes | ISO market identifier code where available. |
| `asset_type` | string | No | Must support the approved common-stock screen. |
| `listing_type` | string | No | Primary/common listing classification. |
| `currency` | string | No | USD for the approved baseline unless explicitly reviewed. |
| `country` | string | No | Country classification. |
| `sector` | string | Yes | Point-in-time sector if used. |
| `industry` | string | Yes | Point-in-time industry if used. |
| `primary_listing` | bool | No | Primary-listing flag. |
| `active` | bool | No | Effective active status, not present-day survivorship. |
| `listing_start_date` | date32 | Yes | First effective listing date. |
| `listing_end_date` | date32 | Yes | Delisting/end date. |
| `source` | string | No | Source authority. |
| `source_identifier` | string | No | Provider-native identity. |
| `retrieval_timestamp` | UTC timestamp[us] | No | Authentic retrieval time. |
| `availability_timestamp` | UTC timestamp[us] | No | Earliest research-available time. |
| `schema_version` | string | No | Contract version. |
| `metadata_quality_status` | string | No | Explicit validation/quality state. |

Only US-listed primary common shares in the approved large/mid-cap design may enter. ETFs, ADRs, preferred shares, closed-end funds, ETNs, REITs, warrants, rights, units, SPAC units, funds, debt, derivatives, crypto, options and futures are excluded.

## Effective-dated mapping authority

The owner must provide a persisted mapping authority consumed by `SecurityMappingStore`. Each mapping has these fields:

| Field | Type | Requirement |
|---|---|---|
| `source` | approved `DataSource` value | Provider whose identifier is mapped. |
| `source_identifier` | string | Non-empty provider-native identifier. |
| `ticker` | string or null | Effective ticker, normalized to uppercase by the mapping constructor. |
| `exchange` | string or null | Effective exchange. |
| `mic` | string or null | Effective MIC. |
| `cik` | string or null | Ten-digit SEC CIK when applicable. |
| `valid_from` | ISO date | Inclusive effective start. |
| `valid_to` | ISO date or null | Inclusive effective end. |
| `status` | mapping status | `RESOLVED` requires a canonical `security_id`; unresolved records cannot carry one. |
| `evidence` | mapping-evidence value | Authority for the mapping. |
| `provenance` | string | Non-empty source/method statement. |
| `retrieval_timestamp` | timezone-aware timestamp | Authentic retrieval time. |
| `security_id` | string or null | Canonical identity when resolved. |

Intervals for the same provider identifier may not ambiguously overlap across different canonical securities. Symbol changes, mergers, share-class changes and delistings require new effective records rather than overwriting history.

## Owner market/factor input contract

Contract name: `factor_market_input`. Required exact columns:

| Order | Column | Arrow type | Nullable | Semantics/unit |
|---:|---|---|---:|---|
| 1 | `security_id` | string | No | Must resolve through the persisted mapping authority. |
| 2 | `date` | date32 | No | Exchange observation date. |
| 3 | `available_at` | UTC timestamp[us] | No | Earliest time the row was available to research. |
| 4 | `eligible` | bool | No | Point-in-time universe eligibility. |
| 5 | `eligibility_available_at` | UTC timestamp[us] | No | Availability time of eligibility evidence. |
| 6 | `sector` | string | No | Point-in-time sector value. |
| 7 | `industry` | string | No | Point-in-time industry value. |
| 8 | `classification_available_at` | UTC timestamp[us] | No | Availability of classification. |
| 9 | `return` | float64 | Yes | Decimal total return. |
| 10 | `price` | float64 | Yes | USD, split-adjusted price basis. |
| 11 | `high` | float64 | Yes | USD. |
| 12 | `low` | float64 | Yes | USD. |
| 13 | `volume` | float64 | Yes | Shares. |
| 14 | `shares_outstanding` | float64 | Yes | Shares, point-in-time. |
| 15 | `exchange` | string | No | Effective listing exchange. |
| 16 | `market_return` | float64 | Yes | Decimal return for the adopted market series. |
| 17 | `risk_free` | float64 | Yes | Frequency-matched decimal return derived from approved DGS3MO evidence. |
| 18 | `benchmark_return` | float64 | Yes | Decimal total return for the explicitly named approved proxy. |

Required unit metadata must exactly equal:

| Metadata key | Required value |
|---|---|
| `price_basis` | `split_adjusted` |
| `return_basis` | `total_return` |
| `return`, `market_return`, `risk_free`, `benchmark_return` | `decimal_return` |
| `price`, `high`, `low` | `USD` |
| `volume`, `shares_outstanding` | `shares` |

The owner must explain how dividends, splits, mergers, delistings and missing terminal returns are reflected. Missing values remain missing; no zero or forward-fill substitution is inferred.

## Owner fundamental input contract

Contract name: `factor_fundamental_input`. Required exact columns:

| Order | Column | Arrow type | Nullable | Semantics |
|---:|---|---|---:|---|
| 1 | `security_id` | string | No | Canonical identity. |
| 2 | `period_end` | date32 | No | Fiscal period end. |
| 3 | `available_at` | UTC timestamp[us] | No | Public filing/publication availability used by the research design. |
| 4 | `field` | string | No | One approved field name below. |
| 5 | `value` | float64 | No | Reported numeric value. |
| 6 | `unit` | string | No | `USD`. |

Approved required field vocabulary:

`book_equity`, `net_income`, `operating_cash_flow`, `dividends`, `shareholder_equity`, `total_assets`, `gross_profit`, `operating_income`, `revenue`, `average_assets`, `total_accruals`, `total_debt`, `interest_expense`, `prior_total_assets`, `capex`, `prior_capex`, `net_equity_issuance`, `working_capital`, `prior_working_capital`.

The source package must preserve the reported fiscal period, filing/publication date, research `available_at`, restatement policy, security mapping, source document/provider, currency/unit and retrieval provenance. A period-end date is not an availability date.

## Mandatory owner metadata

Every owner-supplied request must provide these non-empty fields:

- `path`
- `schema`
- `contract_version`
- `source_name`
- `source_ownership`
- exact `units` mapping
- `date_semantics`
- `security_identifier_semantics`
- `mapping_authority_path` for both Phase 2 input contracts

The owner must also attest the right to use the data for local research, retention constraints, redistribution prohibition, provider attribution and any derived-output restrictions. Repository MIT licensing does not grant rights to external data.

## SEC identity, if SEC is selected

Supply a real SEC-compliant contact/User-Agent identity controlled by the owner. Do not place it in Git or documentation. Provide it through the documented environment/configuration boundary. If lawful point-in-time owner fundamentals are supplied, SEC may be classified `NOT REQUIRED` for that study.

## Study decisions still required after data delivery

Before Phase 4/5 empirical claims, the owner must approve exact concentration, sector, turnover, liquidity, cost and market-impact assumptions, plus the empirical ML target and horizon. These open decisions do not prevent data readiness review, but they prevent final portfolio/ML study claims.

## Acceptance checklist

- Exact schemas, column order, types and units pass without coercive guessing.
- Universe and mappings cover 2010-01-01 onward with effective intervals and delistings.
- No current-constituent substitution is presented as historical membership.
- Every row maps to one canonical security at its date.
- Market and fundamental availability timestamps are defensible and timezone-aware.
- Corporate-action/total-return methodology and benchmark identity are explicit.
- Rights/provenance permit the intended local research use.
- Files are placed only in ignored runtime storage and pass immutable ingestion/authentication.

Until this checklist passes, downstream empirical phases are `NOT EXECUTED — REQUIRED LAWFUL INPUT UNAVAILABLE`.
