# Phase 7 SEC XBRL Concept Registry

Status date: 2026-08-18

## Governance boundary

This registry governs projection from authenticated SEC issuer facts into the approved Phase 2 fundamental vocabulary. It does not itself authorize a listing-level join. SEC company facts remain issuer-level until effective-dated issuer-to-listing evidence is authenticated; a current ticker list is never backdated, company names are never fuzzy-matched, and a multi-class issuer resolves to its complete authenticated listing set. Singular consumers fail closed rather than selecting a share class.

Only standard `us-gaap` concepts listed below are eligible. Registrant extensions remain unrecognized until separately reviewed. Missing concepts and missing formula components remain missing. No missing component is interpreted as zero. Source facts retain CIK, accession, form, fiscal metadata, period start/end, filing date, date-level availability, taxonomy, concept, unit, retrieval time, and restatement history.

The accepted form set is `10-K`, `10-K/A`, `10-Q`, and `10-Q/A`. Annual research fields use `10-K`/`10-K/A` facts with a validated annual duration for flow concepts and instant fiscal-year-end facts for stocks. Quarterly and year-to-date facts are not mixed. Filing date is the available date-level lower bound because Company Facts does not expose an acceptance timestamp. Research needing intraday acceptance must authenticate the original filing header before using finer timing.

The implemented annual projector applies these rules per accession, selects the accession's latest fiscal period end, rejects conflicting values, and preserves later amendments as later-available observations. Complete same-filing formulas and prior-period lags are calculated only when every required input was legitimately available. Projection requires an immutable effective-dated issuer-to-listing mapping authority; one issuer may map to multiple share classes, and every authenticated class receives the issuer characteristic without collapsing identities.

Point-in-time shares are governed separately from monetary fundamentals. The only approved Company Facts share-count concept is `dei:EntityCommonStockSharesOutstanding` in `shares`, from the accepted form set. Duplicate identical facts within an accession collapse; conflicting, non-positive, non-finite, or incomplete facts fail closed. Because Company Facts does not preserve the dimensional share-class context needed to allocate an issuer total, projection is allowed only when exactly one authenticated listing is effective on the filing date. Multi-listing issuers remain not estimable until original inline-XBRL dimensional evidence supports an exact allocation. Amendments remain later-available observations and never overwrite earlier evidence.

Legacy pre-inline filings use a separate parser for exactly one embedded `EX-101.INS` attachment. It recognizes official historical `xbrl.us/dei` and current `xbrl.sec.gov/dei` namespaces and only `DocumentType`, `EntityCentralIndexKey`, `EntityRegistrantName`, `Security12bTitle`, `SecurityExchangeName`, `TradingSymbol`, `EntityCommonStockSharesOutstanding`, and `EntityPublicFloat`. Contexts, explicit/typed dimensions, units, decimals, instance filename, attachment checksum, parser version, and filing identity are preserved. Only dimensionless issuer-level shares enter the existing PIT projector; dimensional subsidiary/class values remain evidence but are not silently allocated.

## Approved field registry

| Phase 2 field | Method | Primary standard concept(s) | Governed fallback / calculation |
|---|---|---|---|
| `book_equity` | Direct | `StockholdersEquity` | `StockholdersEquityIncludingPortionAttributableToNoncontrollingInterest`; fallback is disclosed because it includes noncontrolling interest |
| `net_income` | Direct | `NetIncomeLoss` | `ProfitLoss` |
| `operating_cash_flow` | Direct | `NetCashProvidedByUsedInOperatingActivities` | None |
| `dividends` | Direct | `PaymentsOfDividendsCommonStock` | `PaymentsOfDividends` |
| `shareholder_equity` | Direct | `StockholdersEquity` | `StockholdersEquityIncludingPortionAttributableToNoncontrollingInterest` |
| `total_assets` | Direct | `Assets` | None |
| `gross_profit` | Direct | `GrossProfit` | Missing when the registrant does not report this standard concept |
| `operating_income` | Direct | `OperatingIncomeLoss` | None |
| `revenue` | Direct | `RevenueFromContractWithCustomerExcludingAssessedTax` | `Revenues`, then `SalesRevenueNet` |
| `average_assets` | Derived | — | Mean of current and prior eligible annual `total_assets`; both required |
| `total_accruals` | Derived | — | `net_income - operating_cash_flow`; both required |
| `total_debt` | Component family | `LongTermDebtCurrent` plus `LongTermDebtNoncurrent` | Alternative finance-lease-inclusive current/noncurrent family; families may not overlap |
| `interest_expense` | Direct | `InterestExpenseNonOperating` | `InterestAndDebtExpense` |
| `prior_total_assets` | Lag | — | Prior eligible annual `total_assets`; no forward fill |
| `capex` | Direct | `PaymentsToAcquirePropertyPlantAndEquipment` | None |
| `prior_capex` | Lag | — | Prior eligible annual `capex`; no forward fill |
| `net_equity_issuance` | Not estimable | — | Remains missing until a complete mutually exclusive issuance/repurchase component policy is validated |
| `working_capital` | Difference | `AssetsCurrent`, `LiabilitiesCurrent` | `AssetsCurrent - LiabilitiesCurrent`; both required |
| `prior_working_capital` | Lag | — | Prior eligible annual `working_capital`; no forward fill |

All projected monetary rows use `USD`. Facts reported in another unit are rejected rather than converted without an authenticated exchange-rate policy. Per-share, shares, pure ratios, and currency-per-share units cannot satisfy monetary fields. The separate shares projection uses only the exact `shares` unit and cannot satisfy a monetary field.

## Filing and restatement policy

- A fact becomes eligible no earlier than its SEC filing date; period end is never availability.
- For each filing/accession and target field, concept precedence is deterministic and only one concept family may win.
- Annual flow facts require an annual duration; instant facts require no `period_start`.
- An amendment or later filing is a new observation at its own availability date. It does not overwrite evidence available earlier.
- Comparative prior-year facts repeated in a later filing do not become the current fiscal observation merely because they were refiled.
- Conflicting facts at the same governed identity and precedence remain unresolved; the projector must fail closed rather than choose by row order.
- Derived and lagged fields inherit the latest availability of every required input.

## Current authenticated evidence

Live Company Facts publications exist for Apple, Microsoft, Meta, and Alphabet. The observed standard concepts support much of the direct registry, but coverage differs by issuer: Meta and Alphabet do not expose every requested direct concept, and Alphabet demonstrates the one-issuer/multiple-listing problem. These four issuer publications validate source ingestion and concept discovery only. They do not constitute a study-wide listing-linked fundamental panel, and empirical Phase 2 remains unauthorized.
