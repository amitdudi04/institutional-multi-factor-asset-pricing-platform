# Phase 7 Data Source Selection Report

## Executive conclusion

No complete institutional US-equity route is executable in the current environment. Current public evidence does not identify SRM Institute of Science and Technology as a WRDS subscriber, so WRDS is no longer the selected acquisition target. The single recommended acquisition path is Norgate Data US Stocks Platinum for historical universe/market evidence, paired with SEC EDGAR for filing-time fundamental evidence. Yahoo is not selected as universe authority. FRED and Kenneth French are usable supporting sources but cannot make the equity study ready.

Discovery was secret-safe: only environment-variable names/status, standard credential-path existence, installed applications, importable client names, repository/runtime file metadata, and provider connectivity outcomes were inspected. No credential value was printed or persisted.

## Access discovery

| Capability | Classification | Evidence |
|---|---|---|
| SRM WRDS subscription | NOT FOUND | On 2026-08-11, the live WRDS registration form exposed 525 subscriber-selector options. No option matched SRM, SRM Institute of Science and Technology, or Sri Ramaswamy Memorial. Current public SRM library/resource pages name other subscribed databases but do not name WRDS, CRSP, or Compustat. This is not represented as contractual proof of absence. |
| WRDS platform access | ABSENT | No matching environment name, `.pgpass`, `.wrds` path, installed client, or `wrds` Python module was found. |
| CRSP entitlement | ENTITLEMENT UNKNOWN | Platform access is absent, so entitlement could not be probed lawfully. |
| Compustat entitlement | ENTITLEMENT UNKNOWN | Platform access is absent, so entitlement could not be probed lawfully. |
| Compustat Point-in-Time entitlement | ENTITLEMENT UNKNOWN | Platform access is absent, so entitlement could not be probed lawfully. |
| CRSP/Compustat Merged entitlement | ENTITLEMENT UNKNOWN | Platform access is absent, so entitlement could not be probed lawfully. |
| Nasdaq Data Link / Sharadar access | ABSENT | No matching API-key environment name, config path, client module, or installed application was found. |
| Sharadar table entitlements | ENTITLEMENT UNKNOWN | No authenticated account was available for a table probe. |
| Norgate access | ABSENT | No installation, standard data directory, installed application, or `norgatedata` module was found. |
| SEC owner identity | ABSENT | `IFP_SEC_CONTACT_EMAIL` is declared only as an empty template name in `.env.example`; no runtime value exists. |
| Owner-supplied empirical package | ABSENT | No complete security master, mappings, market/fundamental contract, actions, benchmark, or rights package exists in the repository runtime scope. |
| FRED DGS3MO | PRESENT | Existing authenticated 2010-onward publication passes catalog validation. |
| Kenneth French | PRESENT | Fresh prior readiness connectivity standardized the approved daily FF5 dataset in memory; no payload was persisted. |

## Source selection matrix

