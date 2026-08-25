# Phase 7 Free/Public-Data Universe Protocol

Status: preregistered before empirical performance analysis; bounded construction completed, Phase 2 not estimable

## Name and non-claim

The fallback study population is named the **Free Public-Data Covered Common-Stock Research Universe**. It is not the Russell 1000, S&P 500, or a CRSP/Compustat-equivalent universe. It may be called large/mid-cap only if point-in-time price and legitimately available shares support an annual June top-1,000 ranking. Otherwise the size claim is omitted.

## Annual June formation rule

For each June formation date from 2010 onward, a listing is eligible only when all of the following evidence is authenticated and effective on that date:

1. An Alpha Vantage historical active listing snapshot contains the exact symbol and a permitted US venue (`NASDAQ`, `NYSE`, or `NYSE MKT`).
2. Alpha classifies the row as `Stock`; this is necessary but not sufficient.
3. HF Data Library has an attributable daily file for the exact effective symbol and the file passes internal schema, identity, source-splice, date, and price validation.
4. An SEC filing cover or another approved public authority binds the exact ticker/share class to a CIK for the effective interval. The filing-cover projector requires an exact same-context common-stock title, trading symbol, and supported exchange; debt contexts and incomplete/conflicting triples are excluded. Current or filing-date SEC evidence is never backdated beyond its supported interval.
5. SEC filing history supports a domestic common-equity classification. Foreign private issuers/ADRs, preferred shares, funds, REITs, warrants, rights, units, and other rejected instruments are excluded. Name-pattern screening alone cannot prove eligibility.
6. Ticker reuse, ticker changes, acquisitions, and multiple share classes have non-overlapping effective evidence. Ambiguous cases are excluded and retained in the exception register.
7. If point-in-time shares and price are available, eligible listings are ranked by June market capitalization and the top 1,000 form the large/mid-cap variant. Missing shares do not become zero and current shares are not backdated.

Formation occurs before outcome measurement. The rule, exclusions, and missing-data treatment may not be changed in response to returns.

## Coverage intersection

The annual report must separately show: Alpha eligible listings, identity-confirmed common listings, HF-covered listings, validated market histories, point-in-time-share coverage, SEC-fundamental coverage, unresolved terminal events, and final usable listings. A denominator is never silently changed to improve coverage.

The preliminary exact Alpha-active/HF-stock intersection observed before identity screening ranges from 550 listings in 2010 to 766 in 2022 and 716 in 2026. These are coverage candidates, not approved universe counts: HF's broad `stock` category includes foreign/ADR-like securities, and the current SEC ticker list cannot establish their historical identity.

## Survivorship and terminal events

Historical Alpha snapshots, not a present-day constituent list, establish contemporaneous listing presence. HF coverage selection is reported as a separate source-availability filter because it may itself create survivorship bias. Delisted and acquired listings remain eligible through their evidenced end date. Terminal returns are included only when supported by trading or transaction evidence; otherwise they are labeled `UNRESOLVED TERMINAL RETURN` and enter preregistered sensitivity analysis.

## Final bounded construction

The completed evidence intersection contains AAPL and MSFT only. FB/META lacks a continuous accepted HF successor history and eligible dimensionless PIT shares. GOOG/GOOGL fails the documented source-splice continuity check. The retained panel cannot be called large/mid-cap because annual top-1,000 market-cap ranking is not supported.

The exact Phase 1 publications pass authentication, but maximum cross-sectional breadth is two. No Phase 2 empirical publication is authorized because the preregistered minimum is three. The threshold and weighting method are not changed after observing the data limitation.
