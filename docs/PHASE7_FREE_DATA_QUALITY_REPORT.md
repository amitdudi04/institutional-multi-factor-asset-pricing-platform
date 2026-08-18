# Phase 7 Free Data Quality Report

Status date: 2026-08-18

## Executive conclusion

The free-source acquisition path is authenticated and materially stronger, but it is not yet sufficient for empirical Phase 2. Alpha Vantage now supplies complete annual June active/delisted lifecycle snapshots from 2010 through 2026. HF Data Library supplies a reconciled 1,391-symbol inventory, of which 822 are classified as stocks and 569 ETFs are rejected. Four adversarial-sample market publications remain research-ready after provider-specific remediation: AAPL, MSFT, SPY, and legacy FB through its verified ticker end date.

The present evidence does not yet establish a point-in-time large/mid-cap universe, historical shares, historical market capitalization, comprehensive corporate actions, terminal returns, or study-wide point-in-time fundamentals. Current SEC ticker evidence maps 707 of the 822 HF stocks, but it is current evidence and is not backdated. No factor, asset-pricing, portfolio, or ML result may be represented as empirical from this acquisition state.

## Authenticated source evidence

| Evidence | Result |
|---|---|
| Alpha Vantage lifecycle | 34 authenticated publications: active and delisted snapshots for every annual June date, 2010–2026 |
| HF public inventory | 1,391 one-to-one reconciled records; 822 stocks selected and 569 ETFs rejected by policy |
| HF market sample | Four research-ready publications after eight historical/unsafe publications were durably demoted |
| FRED DGS3MO | Two authenticated publications; latest covers 2010-01-04 through 2026-08-10 with 4,331 observations |
| Kenneth French | Two authenticated official-host publications: daily five-factor plus daily Momentum |
| SEC current ticker list | 10,398 current rows observed; exact current ticker intersection covers 707 of 822 HF stocks |
| SEC PIT fundamentals | Four authenticated issuer-level company-facts publications; not yet linked to listings or expanded study-wide |

## Lifecycle and universe quality

The annual Alpha active-stock/HF-stock intersection is a coverage diagnostic, not a canonical universe. Ambiguous ticker/date identities are not silently collapsed.

| Formation date | Alpha active stock symbols | HF-covered intersection |
|---|---:|---:|
| 2010-06-30 | 4,165 | 550 |
| 2011-06-30 | 4,361 | 561 |
| 2012-06-30 | 4,513 | 576 |
| 2013-06-30 | 4,737 | 587 |
| 2014-06-30 | 4,996 | 607 |
| 2015-06-30 | 5,435 | 622 |
| 2016-06-30 | 5,783 | 635 |
| 2017-06-30 | 5,842 | 655 |
| 2018-06-30 | 5,774 | 672 |
| 2019-06-30 | 5,805 | 707 |
| 2020-06-30 | 5,850 | 719 |
| 2021-06-30 | 7,293 | 748 |
| 2022-06-30 | 7,967 | 766 |
| 2023-06-30 | 7,116 | 747 |
| 2024-06-30 | 6,684 | 739 |
| 2025-06-30 | 7,026 | 725 |
| 2026-06-30 | 7,967 | 716 |

Thirty-three HF-intersection symbol/date combinations contain more than one Alpha issuer name. Examples include genuine ticker reuse or entity transitions such as ACI, ADT, CZR, DD, PARA, TW, WMG, and WOLF, as well as legal-name variants such as TEL. They remain unresolved unless stronger effective-dated evidence distinguishes them. Across the full Alpha lifecycle evidence, 561 active symbol/date combinations have multiple issuer names.

The HF universe is explicitly documented by its publisher as a fixed circa-2022/2023 snapshot with material pre-2022 survivorship bias. It is not a historical constituent authority and is not called Russell 1000 or S&P 500 history.

### Lifecycle publication register

