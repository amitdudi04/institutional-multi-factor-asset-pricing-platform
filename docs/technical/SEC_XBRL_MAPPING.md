# SEC/XBRL Mapping Notes

This note summarizes how SEC issuer-level evidence is mapped into the listing-level point-in-time research panel.

## Issuer and Listing Identity

SEC CIK identifies a registrant. It does not automatically identify one listed share class.

The project therefore separates:

- issuer identity;
- listing/security identity;
- effective dates;
- ticker/exchange history;
- issuer-to-listing mappings.

Issuer facts can reach a listed security only through an effective-dated mapping. A multi-class issuer is not silently collapsed to one share class.

## Filing Availability

A fundamental observation carries its filing availability information. Research joins use what was available by the relevant date rather than backdating a later filing to its fiscal period end.

Amended filings remain later observations.

## Monetary Fundamentals

The accepted Phase-2 vocabulary includes fields such as:

- book equity;
- net income;
- operating cash flow;
- dividends;
- shareholder equity;
- total assets;
- gross profit;
- operating income;
- revenue;
- debt;
- interest expense;
- capital expenditure;
- working-capital components.

The projection layer uses explicit US-GAAP concept rules and rejects conflicting or incompatible evidence instead of selecting a value by row order.

Projected monetary values use USD. Per-share, share-count, ratio and incompatible currency units cannot satisfy a monetary field without an explicit conversion policy.

## Shares Outstanding

Shares outstanding are handled separately from monetary fundamentals.

The preferred filing evidence is the SEC common-stock shares-outstanding concept with the exact `shares` unit. When issuer-level facts do not preserve enough dimensional information to allocate a value across multiple listed share classes, the listing-level share count remains unavailable.

This prevents a multi-class issuer total from being assigned arbitrarily to one security.

## Historical Inline and Legacy XBRL

The codebase supports both modern inline XBRL and older XBRL filing structures. Parsers preserve filing identity, context, units and dimensions needed for later validation.

## Missing Evidence

If a required concept, context, unit, filing identity or listing mapping is missing or ambiguous, the related research field is not manufactured. This policy is the reason some characteristics can be non-estimable even when the rest of the issuer's financial history is available.

For the broader data design, see [../DATA_AND_SOURCES.md](../DATA_AND_SOURCES.md).
