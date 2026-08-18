# Final Empirical System Architecture

The empirical path is a connected immutable chain:

```text
HF market + Alpha lifecycle + SEC submissions/Company Facts/tagged covers
  -> ignored immutable source cache and 822-row screening matrix
  -> persisted security and issuer/listing authorities
  -> authenticated factor_market_input + factor_fundamental_input
  -> authenticated 48-factor publication and diagnostic portfolios
  -> authenticated five-family asset-pricing publication
  -> authenticated FastAPI/report/dashboard delivery
```

Identity is listing-level and effective-dated. SEC issuer facts reach a security only through a singular persisted issuer/listing mapping. Share observations are filing-time and are attached only after availability. Accepted intervals begin no earlier than exact tagged filing anchors and, where necessary, after the last detected material share-basis jump.

Research reads authenticate checksums, manifests, configuration identity, Git identity, lineage, and lifecycle state. Raw evidence and generated Parquet/report artifacts are ignored by Git. The detailed candidate matrix is runtime evidence; versioned documentation contains aggregates only.

Phase 4 and Phase 5 software remain implemented but have no real publication in this run because their approved empirical configuration is incomplete. Delivery surfaces expose authenticated real Phase 1–3 evidence and explicit empty states for absent portfolio/ML publications.
