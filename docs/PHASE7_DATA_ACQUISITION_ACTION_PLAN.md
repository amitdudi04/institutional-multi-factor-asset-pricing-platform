# Phase 7 Data Acquisition Action Plan

## Minimal owner action

Provide **one institutional WRDS account with verified entitlements** to the following research components:

1. CRSP US Stock daily/history evidence sufficient for permanent security identities, name/ticker/exchange history, prices and holding-period returns, shares, distributions, corporate actions, delistings and terminal-return evidence.
2. Compustat North America with Point-in-Time capability, or the strongest licensed historical filing/availability evidence that can defensibly populate the required fundamentals.
3. CRSP/Compustat Merged historical link evidence.
4. An authenticated total-return benchmark series that can implement the owner-approved broad S&P 500 proxy, or a separate exact benchmark entitlement/source approved for the study.

The account must permit local owner research across 2010 onward. The owner should confirm retention, no-redistribution, attribution, and derived-output terms. No purchase was attempted.

## Why this is the recommended route

One properly entitled WRDS route most directly resolves the permanent-identity, ticker-history, delisting, corporate-action, daily-return, shares-outstanding, point-in-time fundamental and historical-link requirements without constructing a survivor universe from current tickers. It also permits explicit entitlement probes before any query. FRED DGS3MO and Kenneth French comparison factors are already available as supporting public routes and do not need to be replaced.

## Credential boundary after access exists

Do not send a password in chat or commit it. Supply the WRDS username through `WRDS_USERNAME` and configure the password through WRDS' approved local credential mechanism (for example an owner-controlled `.pgpass` outside the repository) when the adapter is implemented. The repository will record only `PRESENT`/`ABSENT`/entitlement classifications. If institutional policy mandates a different secret store, the adapter must use that store without logging values.

Before extraction, the workflow will probe and record separately:

- WRDS platform access;
- CRSP entitlement;
- Compustat entitlement;
- Compustat Point-in-Time entitlement;
- CRSP/Compustat Merged entitlement;
- benchmark/index entitlement.

An absent entitlement will not be bypassed.

## Planned extracts after access is verified

Provider schemas will be inspected live before column selection. Subject to entitlement, the extraction will obtain:

- CRSP permanent security/company identities and effective-dated name, ticker, exchange, share/security-type and listing histories;
- daily prices, returns, shares, volume, distributions, split/action evidence, delisting dates and delisting returns;
- Compustat fiscal observations with actual publication/availability evidence, restatements and units;
- authorized historical CRSP/Compustat links with effective intervals and link quality;
- exact total-return benchmark evidence and methodology.

These will be transformed into the existing `security_master`, `SecurityMappingStore`, `daily_market`, `corporate_actions`, `factor_market_input`, and `factor_fundamental_input` contracts. Raw extracts, Parquet publications, DuckDB catalogs, and model artifacts remain under ignored runtime paths and will not enter Git.

## Remaining owner research decisions

Data extraction may begin once access/rights pass, but final empirical formation still requires the owner to set the exact transparent large/mid-cap threshold. Before final Phase 4 and Phase 5 claims, the existing open concentration, sector, turnover, liquidity, cost/impact, ML target, horizon, retraining and primary-metric decisions must also be resolved or preregistered as the governing documents require.

## Backup action

If WRDS cannot be supplied, provide one owner-controlled `NASDAQ_DATA_LINK_API_KEY` with verified Sharadar entitlements for historical active/delisted reference, end-of-day price/action evidence, and point-in-time fundamentals. After authentication, the workflow will inspect actual subscribed tables and current schemas; it will not assume product contents.

If neither WRDS nor Sharadar is available, a lawful Norgate Platinum/Diamond installation can cover historical universe/market evidence only when paired with SEC EDGAR under a real `IFP_SEC_CONTACT_EMAIL` or another lawful point-in-time fundamental source. Alternatively, provide the complete owner package defined in `PHASE7_EMPIRICAL_INPUT_REQUIREMENTS.md`.

## Resume command boundary

After the single credential/access action, resume this Phase 7 branch. The next execution will perform entitlement probes first, update `PHASE7_DATA_RIGHTS_REGISTER.md`, inspect provider schemas, acquire ignored runtime data, run the empirical data-quality gate, and only then attempt authenticated Phase 1 through Phase 6 research execution.

Until then:

**PHASE 7 EMPIRICAL VALIDATION BLOCKED — SOFTWARE READY, EXTERNAL DATA ACCESS REQUIRED**
