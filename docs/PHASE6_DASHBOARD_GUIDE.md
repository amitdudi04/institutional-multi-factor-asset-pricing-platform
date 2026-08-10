# Phase 6 Dashboard Guide

Start the API, then run:

```shell
uv run institutional-factor-platform serve-dashboard
```

The dashboard contains Platform Overview, Data and Lineage Explorer, Factor Research, Asset-Pricing Research, Portfolio Construction, Risk Analytics, Machine Learning, Validation and Audit, and Report Builder pages.

Every research page starts from authenticated API discovery and shows provenance before detail. Tables and charts are display transformations only. Units, validation status, configuration identity, Git identity, publication identity, and limitations remain visible. The ML page states that SHAP and feature importance are not causal.

When no empirical publication exists, the dashboard shows capabilities, validation status, documentation-oriented guidance, and an explicit empty state. It does not load test fixtures or fabricate KPIs, performance, charts, or recommendations. Streamlit inputs cannot select local files, DuckDB databases, Parquet paths, Python code, SQL, or report destinations.
