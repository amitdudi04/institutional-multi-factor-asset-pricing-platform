# Phase 7 Single Owner Action Required

## Final acquisition blocker

**PHASE 7 EMPIRICAL VALIDATION BLOCKED — ONE EXTERNAL OWNER DATA ACTION REQUIRED**

No WRDS credentials, CRSP/Compustat entitlements, Norgate installation, Sharadar credential, SEC owner identity, or complete owner empirical package is available. FRED DGS3MO and Kenneth French factor connectivity remain available but cannot provide the required historical equity universe, permanent identities, delistings, market history, point-in-time fundamentals, or authenticated benchmark evidence.

## The one required owner action

Obtain and make available **one owner- or institution-controlled WRDS account with verified entitlement to CRSP US Stock, Compustat Point-in-Time, and CRSP/Compustat Merged linking evidence** for local 2010-onward research.

The entitlement must permit the project to retrieve permanent security and company identifiers, effective-dated name/ticker/exchange history, daily returns/prices/shares/volume, distributions and delistings, point-in-time accounting facts with defensible availability, and authorized historical CRSP/Compustat links. The owner must also confirm the applicable retention, attribution, redistribution, and derived-output terms.

Configure only the non-secret username through `WRDS_USERNAME`. Store the password through WRDS' approved owner-controlled credential mechanism, such as a `.pgpass` file outside the repository or an institutional secret store. Do not send the password in chat and do not commit it.

This is one acquisition path. The owner does **not** also need Norgate, Sharadar, SEC bulk files, or manually assembled CSV contracts if the stated WRDS entitlements are available.

## Automatic continuation after that action

After access exists, resume `phase/7-empirical-research-validation`. Codex will independently verify each entitlement, inspect live provider schemas, register rights, acquire ignored runtime extracts, construct the canonical security master and effective mappings, use the preregistered Project Top-1000 large/mid universe when licensed Russell membership is unavailable, authenticate SPY total returns as the approved empirical benchmark, and execute the complete Phase 1 through Phase 7 empirical and assurance workflow.

No empirical phase can lawfully begin before this action is complete.
