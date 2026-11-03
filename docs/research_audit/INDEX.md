# Research audit and evidence index

Start with the [current working paper](../../outputs/audit/final_correction/FINAL_CANDIDATE_MANUSCRIPT.pdf), [current research results](../RESULTS.md), [methodology](../METHODOLOGY.md), and [limitations](../LIMITATIONS.md). The permanent [50-issue master tracker](MASTER_AUDIT_TRACKER.md) contains the full investigation record. The phases below document the evolution of the evidence; **historical figures are not interchangeable with the accepted corrected results**.

| Investigation | Main evidence | Purpose |
|---|---|---|
| Phase 1: source/financial integrity | [Validation report](../../outputs/audit/phase1/PHASE1_FINANCIAL_DATA_VALIDATION.md) | Drawdown, incomplete constituent histories and provenance limitations |
| Phase 2: pricing diagnosis | [Asset-pricing validation](../../outputs/audit/phase2/PHASE2_ASSET_PRICING_VALIDATION.md) | Reproduced historical regressions and identified return-horizon mismatch |
| Phase 2B: corrected factor/pricing publication | [Empirical correction](../../outputs/audit/phase2b/PHASE2B_EMPIRICAL_CORRECTION_REPORT.md) | Corrected holding intervals and versioned publication lineage |
| Phase 2C: independent regression checks | [Regression verification](../../outputs/audit/phase2c/PHASE2C_REGRESSION_VERIFICATION.md) | Independent QR regression checks and economic-dependence diagnostics |
| Phase 3: portfolio and ML | [Complete validation](../../outputs/audit/phase3/PHASE3_COMPLETE_VALIDATION.md) | Corrected portfolio/ML outputs, costs and chronological evaluation |
| Phase 4: paper reconciliation | [Manuscript validation](../../outputs/audit/phase4/PHASE4_MANUSCRIPT_VALIDATION.md) | Claim-by-claim manuscript mapping and qualified findings |
| Final candidate correction | [Final correction report](../../outputs/audit/final_correction/FINAL_CORRECTION_REPORT.md) | Documentation/format corrections and accepted manuscript provenance |
| Repository integration | [Final release review](../../outputs/audit/final_release/FINAL_RELEASE_REVIEW.md), [CI evidence](../../outputs/audit/final_release/FINAL_TEST_AND_CI_RESULTS.txt) | Lockfile/security, release checks and GitHub integration |

## How to interpret the archive

- **Current empirical authority:** [accepted Phase 3 results](../../outputs/audit/phase3/PHASE3_COMPLETE_VALIDATION.md) and the corrected publication IDs in its source manifest. Model-fit details are supported by [Phase 2C](../../outputs/audit/phase2c/PHASE2C_REGRESSION_VERIFICATION.md).
- **Historical originals:** the original manuscript and early phase results are retained to document correction history, not as competing current numerical claims.
- **Software evidence:** passing tests and source hashes establish tested behavior and recorded lineage, not full historical market coverage, causal validation, actual trade fills, or directly executable sleeve costs.
- **Reproduction boundary:** raw third-party evidence and large frozen inputs are not fully distributed publicly; see [reproducibility](../REPRODUCIBILITY.md).
- **Author review:** [M1/M2/R6 remain pending](../../outputs/audit/final_correction/DEFERRED_AUTHOR_REVIEW.md); no historical author declaration is independently certified here.
- **Release status:** PR [#9](https://github.com/amitdudi04/institutional-multi-factor-asset-pricing-platform/pull/9) and documentation PR [#10](https://github.com/amitdudi04/institutional-multi-factor-asset-pricing-platform/pull/10) were merged; [final main CI](https://github.com/amitdudi04/institutional-multi-factor-asset-pricing-platform/actions/runs/41489336229) passed on 2 November 2026. Live GitHub status supersedes any historical checkpoint in archived reports.

This index is navigation only. It does not modify the immutable audit files, original data, empirical publications or their identifiers.
