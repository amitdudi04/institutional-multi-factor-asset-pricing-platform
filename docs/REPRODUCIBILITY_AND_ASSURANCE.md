# Reproducibility and Assurance

## Frozen empirical identity

- Release: `project-complete-public-data-v1`
- Parallel release tag: `research-empirical-public-v1`
- Commit: `5a3e930665756fa7aaedeceb5f9ab90792bcf849`

Both historical tags resolve to the same empirical commit. Public-repository packaging occurs on later commits and does not modify the frozen factors, diagnostic portfolios, asset-pricing estimates, transaction costs, portfolio results, ML results, hypotheses, publication identifiers, or provenance.

## Reproduction boundary

The repository versions the implementation, strict configuration, dependency lock, tests, data contracts, source mappings, and research documentation. Provider source bytes, local databases, authenticated generated publications, reports, and model artifacts remain untracked. A lawful reproducer must acquire the approved sources described in `data/README.md`, follow the point-in-time and identity rules, and regenerate publications in dependency order.

## Research authentication

Research reads verify immutable manifests, checksums, configuration identity, code revision, lifecycle state, validation evidence, and upstream lineage. Missing or inconsistent evidence fails closed. Data and generated claims are not substituted with software fixtures.

## Software assurance

The retained test suite covers configuration, data contracts, immutable storage, authenticated read-time isolation, security identity, crash recovery, catalog rebuild, lifecycle transitions, factor construction, asset-pricing models, portfolio accounting, risk, temporally safe ML, API/dashboard delivery, deployment, restart, and tamper rejection.

The public packaging commit records its own post-cleanup test, coverage, lint, format, type-check, dependency-lock, secret, link, and runtime checks in `outputs/repository-cleanup/FINAL_REPOSITORY_CLEANUP_REPORT.md`.

## Evidence retained in Git history

Detailed historical phase audits, remediation logs, implementation reports, defect matrices, blocker reports, and version-specific closure records remain available through the immutable Git history but are removed from the current public tree. Their durable conclusions are represented by the final research paper, final assurance report, reproducibility guide, architecture, methodology documents, tests, and this index.

## Limits of assurance

Passing software checks establishes behavior of the released code under the tested conditions. It does not establish persistent alpha, causal factor mechanisms, proprietary-data equivalence, or future model performance. Reproducibility remains conditional on lawful access to upstream evidence and compatible provider availability.
