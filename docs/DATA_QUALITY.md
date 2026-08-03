# Phase 1 Data Quality and Quarantine

## Status model

Findings use `INFO`, `WARNING`, `ERROR`, and `CRITICAL`. Dataset outcomes are `PASS`, `PASS_WITH_WARNINGS`, `FAIL`, and `QUARANTINED`. Any critical finding quarantines; errors fail publication; warnings remain visible but may publish. No score can override an error or critical finding.

## Validation dimensions

Common checks cover exact schema/type/nullability, primary-key uniqueness, non-empty success, provenance, date ordering, and deterministic status. Market checks add configured XNYS expected/observed coverage, listing boundaries, out-of-range dates, OHLC/volume/price/order/staleness/extreme-return rules without filling. FRED preserves missingness/frequency. French checks finite explicit-unit values. SEC blocks period, filing, date-level availability, and retrieval chronology violations. Mapping checks make ambiguity/conflict explicit.

## Quarantine

Invalid schema, duplicate keys, empty-success responses, checksum mismatch, impossible OHLC, bad dates, missing provenance, severe coverage mismatch, or identity conflict block promotion. Quarantine copies the immutable raw artifact and writes a reason/report under an ignored checksum-addressed path. It never registers a validated DuckDB dataset or deletes evidence. Reprocessing may use preserved raw bytes.

## Reports

Each finding carries stable rule/version, dataset/source/time, severity, affected count, representative keys where safe, message, and remediation where available. Results are deterministically ordered. Reports and manifest/lineage instances are generated ignored evidence, not dashboards or research conclusions.
