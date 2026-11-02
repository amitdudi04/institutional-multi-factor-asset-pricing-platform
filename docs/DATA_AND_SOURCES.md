# Data and Sources

## Overview

Numerical authority: [accepted correction commit f22f5cb](https://github.com/amitdudi04/institutional-multi-factor-asset-pricing-platform/tree/f22f5cbe365e98c8d5fef6b5308ff765703df173/outputs/audit), with the [Phase 3 reconciliation](https://github.com/amitdudi04/institutional-multi-factor-asset-pricing-platform/tree/f22f5cbe365e98c8d5fef6b5308ff765703df173/outputs/audit/phase3/PHASE3_COMPLETE_VALIDATION.md) and [Phase 2C matched-sample checks](https://github.com/amitdudi04/institutional-multi-factor-asset-pricing-platform/tree/f22f5cbe365e98c8d5fef6b5308ff765703df173/outputs/audit/phase2c/PHASE2C_REGRESSION_VERIFICATION.md). The [accepted documentation and candidate manuscript](https://github.com/amitdudi04/institutional-multi-factor-asset-pricing-platform/tree/028dfd9cd18bcd6ef8114d829cc789d5bffacc61) preserve the interpretation of these results. Original releases are historical records.

The empirical study combines public or publicly accessible market, listing, filing, macro, factor, and benchmark evidence. The final research universe is selected by the intersection of available historical data and the project's identity and timing requirements.

## Sources

| Source | Research role | Main limitation |
|---|---|---|
| HF Data Library | Historical US-equity market data and initial candidate stock universe | Source-selected coverage; historical membership is not a complete market database; the PiTrading-to-IEX transition affects volume comparability |
| SEC EDGAR | CIK identity, filing history, XBRL fundamentals, shares, and filing-time evidence | Concept availability and reporting practice vary across issuers and time |
| Alpha Vantage LISTING_STATUS | Listing/lifecycle evidence during universe screening | Does not reconstruct every historical security absent from other sources |
| FRED DGS3MO | 3-month constant-maturity Treasury yield / risk-free reference | Frequency conversion and release timing must be handled explicitly |
| Kenneth French Data Library | Reference factor datasets and methodology comparison | Provider definitions are not automatically identical to project-specific characteristic portfolios |
| SPY | Broad investable US-equity benchmark proxy | Not a historical constituent-membership database |

## Final Research Panel

| Measure | Result |
|---|---:|
| Candidate stocks | 822 |
| Accepted | 487 |
| Rejected | 335 |
| Market observations | 715,447 |
| Fundamental observations | 37,273 |

Market observations span 2018-02-14 through 2026-08-04. Fundamental availability spans 2019-02-23 through 2026-08-15.

## Security Identity

Ticker symbols are not treated as permanent identifiers. The data layer maintains effective-dated listing and issuer mappings so that:

- ticker changes can be represented through time;
- issuer-level SEC data do not automatically collapse multiple share classes;
- current identifiers are not silently applied to earlier periods;
- ambiguous mappings are excluded from the research-ready panel.

CIK identifies an SEC registrant, not automatically a unique listed share class. Listing-level joins therefore require explicit mapping evidence.

## Filing Availability

Fundamentals use the information-availability date associated with the filing evidence. Fiscal-period end alone is not sufficient for a point-in-time join.

The intended rule keeps amendments as later observations rather than overwriting earlier information. Recorded UTC-day gates and representative authenticated cases do not establish exhaustive SEC acceptance/local-capture chronology, all original amendments or issuer/share-class attribution. D4 remains source-evidence blocked; see the accepted audit tracker and Phase 3 report.

## Shares and Share Classes

Shares outstanding are treated separately from monetary fundamentals. When SEC evidence cannot identify a unique listed share class or does not preserve the dimensional context needed for a defensible allocation, the related listing-level value is not inferred.

## Market Data

The market panel retains source provenance through the HF Data Library history. The project does not treat historical volume across the PiTrading/IEX source transition as perfectly comparable.

The universe is source-availability selected; pre-snapshot delisted names are not restored by screening. Returns are frozen provider-vintage adjusted-quote returns. Complete dividend-inclusive total-return comparability and historical adjustment vintage remain unverified (V1). Current vendor files or changed provider documentation are not substitutes for the authenticated original bytes. Modeled closes and retrospective outputs are not actual historical fills or timestamped live forecasts.

## Missing Data

Missing required evidence remains missing. The research pipeline does not convert unavailable accounting inputs into economically favorable zeros or silently substitute a different security, date, benchmark, or source.

This rule is why `equity_issuance` remains non-estimable in the final factor study.

## Data Rights and Repository Boundary

The repository contains code, configuration, tests, methodology, and aggregate research results. Raw provider files, local databases, generated Parquet datasets and fitted-model bundles remain private. Selected aggregate audit reports, manifests and the candidate PDF are public; the editable DOCX remains controlled local author delivery with a public checksum. Exact reproduction needs the same lawful original source bytes, not a present-day download.

The MIT License applies to original repository code and documentation. It does not override the terms of third-party data providers.

Exact empirical reproduction therefore requires lawful access to the same source material.

## SEC/XBRL Mapping

A concise technical description of the SEC concept and share-class mapping rules is available in [technical/SEC_XBRL_MAPPING.md](technical/SEC_XBRL_MAPPING.md).