| Route/source | Access and entitlement | Historical coverage | Survivorship / delistings | Historical mappings | Prices / actions | Point-in-time fundamentals | Rights status | Decision and reason |
|---|---|---|---|---|---|---|---|---|
| WRDS / CRSP / Compustat | SRM subscription not found; local access absent; entitlements unknown | Potentially suitable, not verified | Potentially suitable, not verified | Potentially suitable through permanent IDs/authorized links, not verified | Potentially suitable, not verified | Potentially suitable only with verified Compustat PIT/history semantics | Not established | NOT SELECTED; retain only as a conditional future route if SRM or another legitimate affiliation is confirmed |
| Nasdaq Data Link / Sharadar | Access absent; premium entitlement unknown | Not inspected without entitlement | Not inspected | Not inspected | Not inspected | Not inspected | Not established | NOT SELECTED; no key or entitlement exists and product contents cannot be assumed |
| Norgate US Stocks Platinum plus SEC EDGAR | Installation/subscription absent; SEC contact identity absent | Norgate publishes daily US-stock history back to 1990 | Norgate publishes currently listed and delisted coverage and historical membership | Norgate exposes a stable AssetID unaffected by name/ticker changes; exact effective history still requires live schema inspection | Norgate publishes price/volume, dividends, capital events and major-exchange status | SEC submissions/XBRL can preserve filing/accession availability; Norgate current fundamentals are not PIT evidence | Standard Norgate EULA requires deletion of Data and Derived Data when the subscription lapses; compatible academic retention/publication terms are not established. SEC is public subject to declared User-Agent and policy | SINGLE RECOMMENDED ACQUISITION PATH, conditional on written Norgate rights compatible with immutable/reproducible research; live rights/schema validation remains mandatory before extraction |
| SEC EDGAR alone | Owner identity absent | Filing history only; no security universe | Does not solve the universe alone | Requires CIK-to-Norgate identity mapping | Does not solve market history | Public submissions and XBRL APIs are usable after genuine contact identity and documented normalization | Not authorized in this execution | SELECTED ONLY AS THE FUNDAMENTAL COMPONENT OF THE NORGATE + SEC ROUTE |
| Owner-supplied | Required files absent | Unknown | Unknown | Unknown | Unknown | Unknown | Attestation absent | REJECTED FOR CURRENT EXECUTION; accepted later only if the exact contract package passes |
| Yahoo secondary price route | Prerequisite universe/mapping gate failed | Not tested | Not a universe authority | Requires pre-existing effective mappings | Secondary route only | No | Project local-only baseline, source terms still controlling | REJECTED FOR CURRENT EXECUTION; calling it now would create unsupported selection/survivorship evidence |
| FRED | Public route present | DGS3MO 2010-01-04 to 2026-08-06 in authenticated runtime publication | Not applicable | Not applicable | Not applicable | Not applicable | Restricted to local no-redistribution project use | SELECTED SUPPORTING SOURCE for risk-free evidence only |
| Kenneth French | Public route present | Approved daily FF5 dataset connectivity verified through 2026-06-30 | Not an equity universe | Not applicable | Official comparison factor returns only | Not applicable | In-memory use only pending study-specific rights confirmation | SELECTED SUPPORTING SOURCE for comparison/model input only |

## Selected route

The selected acquisition target is **Norgate Data US Stocks Platinum plus SEC EDGAR**. Platinum is the minimum Norgate level that publishes the required 2010-onward history, delisted securities, historical index constituents, major-exchange status, stable security identity, dividends, and capital-event evidence. SEC EDGAR supplies public filing/submission and XBRL evidence with actual filing/accession availability; Norgate's current fundamentals must not be substituted for point-in-time fundamentals.

No backup is recommended by this report because Master Prompt 15.0 requires exactly one acquisition path when institutional access is unavailable. WRDS and Sharadar remain lawful conditional possibilities if genuine access later appears, but neither is an actionable current route.

The route is not yet acquired. No Norgate installation/subscription and no runtime `IFP_SEC_CONTACT_EMAIL` were found. Norgate's standard EULA states that Data and Derived Data must be deleted when a subscription lapses, which is incompatible with indefinite immutable/reproducible evidence unless the vendor grants compatible written terms or the subscription remains continuously active. Before purchase or extraction, the owner must obtain written confirmation covering academic use, local immutable retention, derived research outputs, attribution and non-redistribution. The workflow must then inspect the licensed Norgate Python interface and terms, register rights, verify identity/history fields, and use a genuine owner-controlled SEC contact email without committing it.

## Research-design decisions preserved

No provider was used to invent the exact large/mid-cap threshold. The owner-approved universe concept remains in force, but its exact transparent breakpoint is still required before final portfolio formation. The exact benchmark instrument/index, return methodology, and history also remain unresolved. Later Phase 4 cost/concentration limits and the Phase 5 empirical target/horizon remain open and were not inferred.

## Final source verdict

**PHASE 7 INSTITUTIONAL DATA ACCESS UNAVAILABLE — EXTERNAL DATA ACQUISITION REQUIRED**