| Year | Active publication | Delisted publication |
|---:|---|---|
| 2010 | `listing_lifecycle-a36f41b7f0c7be507deaf636` | `listing_lifecycle-b42d18bfac113a40c72cb66c` |
| 2011 | `listing_lifecycle-59f8bf0cdf3ae3e720124281` | `listing_lifecycle-8ef81df1a6e9f90140b2e1c4` |
| 2012 | `listing_lifecycle-ce3f37c71ed70ee4ab144a2d` | `listing_lifecycle-c76b74dfcb05ac709d92797e` |
| 2013 | `listing_lifecycle-45a242025699d08658e61955` | `listing_lifecycle-0afb8a1aca9de2d049ef5f5c` |
| 2014 | `listing_lifecycle-13c040d11d29be0c080262eb` | `listing_lifecycle-041fedd49f2d4a13213b8c2d` |
| 2015 | `listing_lifecycle-aeab2b718a9ba6b069673acc` | `listing_lifecycle-05e4b7851d34c0645acbb077` |
| 2016 | `listing_lifecycle-c47f007ccf913b16461413f0` | `listing_lifecycle-6a453c53048a9666929da2c7` |
| 2017 | `listing_lifecycle-8e12f5c7b21b6c87db37cc2f` | `listing_lifecycle-185f1526a592318be8f04a56` |
| 2018 | `listing_lifecycle-c898b6816d5c25321cddb754` | `listing_lifecycle-b0999ca76e7eb037d446950c` |
| 2019 | `listing_lifecycle-e47683052c9420ac75842f31` | `listing_lifecycle-1c9d2d3e8f49510ceffc137f` |
| 2020 | `listing_lifecycle-27e6d893a4465ca7cd8369d1` | `listing_lifecycle-642d2e36d12d5b4cc2c30c35` |
| 2021 | `listing_lifecycle-3c218cbff346886ea6a41eea` | `listing_lifecycle-2ce6b2c99919cce7450cb250` |
| 2022 | `listing_lifecycle-a4eba225c7f96d5dd2a70ecb` | `listing_lifecycle-04f6d371cb899399ffe4649d` |
| 2023 | `listing_lifecycle-e1bddaa435a8c6bdd07c6496` | `listing_lifecycle-1ea26dd3b30a7fc0ba87a060` |
| 2024 | `listing_lifecycle-ed1cce80d8badc71e5d1edf7` | `listing_lifecycle-d6d16f38771c328250bac136` |
| 2025 | `listing_lifecycle-2f420445ad5403c5db4030e0` | `listing_lifecycle-b7bfe308b42a6a266c9af080` |
| 2026 | `listing_lifecycle-7ed66737d98df0ff34c8a560` | `listing_lifecycle-c5d2c6d2421f6d3f995b9471` |

## Market quality

| Publication ID | Ticker | Rows | Date range | Status |
|---|---|---:|---|---|
| `daily_market-95b54ca990b3e298bc14c703` | AAPL | 4,172 | 2010-01-04–2026-08-05 | PASS_WITH_WARNINGS |
| `daily_market-f1df385da42741d9b2a88024` | MSFT | 4,171 | 2010-01-04–2026-08-04 | PASS_WITH_WARNINGS |
| `daily_market-ed1285b4d527b2a25910c0f2` | SPY | 4,171 | 2010-01-04–2026-08-04 | PASS_WITH_WARNINGS |
| `daily_market-cc93e8679ad07743f2de02a7` | FB | 2,531 | 2012-05-18–2022-06-08 | PASS_WITH_WARNINGS |

These four publications have zero duplicate dates, null closes, non-positive closes, null volumes, or negative volumes. Each preserves the upstream `pitrading`/`iex` feed marker on every standardized row. `PASS_WITH_WARNINGS` reflects coverage/staleness warnings that require research review, not permission to ignore the documented feed break.

HF states that prices are split- and dividend-adjusted and that `clean` applies its nine-step filtering pipeline while preserving gaps. The platform does not apply a second adjustment. Post-March-2022 volume is IEX-only and is not comparable to pre-splice consolidated-tape volume without explicit controls.

## Material defects and dispositions

