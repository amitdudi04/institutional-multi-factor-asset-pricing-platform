# Phase 1 Data Quality and Quarantine

## Status model

Findings use `INFO`, `WARNING`, `ERROR`, and `CRITICAL`. Dataset outcomes are `PASS`, `PASS_WITH_WARNINGS`, `FAIL`, and `QUARANTINED`. Any critical finding quarantines; errors fail publication; warnings remain visible but may publish. No score can override an error or critical finding.

## Validation dimensions

Common checks cover schema/type/nullability, primary-key uniqueness, non-empty success, provenance, date ordering, temporal integrity, coverage, and deterministic status. Market checks cover positive finite prices, OHLC relationships, volume, duplicates, ordering, and stale-price warnings. FRED preserves missing markers/frequency and prohibits interpolation. French checks identity, header/date/factor completeness, and explicit units. SEC checks CIK/entity/fact structure, numeric values, filing/period/availability order, taxonomy/unit/form/accession metadata. Security-master checks stable IDs, source identities, primary listings, common-stock/US/USD eligibility, and listing status/dates.

## Quarantine

Invalid schema, duplicate keys, empty-success responses, checksum mismatch, impossible OHLC, bad dates, missing provenance, severe coverage mismatch, or identity conflict block promotion. Quarantine copies the immutable raw artifact and writes a reason/report under an ignored checksum-addressed path. It never registers a validated DuckDB dataset or deletes evidence. Reprocessing may use preserved raw bytes.

## Reports

Each run writes JSON and Markdown reports with dataset/source/run/schema, requested/observed range, rows/entities, findings, final status, and quarantine location where applicable. Reports are generated evidence, are ignored by Git, and are not dashboards or research conclusions.
