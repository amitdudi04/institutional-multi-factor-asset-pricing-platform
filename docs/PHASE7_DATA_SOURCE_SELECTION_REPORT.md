# Phase 7 Data Source Selection Report

## Executive conclusion

No complete institutional US-equity route is executable in the current environment. Route A is the preferred acquisition route, Route B is the backup, and Routes C–E remain conditional alternatives. Yahoo is not selected as universe authority. FRED and Kenneth French are usable supporting sources but cannot make the equity study ready.

Discovery was secret-safe: only environment-variable names/status, standard credential-path existence, installed applications, importable client names, repository/runtime file metadata, and provider connectivity outcomes were inspected. No credential value was printed or persisted.

## Access discovery

| Capability | Classification | Evidence |
|---|---|---|
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
| WRDS / CRSP / Compustat | Access absent; entitlements unknown | Potentially suitable, not verified | Potentially suitable, not verified | Potentially suitable through permanent IDs/authorized links, not verified | Potentially suitable, not verified | Potentially suitable only with verified Compustat PIT/history semantics | Not established | RECOMMENDED PRIMARY ACQUISITION ROUTE; strongest design if the exact entitlements are obtained |
| Nasdaq Data Link / Sharadar | Access absent; premium entitlement unknown | Not inspected without entitlement | Not inspected | Not inspected | Not inspected | Not inspected | Not established | RECOMMENDED BACKUP; validate live subscribed schemas before adapter work |
| Norgate plus PIT fundamentals | Installation absent | Not inspected | Not inspected | Not inspected | Not inspected | Norgate current fundamentals are not acceptable PIT evidence; a second lawful source is required | Not established | REJECTED FOR CURRENT EXECUTION; conditional fallback only |
| SEC EDGAR | Owner identity absent | Filing history only; no security universe | Does not solve the universe alone | Requires CIK-to-listing authority | Does not solve market history | Potentially usable after identity and documented XBRL normalization | Not authorized in this execution | REJECTED FOR CURRENT EXECUTION; possible fundamental supplement only |
| Owner-supplied | Required files absent | Unknown | Unknown | Unknown | Unknown | Unknown | Attestation absent | REJECTED FOR CURRENT EXECUTION; accepted later only if the exact contract package passes |
| Yahoo secondary price route | Prerequisite universe/mapping gate failed | Not tested | Not a universe authority | Requires pre-existing effective mappings | Secondary route only | No | Project local-only baseline, source terms still controlling | REJECTED FOR CURRENT EXECUTION; calling it now would create unsupported selection/survivorship evidence |
| FRED | Public route present | DGS3MO 2010-01-04 to 2026-08-06 in authenticated runtime publication | Not applicable | Not applicable | Not applicable | Not applicable | Restricted to local no-redistribution project use | SELECTED SUPPORTING SOURCE for risk-free evidence only |
| Kenneth French | Public route present | Approved daily FF5 dataset connectivity verified through 2026-06-30 | Not an equity universe | Not applicable | Official comparison factor returns only | Not applicable | In-memory use only pending study-specific rights confirmation | SELECTED SUPPORTING SOURCE for comparison/model input only |

## Primary and backup route

The selected acquisition target is **Route A: WRDS with CRSP US Stock, Compustat North America Point-in-Time (or the strongest historically timestamped licensed equivalent), CRSP/Compustat Merged link evidence, and exact benchmark evidence**. This is a recommendation, not a claim of access.

The selected backup is **Route B: a Sharadar subscription whose live entitlements demonstrably include active and delisted security reference, end-of-day prices/actions, and point-in-time fundamentals**. Table names and schemas must be inspected after authenticated access; none are assumed here.

If neither is available, Route C requires a lawful Norgate installation plus a separate point-in-time fundamental source. Route E remains valid if the owner supplies every exact contract in `PHASE7_EMPIRICAL_INPUT_REQUIREMENTS.md` with rights evidence.

## Research-design decisions preserved

No provider was used to invent the exact large/mid-cap threshold. The owner-approved universe concept remains in force, but its exact transparent breakpoint is still required before final portfolio formation. The exact benchmark instrument/index, return methodology, and history also remain unresolved. Later Phase 4 cost/concentration limits and the Phase 5 empirical target/horizon remain open and were not inferred.

## Final source verdict

**PHASE 7 EMPIRICAL VALIDATION BLOCKED — SOFTWARE READY, EXTERNAL DATA ACCESS REQUIRED**