| ID | Severity | Evidence | Disposition |
|---|---|---|---|
| FD-001 | High | HTTP client informational logging exposed an Alpha Vantage query credential | Closed in code; credential rotated; URL and logger regression tests pass |
| FD-002 | Medium | Alpha lifecycle responses contained exact duplicate rows | Closed; raw evidence retained and exact duplicates recorded/collapsed after retrieval |
| FD-003 | Low | Free-tier quota interrupts unrestricted batch acquisition | Managed; requests paced, completed evidence cached, quota responses fail closed |
| FD-004 | Medium | TWTR and ATVI HF files omitted citation/IEX schema metadata | Open upstream; files rejected and excluded |
| FD-005 | High | FB source file continued beyond verified legacy-ticker interval | Closed; requested-date clipping and effective-dated mapping enforce 2022-06-08 end |
| FD-006 | High | GOOG and GOOGL adjusted closes fell about 95.25% exactly at the 2022-03-07 source splice | Closed in code; live re-ingestion fails closed; affected publications demoted; upstream files excluded |
| FD-007 | High | The SEC fact primary key omitted `period_start`, colliding 2,517 valid Apple keys where quarterly and year-to-date facts shared an end date and filing | Closed in contract v3.1.0; `period_start` is key material, all observed live collisions resolve without dropping rows, and four issuers publish successfully |
| FD-008 | High | Phase 2 required all 19 accounting fields even when free point-in-time evidence could not support them, encouraging fabricated completeness instead of governed non-estimability | Closed in software; a non-empty approved subset is accepted with exact observed-field units, unknown fields fail, and unsupported characteristics remain null with explicit estimability diagnostics |
| FD-009 | High | The issuer mapping store treated multiple simultaneous listings for one issuer as a conflict, making legitimate share classes such as Alphabet impossible to represent | Closed in software; plural resolution preserves every authenticated listing, while legacy singular consumers fail closed when more than one share class is active |

Eight HF publications were durably demoted: six legacy standardized publications that did not preserve per-row feed identity and two corrected-format GOOG/GOOGL publications that failed splice continuity. Historical raw data, manifests, validation reports, lineage, and demotion events were retained.

## Supporting data

The latest authenticated DGS3MO publication is `macro_observations-c81a80f735cccb07624bcb7c` with 4,331 observations from 2010-01-04 through 2026-08-10. The earlier authenticated publication `macro_observations-62a503378065618009d5e7e9` remains historical evidence and contains 4,329 observations through 2026-08-06.

The official Kenneth French five-factor publication `french_factor_returns-adf7661d83688a9374d91fd7` contains 95,124 long-form observations for Mkt-RF, SMB, HML, RMW, CMA, and RF from 1963-07-01 through 2026-06-30. The official Momentum publication `french_factor_returns-f803dd07dbe251239dbe0c33` contains 26,173 observations from 1926-11-03 through 2026-06-30. Both are authenticated comparison evidence; they do not replace the platform's own factor construction.

SEC company facts are authenticated for Apple (`sec_financial_facts-c3bb91229bf1838fbd7157ae`, 25,135 rows), Microsoft (`sec_financial_facts-43ae6b01066b2c47d140c44d`, 32,671), Meta (`sec_financial_facts-7cd980b4173126a78d4c5ad3`, 18,053), and Alphabet (`sec_financial_facts-99512737441d0370cd0da855`, 20,907). Filing dates and date-level availability are preserved. These are issuer-level facts with null `security_id`; they cannot join market listings until effective-dated issuer-to-listing mappings are authenticated.

The governed annual SEC projector now selects only registered standard-taxonomy concepts, enforces annual flow durations versus instant facts, rejects conflicts, retains amendment availability, computes only complete formulas, derives lags without look-ahead, and supports authenticated one-to-many issuer/share-class mappings. It has not been run empirically because the required effective-dated issuer-to-listing authority is still missing.

## Remaining blocking data gaps

- Canonical effective-dated CIK/listing/share-class mappings for the study universe.
- A preregistered, defensible universe rule that does not claim unavailable large/mid-cap ranking evidence.
- Point-in-time shares and market capitalization, or an explicitly narrower universe design that does not require them.
- Study-wide point-in-time SEC fundamentals, selected accounting concepts, filing lags, restatement policy, and authenticated issuer-to-listing mappings.
- Corporate-action and terminal-event evidence for delisted/acquired securities.
- Broader HF daily coverage after per-file attribution and splice checks.

## Readiness verdict

**REAL PHASE 1 ACQUISITION IN PROGRESS — EMPIRICAL PHASE 2 NOT AUTHORIZED.**

The software controls and current publications are authenticated, but the research data contract is incomplete. Advancing to factor results would create unsupported identity, universe, market-cap, fundamental, and survivorship claims.
