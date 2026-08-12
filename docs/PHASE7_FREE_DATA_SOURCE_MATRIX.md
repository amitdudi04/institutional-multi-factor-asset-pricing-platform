# Phase 7 Free Data Source Matrix

Status date: 2026-08-12. This matrix records current first-party terms and live evidence. It does not treat free access as permission by itself.

| Provider | Cost | License / rights | Depth and coverage | Lifecycle / IDs | Actions / shares / fundamentals | Publication and retention | Decision |
|---|---:|---|---|---|---|---|---|
| SEC EDGAR | $0 | U.S. government public access; fair-access policy and identified user agent required | Historical filings and XBRL facts | CIK issuer identity; filing cover-page ticker/exchange evidence | Filing facts, shares, actions and event disclosures where filed | Public research use with provenance; no completeness guarantee | **Selected** for issuer identity and point-in-time fundamentals |
| Alpha Vantage Free | $0 | Free account terms; credential required | `LISTING_STATUS` supports historical dates after 2010-01-01 | Active/delisted snapshots; ticker is not a permanent identifier | Limited free supplementary fields; full adjusted history is premium | Local research evidence only; no premium dependency | **Selected** for historical lifecycle evidence. Annual June snapshots are authenticated and immutable; quota limits are cached and fail closed |
| HF Data Library | $0 | CC BY 4.0; attribution required. Post-March-2022 bars also require IEX attribution and acceptance of IEX historical-data terms | 1,391 U.S. tickers; 818 stocks and 573 ETFs; generally 2002-present | Ticker-level files; not a permanent security master; includes current/former major-index members | Adjusted OHLCV; no complete corporate-action, shares, or PIT fundamental authority | Use, adaptation, publication, redistribution and retention allowed with attribution | **Selected pending owner-created free account** for daily market history. Research universe must disclose its 818-stock ceiling and coverage bias |
| FRED DGS3MO | $0 | Official Federal Reserve public series | Daily risk-free proxy | Series ID | Treasury yield only | Public research with source attribution | **Selected** |
| Kenneth French Data Library | $0 | Official academic research library | Daily factor returns and documented revisions | Dataset identity | Official Mkt-RF, SMB, HML, RMW, CMA, RF and Momentum datasets | Public research with citation | **Selected**; official host transport currently intermittent |
| Yahoo Finance / yfinance | $0 | Current Yahoo terms prohibit automated collection without express prior permission | Broad survivor history; delisted access inconsistent | Ticker-centric | Adjusted prices/actions | Rights insufficient for the automated canonical workflow | **Rejected** as canonical acquisition source |
| Stooq | $0 | Public access, but no sufficiently explicit first-party publication/retention grant was verified | Long daily history for many securities | Ticker-centric; delisted/security-master coverage unclear | Prices; adjustment provenance unclear | Rights unresolved | **Rejected** as canonical evidence |
| Twelve Data Basic | $0 | Free tier is internal/non-commercial and redistribution restricted; deeper history/standard plans vary | Complete daily history for many symbols | Ticker-centric | Prices and some actions | Public empirical outputs not sufficiently authorized under free tier | **Rejected** |
| SimFin Free | $0 | Free/basic non-commercial license | Five years under current free plan | Company/ticker identifiers | Fundamentals and prices, limited depth | Insufficient 2010-onward depth | **Rejected** |
| QuantRocket learning bundle | $0 | Learning use | Survivorship-aware U.S. prices only for 2007-2011 | Vendor-specific | Prices | Does not cover the study period through present | **Rejected** |
| Random Kaggle/GitHub/Hugging Face price dumps | $0 | Often repository-license labels without defensible upstream rights | Varies | Usually ticker-only | Varies | Provenance and upstream licensing commonly unresolved | **Rejected** unless a DOI, explicit data license, and source chain are verified |

## Selected zero-cost stack

The selected architecture is Alpha Vantage Free lifecycle evidence + SEC EDGAR issuer/PIT filing evidence + HF Data Library CC BY 4.0 daily market evidence + FRED DGS3MO + the Kenneth French Data Library. It is a public/free-data empirical validation, not CRSP/Compustat replication.

HF Data Library attribution must include: Elkassabgi, A. (2026), *HF Data Library: Free 1-Minute Intraday U.S. Equity Data*, Zenodo, DOI 10.5281/zenodo.19501605. For post-March-2022 evidence it must additionally state: “Data provided for free by IEX. By accessing or using IEX Historical Data, you agree to the IEX Historical Data Terms of Use.”

## Live defects discovered

- `FD-001` (High, closed in code): HTTPX informational logging rendered an Alpha Vantage query credential. The affected credential was revoked locally, no repository/runtime file contained it, HTTPX/HTTPCore informational logging is now suppressed, provider URLs are redacted in exceptions, and regression tests enforce both controls.
- `FD-002` (Medium, closed): Alpha Vantage returned exact duplicate lifecycle rows. Raw evidence remains immutable; exact duplicates are collapsed only after recording `source_duplicate_count`. Distinct issuers sharing a ticker remain separate.
- `FD-003` (Low, open external): Alpha Vantage free-tier quota responses interrupt batch acquisition. Completed snapshots are cached; error JSON fails closed and no premium upgrade is used.
