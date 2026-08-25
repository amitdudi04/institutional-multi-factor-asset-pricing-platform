# Phase 7 Access Resolution Report

## Investigation record

- Investigation completed: `2026-08-11T14:26:57.2176435Z`
- Branch: `phase/7-empirical-research-validation`
- Starting HEAD: `eda43895099e1dd769cdf48f45ea3566af5da1f5`
- Method: current official WRDS and SRM public sources, live WRDS registration selector inspection, secret-safe local access discovery, and official fallback-provider documentation
- External actions: no registration, support request, email, purchase, terms acceptance, login, or data download was performed

## SRM WRDS subscription status

**SRM WRDS SUBSCRIPTION STATUS: NOT FOUND**

Evidence:

1. The live [WRDS registration form](https://wrds-www.wharton.upenn.edu/register/) exposed 525 subscriber options on 2026-08-11. No option matched `SRM`, `SRM Institute of Science and Technology`, or `Sri Ramaswamy Memorial`. The selector did list other Indian subscribers, including six Indian Institutes of Management and the Indian School of Business.
2. Current SRM public material describes access to resources such as Scopus, EBSCO, ProQuest, Emerald, Knimbus and other databases, but searches of official SRM library/resource pages did not identify WRDS, CRSP or Compustat. See the [SRM university brochure](https://webstor.srmist.edu.in/web_assets/downloads/2024/srmist-university-brochure-2024-25.pdf), [SRM online resources](https://library.srmist.edu.in/univlib/ListofOnlineResources.jsp), and [SRM Central Library contact page](https://library.srmist.edu.in/univlib/ContactLibrarian.jsp).

This status is deliberately `NOT FOUND`, not `CONFIRMED ABSENT`: public registration and library evidence is strong enough to reject an automatic SRM registration route, but it is not a copy of SRM's private subscription contracts.

## Available WRDS account route

No SRM-specific registration route is currently available.

- Individual undergraduate/master's account: **NOT ELIGIBLE ON CURRENT EVIDENCE**. WRDS offers this account type only at subscriber institutions, and the registration selector does not offer SRM. WRDS states that individual accounts are available to enrolled undergraduate and master's students at subscriber institutions in its [Terms of Use](https://wrds-www.wharton.upenn.edu/users/tou/).
- Class account: **NOT ELIGIBLE ON CURRENT EVIDENCE**. A class account requires an institutional subscription, an instructor-created class, institutional WRDS representative approval, and a real class code. The [WRDS class-account guide](https://wrds-www.wharton.upenn.edu/pages/about/wrds-account-types/student-guide-enrolling-in-a-class-account/) confirms those registration mechanics. No SRM class, representative, sponsor, or code was found or invented.
- IP/library Access Pass: **NOT ELIGIBLE ON CURRENT EVIDENCE**. WRDS permits Access Pass only through subscriber-controlled eligible locations and institutional email. No SRM WRDS Access Pass, finance lab, trading lab, or IP-authenticated route was found. No VPN or proxy workaround was attempted.
- Institutional email: required only if a valid subscriber route is confirmed; no owner email was requested or fabricated.
- Approval: an individual account or upgrade requires the subscriber institution's WRDS representative.
- MFA: WRDS requires Duo MFA after registration; see [WRDS MFA guidance](https://wrds-www.wharton.upenn.edu/pages/about/log-in-to-wrds-using-two-factor-authentication/).
- Restrictions: WRDS states undergraduate/master's accounts cannot access WRDS during the extended break between semesters; class accounts expire with the class.

## Exact unresolved-institution inquiry

No message was sent. If the owner wants contractual confirmation before purchasing a fallback, the precise inquiry destination is SRM Central Library at the publicly listed `librarian@srmist.edu.in` (or the library help desk), with this body:

> Does SRM Institute of Science and Technology subscribe to Wharton Research Data Services (WRDS)?
>
> If yes, does the subscription include CRSP US Stock, Compustat North America, Compustat Point-in-Time, and CRSP/Compustat Merged?
>
> Are undergraduate students eligible for individual WRDS accounts, class accounts, or IP-authenticated library/lab access?
>
> Who is SRM's WRDS representative or database administrator?

If SRM cannot answer, the owner can submit the same limited questions through [WRDS Support](https://wrds-www.wharton.upenn.edu/contact-support/), identifying the institution and current undergraduate status but sending no password or unnecessary personal data.

## WRDS entitlement status

| Product | Status | Reason |
|---|---|---|
| WRDS platform | ABSENT | SRM subscription not found; `WRDS_USERNAME` and approved password mechanisms remain absent. |
| CRSP US Stock | ENTITLEMENT UNKNOWN | No authenticated subscriber account exists. |
| Compustat North America | ENTITLEMENT UNKNOWN | No authenticated subscriber account exists. |
| Compustat Point-in-Time | ENTITLEMENT UNKNOWN | No authenticated subscriber account exists. |
| CRSP/Compustat Merged | ENTITLEMENT UNKNOWN | No authenticated subscriber account exists. |
| Index/benchmark data | ENTITLEMENT UNKNOWN | No authenticated subscriber account exists. |

WRDS itself explains that vendor datasets such as CRSP require separate institutional licenses; platform access would not prove these entitlements. See [What is WRDS?](https://wrds-www.wharton.upenn.edu/pages/about/what-wrds/).

## Fallback status

### Norgate

**AVAILABLE FOR OWNER ACQUISITION; NOT CURRENTLY SUBSCRIBED OR INSTALLED.**

Official Norgate documentation states that US Stocks Platinum includes history back to 1990, currently listed and delisted securities, historical index constituents, current fundamentals, and suitability for backtesting. Its stable AssetID does not change with ticker/name changes, and its indicators expose dividends, capital events and major-exchange status. See [package comparison and current prices](https://norgatedata.com/stockmarketpackages.php), [data content](https://norgatedata.com/data-content-tables.php), and [integration/identity behavior](https://norgatedata.com/amibroker-usage.php).

The minimum published package meeting the 2010-onward market/universe requirement is **US Stocks Platinum**, currently listed by Norgate at USD 346.50 for six months or USD 630.00 for twelve months. This report does not purchase it, accept its terms, or claim its live schema is already sufficient. Norgate explicitly says its fundamentals are current rather than historical, so they cannot supply point-in-time fundamentals.

The current [Norgate EULA](https://norgatedata.com/subscribe/eula.php) permits personal use and prohibits redistribution, and requires deletion of both Data and Derived Data when a subscription lapses. Those standard lapse terms conflict with indefinite immutable/reproducible research evidence. The route is institutionally acceptable only if Norgate supplies written terms permitting the required academic use, retention and derived outputs, or the owner maintains an uninterrupted subscription for the complete retention period. Written vendor clarification must precede purchase and extraction.

### Sharadar

**ACCESS ABSENT; ENTITLEMENTS UNKNOWN; NOT SELECTED.**

No Nasdaq Data Link/Sharadar API key or client was detected. Nasdaq documents Sharadar Core Fundamentals (`SF1`) as premium and describes the Core US Equities Bundle as a premium product; an API key alone would still not prove subscription. No live tables or rights were assumed. See [Nasdaq Data Link data organization](https://docs.data.nasdaq.com/docs/data-organization) and the [Sharadar publisher page](https://data.nasdaq.com/publishers/SHARADAR).

### SEC EDGAR

**PUBLIC ROUTE AVAILABLE; OWNER CONTACT IDENTITY ABSENT.**

The SEC states that its submissions and XBRL data APIs require no authentication or API key and publishes nightly bulk archives. Automated access must declare an identifying User-Agent/contact and follow SEC policy. See [EDGAR APIs](https://www.sec.gov/search-filings/edgar-application-programming-interfaces) and [Accessing EDGAR Data](https://www.sec.gov/search-filings/edgar-search-assistance/accessing-edgar-data). `IFP_SEC_CONTACT_EMAIL` remains absent and was not invented.

### Owner package

**ABSENT.** No complete owner-supplied security master, effective mappings, market data, point-in-time fundamentals, corporate actions, benchmark, and rights/provenance package is available.

## Selected route and minimal owner action

**Selected route: Norgate Data US Stocks Platinum plus SEC EDGAR.**

The one required owner acquisition action is:

1. Ask Norgate for written confirmation or an appropriate license/addendum permitting local academic research, immutable retention for reproducibility, allowed derived research outputs, attribution and non-redistribution. The request must explicitly address the standard EULA's deletion requirement for Data and Derived Data after subscription lapse.
2. Only after compatible rights are confirmed, purchase or otherwise lawfully obtain **Norgate Data US Stocks Platinum** with **Python (Windows)** access and install it locally.
3. Set `IFP_SEC_CONTACT_EMAIL` in the local environment to a genuine owner-controlled contact address. Do not place the value in Git or chat.

Use the official [Norgate contact form](https://norgatedata.com/contact.php) and ask exactly:

> I am a university student conducting non-commercial academic research in a local, owner-controlled repository. I am considering Norgate Data US Stocks Platinum with Python (Windows) access for a reproducible 2010-onward US-equity study.
>
> Does the standard individual license permit this academic use? May I retain immutable local raw evidence and non-reconstructable derived research artifacts for reproducibility after the subscription ends, without redistributing vendor data? What aggregate statistics, tables, figures, and research reports may be published, and what attribution is required?
>
> The current EULA says Data and Derived Data must be deleted when a subscription lapses and says modifications require a writing signed by a Norgate Director. If the requested retention or outputs are not permitted by the standard license, can Norgate provide the appropriate written agreement or license terms before purchase?

Do not include repository files, credentials, payment information, or unnecessary personal information in that inquiry. Do not purchase until the answer establishes compatible rights.

After those two inseparable components of the selected route exist, resume this branch. The next execution must verify the Norgate product level, licensed features, rights and live schemas; authenticate policy-compliant SEC connectivity; validate stable identities, history, delistings/actions and CIK mappings; and only then acquire ignored runtime data and continue Phase 7 automatically.

## Quality gate result

The access investigation did not change analytical functionality. The required complete validation exposed one order-dependent delivery-launcher defect: `run_dashboard()` set `IFP_DELIVERY_CONFIG` for Streamlit but did not restore the caller's environment. When the launcher test preceded the full connected restart test, the latter attempted to read a deleted temporary configuration. The launcher now restores both absent and pre-existing environment states in a `finally` block, including configuration-load failure, and the regression test verifies both paths.

Final validation after remediation:

- 254 unique tests passed in six non-overlapping coverage batches;
- 103 non-blocking statistical/deprecation warnings;
- 91.37% source-only branch-aware coverage;
- Ruff lint and format checks passed;
- strict mypy passed for 105 source files;
- lock verification passed;
- imports, delivery configuration and authenticated delivery readiness passed;
- dependency audit found no known vulnerabilities;
- no provider data, credentials, API keys, contact identities, caches or generated research artifacts were selected for Git.

## Final verdict

**PHASE 7 INSTITUTIONAL DATA ACCESS UNAVAILABLE — EXTERNAL DATA ACQUISITION REQUIRED**
