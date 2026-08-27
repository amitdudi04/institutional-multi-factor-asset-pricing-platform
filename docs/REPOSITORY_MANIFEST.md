# Repository Manifest

This repository contains the public software, configuration, tests, methodology, and selected research outputs for the Institutional Multi-Factor Asset Pricing & Portfolio Analytics Platform.

| Path | Purpose |
|---|---|
| `src/` | Python package implementing governed data access, factor construction, asset-pricing models, portfolio and risk analytics, machine learning, and delivery services. |
| `config/` | Versioned YAML configuration for the frozen research and delivery designs. |
| `tests/` | Unit, connected-lifecycle, restart, tamper, security, CLI, API, dashboard, and deployment checks. |
| `docs/` | Durable governance, methodology, data, architecture, reproducibility, results, and user documentation. |
| `data/` | Public data-access guide. Raw and generated empirical data remain local and Git-ignored. |
| `examples/` | Small redistributable input templates. |
| `paper/` | Canonical public PDF of the final research manuscript. |
| `outputs/repository-cleanup/` | Reviewed public file classification and final packaging report only. Other runtime outputs remain ignored. |
| `.github/workflows/` | Continuous-integration quality gates. |

Top-level files provide package metadata, dependency locking, environment templates, security guidance, licensing, citation metadata, and contribution instructions.

The empirical release is frozen at tag `project-complete-public-data-v1` and commit `5a3e930665756fa7aaedeceb5f9ab90792bcf849`. Historical research tags are not moved by repository packaging.
