# Free/Public-Data Empirical Validation

## Abstract

This study screened all 822 HF Data Library stock candidates before examining analytical performance. Exact HF attribution and source-transition checks, Alpha lifecycle evidence, SEC ticker/CIK evidence, tagged annual filing covers, point-in-time shares, governed US-GAAP concepts, and bounded identity intervals produced a frozen universe of 487 equities. The empirical panel contains 715,447 daily market rows and 37,273 point-in-time fundamental rows. It supports 47 of the 48 configured Phase 2 factors and five configured Phase 3 model families. Portfolio net economics and machine learning are not estimable because their governing owner decisions remain open.

## Universe construction

The waterfall was HF existence and schema, attribution, PITRADING-to-IEX splice integrity, approved instrument/venue, exact current SEC CIK, single-listing share allocation, SEC submissions and Company Facts, two exact eligible inline-XBRL annual listing anchors spanning at least two years, post-share-jump basis compatibility, governed SEC projection, and unresolved terminal-event exclusion. Present identity, shares, or names were never backfilled historically. The detailed 822-row candidate matrix and source artifacts remain in ignored runtime storage.

Final dispositions are: 487 accepted; 114 HF attribution failures; 56 HF splice failures; 68 identity failures; 70 share failures; 16 unresolved terminal events; 7 split-basis failures; 2 asset-type exclusions; 1 non-US/venue exclusion; and 1 fundamental-projection failure. The accepted universe contains 372 Tier A and 115 Tier B securities. No Tier C security passed.

An optional cheap non-HF review identified 5,264 current Alpha/SEC exact-ticker US-listed stock candidates outside HF. None was admitted because no already-authenticated market history shared the HF source/adjustment basis; mixing a second un-reconciled source would make the panel methodologically inconsistent.

## Coverage

Daily market breadth has minimum 1, median 428, mean 336.206, maximum 487, 5th percentile 4, and 95th percentile 487. Monthly market breadth has minimum 3, median 428, mean 339, and maximum 487. Annual distinct-security breadth is 4 (2018), 46 (2019), 357 (2020), 404 (2021), 431 (2022), 466 (2023), and 487 (2024–2026).

Shares-valid daily breadth has median 420 and maximum 487. Fundamentals-valid breadth has median 400 and maximum 487. The joint shares-and-fundamentals breadth has median 394 and maximum 487; early dates legitimately have zero joint breadth and remain non-estimable rather than backfilled.

## Phase 2 results

The authenticated Phase 2 publication is `factor-5a73616f131fca2102fa2ca4141ad64f`. It contains 34,341,456 factor rows, 11,545 portfolio rows, all 48 configured definitions, and validation status `PASS_WITH_WARNINGS`. Forty-seven factors are estimable. `equity_issuance` has zero observations because its approved SEC concept policy explicitly classifies it as not estimable. Coverage is heterogeneous: market/liquidity fields approach the full panel, while interest coverage and several debt/profitability fields are narrower.

The first real run exposed a benchmark bug: security-specific missing sessions produced differing benchmark compounds. The corrected publication compounds one authenticated benchmark calendar per holding period. Its maximum cross-portfolio benchmark discrepancy is `8.33e-17`, numeric roundoff only. Descriptive factor returns, turnover, correlations, and significance diagnostics are available in the authenticated publication. They are not claims of causal or investable premia, particularly because approved net-cost materiality is unavailable.

## Phase 3 results

The authenticated Phase 3 publication is `asset-pricing-c0a72fae5349f1048e18557250da1927`. Each configured model covers 123 diagnostic portfolios. Mean adjusted R-squared is 0.063 for CAPM, 0.259 for Fama-French 3, 0.277 for Carhart 4, 0.301 for Fama-French 5, and 0.296 for the configured q-factor mapping. Mean monthly intercepts range from 0.00875 to 0.01187 across models. These intercepts are descriptive estimates on project-specific diagnostic portfolios; they are not proof of alpha, causal pricing, or deployable performance.

## Hypothesis assessment

- H1: `INCONCLUSIVE`. Gross characteristic diagnostics exist, but the hypothesis requires approved net-cost materiality and FDR conclusions.
- H2: `PARTIALLY_SUPPORTED`. Multifactor models have higher in-sample adjusted R-squared than CAPM, but stable economic and out-of-sample improvement is not established.
- H3: `INCONCLUSIVE`. Rolling estimates exist, but approved regime/break multiplicity conclusions were not completed.
- H4 and H5: `INCONCLUSIVE`. Phase 4 costs and mandate constraints remain open owner decisions.
- H6 and H7: `INCONCLUSIVE`. Phase 5 target, horizon, benchmark, feature families, and economic parent remain unset.

## Conclusion

The free/public-data architecture supports a broad, authenticated, bounded Phase 1 and real Phase 2–3 research. It does not support honest Phase 4 net economics or Phase 5 ML conclusions without additional owner approvals. This is a partial empirical completion with disclosed governance limitations, not CRSP/Compustat equivalence or a trading recommendation.
