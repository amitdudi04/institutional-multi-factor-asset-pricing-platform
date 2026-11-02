# Dependency-security maintenance checkpoint

This entry supersedes the earlier dependency-blocked checkpoint **for the freshly tested local environment only**. PR10 and PR9 still require successful checks at their actual heads before merging. Their live merge records are the authority for eventual main integration.

Exact starting maintenance branch `maintenance/final-review-explanations`, commit `a2d4bb92faea6d7e351aade4944642f2c555697b`. Existing README and architecture corrections are preserved exactly. The dependency commit is the containing commit of this entry. No financial source/configuration/model/manuscript/output change.

## Resolver and compatibility

Ran `uv lock --upgrade-package certifi --upgrade-package pillow`. Certifi advanced but Pillow remained12.3.0: locked Streamlit1.61.1 requires `pillow<13`. PyPI metadata for1.62/1.63/1.64/1.65 retains that cap. The1.66family permits `pillow<14`; selected latest patch1.66.1. Then ran `uv lock --upgrade-package certifi --upgrade-package pillow --upgrade-package "streamlit==1.66.1"`. No dependency overrides, manual lock hashes, pyproject edits or advisory exclusions.

|Package|Old|Verified new|
|---|---|---|
|certifi|2026.7.22|2026.10.23|
|Pillow|12.3.0|13.0.0|
|Streamlit (necessary Pillow constraint update)|1.61.1|1.66.1|

Resolver removed four now-unused Streamlit dependencies: blinker1.9.0,httptools0.8.0,tenacity9.1.4,toml0.10.2. No other retained package record changed. NumPy,pandas,SciPy,scikit-learn,statsmodels,XGBoost,SHAP,PyArrow and other numerical packages remain identical. The new lock has92 platform-universal package records rather than96; local installed environment has88distributions including the editable project. Removed modules have no direct imports in project source/tests.

Project `requires-python >=3.11` unchanged. Certifi metadata requires>=3.7;Pillow13 andStreamlit1.66.1 require>=3.11 and supply compatible metadata/wheels. Universal uv resolution, `uv lock --check` and `uv pip check` pass. Metadata requirements accept3.11–3.15; full local runtime validation is Python3.12.13 on Windows, not a claim of full tests on every Python version. Linux/container compatibility is additionally gated by existing CI. Full source/package metadata: [certifi](https://pypi.org/pypi/certifi/2026.10.23/json), [Pillow](https://pypi.org/pypi/pillow/13.0.0/json), [old Streamlit cap](https://pypi.org/pypi/streamlit/1.61.1/json), [selected Streamlit](https://pypi.org/pypi/streamlit/1.66.1/json).

## Fresh test and advisory results

`uv sync --frozen --all-groups` PASS; no dependency-resolution incompatibilities. Fresh suite: **372 passed, 105 warnings in 443.06s (0:07:23)**. Coverage gate90% PASS; exact coverage is in the full output below. Ruff lint/format,mypy,configuration,delivery,imports/Pillow smoke,lock and installed dependency consistency all PASS. Full existing372-test suite executed once for this maintenance environment with an external warning recorder, which changes no warning filters or source/tests.

`uvx pip-audit --path .venv/Lib/site-packages --skip-editable --format json --output ../dependency_maintenance/pip_audit.json`: exit0, **no known vulnerabilities**,87third-party distributions audited; only the editable project skipped. All selected certifi/Pillow/Streamlit entries have empty vulnerability arrays. Their version-specific PyPI advisory arrays are also empty. This closes the reported advisories at the current database snapshot, not a guarantee against future discoveries. The previous41finding rows were not41unique advisories; its duplicate certifi entry is retained in historical evidence.

Lock SHA256 `ec5d9cbce46ebaf16cf1c8b4b095893c8318ef1831b355d983895cd7bf6bbd86`. Local audit JSON SHA256 `0be930b40b6d52ea7b6dbfc9865aa5aa90968b58f8cf6b975a71d537430a8ed0`; complete package/advisory receipt is embedded in the validation text. No financial experiments, original input downloads, empirical refits or publication regeneration occurred. Accepted financial outputs remain bound to their historical source/environment identities; this dependency-maintenance environment is not relabeled as their original vintage.

## All105warnings reviewed

|Warning|Count|Assessment|Action in this pass|
|---|---:|---|---|
|scipy.stats.ConstantInputWarning via pandas nanops|102|Expected undefined rank correlation for constant predictions/small synthetic test slices; 98 in ML tests and4 in the connected-platform fixture. Baseline/undefined-IC cases remain explicit; not105 statistical model failures.|Retained; no global suppression or manufactured finite IC.|
|sklearn UserWarning: minority class has4 or3 members versus5 splits|2|Both from the existing small synthetic sigmoid-calibration test, which verifies validation-only calibration and bounded probabilities. Low-support fixture behavior, not a production sample-size assurance.|Disclose; real classification use must check class support. No change to models/config or fixture in this security-only pass.|
|StarletteDeprecationWarning: httpx TestClient path deprecated|1|Actionable future test-client dependency migration. Pre-existing; FastAPI/Starlette/httpx records are unchanged by this update.|Record follow-up outside certifi/Pillow scope; do not add httpx2 or suppress warnings.|

All105 recorded warning events were counted by category/message and test node, not dismissed as one generic category. Existing undefined-correlation behavior, tiny classification fixtures and an actionable deprecation are distinguished. No global suppression/filter change or test weakening. Existing `ml/evaluation.py::_correlation` preserves unavailable constant IC; the pandas diagnostic warning path is retained.

## Scope and merge gates

Changes from `a2d4bb92faea6d7e351aade4944642f2c555697b` are restricted to `uv.lock` and append-only maintenance receipts in `FINAL_RELEASE_REVIEW.md`, `FINAL_TEST_AND_CI_RESULTS.txt`, `FINAL_MERGE_READINESS.md`. README,docs/ARCHITECTURE,pyproject,source,tests,configurations,50-IDtracker,manuscript and all other prior evidence/publications are unchanged. R5 stays resolved;M1/M2/R6 pending personal author confirmation.

PR10 →release branch only after final-head validate/docker and review gates pass. Then revalidate PR9 at the updated release head before normal merge to main. No forced merge, squash of phase history, branch deletion, new release/tag or SSRN submission. Actual merge SHAs and final CI are recorded on the live PRs and controlled final delivery after they exist.

---

## Historical release checkpoint (preserved)

# Final repository release review

This is the committed **pre-merge checkpoint**, not a claim that a pending PR has merged. Final branch SHA is the containing release-preparation commit. The [PR9 merge record](https://github.com/amitdudi04/institutional-multi-factor-asset-pricing-platform/pull/9) gives the actual final outcome, merge SHA and checks; the final controlled delivery report records post-merge verification without rewriting this historical checkpoint. A commit cannot contain its own SHA or its future GitHub merge SHA.

- Accepted source branch: `research/institutional-final-documentation-corrections`.
- Exact accepted source: `028dfd9cd18bcd6ef8114d829cc789d5bffacc61`.
- Release branch: `release/institutional-research-finalization`; direct parent is the accepted source.
- Refreshed target main before work: `4e7fbdc380b8042db72e9c628260f60077a205ef`; unchanged from the user-recorded baseline; main is an ancestor of the accepted lineage, with no divergence/conflict at this checkpoint.
- Numerical authority: `f22f5cbe365e98c8d5fef6b5308ff765703df173`.
- PR: [Finalize validated institutional multi-factor research and documentation](https://github.com/amitdudi04/institutional-multi-factor-asset-pricing-platform/pull/9).
- Classification at this checkpoint: FINAL_REPOSITORY_PR_READY — merge remains gated on final-head CI and current review status.

## Minimal changes

`README.md`: add direct final-paper, pending-author, permanent-tracker and audit/release navigation; point to fresh release validation. In README and `docs/RESULTS.md`, `docs/METHODOLOGY.md`, `docs/DATA_AND_SOURCES.md`, `docs/LIMITATIONS.md`, `docs/REPRODUCIBILITY.md`, replace now-transitional “unmerged main” statements with exact accepted-documentation SHA links that remain true before and after integration. REPRODUCIBILITY's separate unmerged-lineage sentence is likewise corrected. No numerical table or economic interpretation changed. `docs/SOFTWARE_USAGE.md` already matches CLI/API behavior and is untouched. Six edited documentation files plus exactly these five new release-evidence files; no cleanup deletion or relocation.

The README already explains the integrated workflow, internal pricing, eight allocation methods, costs, chronological ML and mixed/negative findings. Its authentic title and substantive structure are retained. The new paper/audit section supplies the previously missing direct reviewer route. No faculty grade, institutional endorsement or admissions probability is asserted.

## Source, result and history integrity

One source-authority pass authenticated final candidate PDF/controlled DOCX and final-correction evidence, seven Phase3 bound evidence hashes, 32 final portfolio/ML pointer/manifest pairs and 540 cached original-source size/mtime guards. No full SEC ingestion, factor-return rebuild, regression rerun, model retraining, portfolio experiment or bootstrap was performed. The unchanged PDF SHA256 is `ad558e75af0546ef6cfe417514d9a0d83fc556012f77227ac5c1e0a897476b52`. The paper remains 26 pages/25 tables/6 figures/26 editable equations; its original DOCX is controlled locally and no public DOCX link was invented.

The accepted factor identity is `factor-4ddee9ac6fb45cedfd62a2cc68676b58`; primary pricing `asset-pricing-d60bee7310b34976c80372a0f0f29e21`; supplementary pricing `asset-pricing-8c2396179c4b509796b2cab043ec31d2`. All 24 final portfolio and eight ML authorities, actual parents and their hashes remain in the [accepted Phase3 manifest](https://github.com/amitdudi04/institutional-multi-factor-asset-pricing-platform/blob/f22f5cbe365e98c8d5fef6b5308ff765703df173/outputs/audit/phase3/PHASE3_SOURCE_MANIFEST.json). The final-correction checksum manifest's documentation entries bind snapshot028dfd9, not newly edited navigation text; validate that historical snapshot with git show rather than overwrite its accepted hashes.

All seven phase tips and accepted028dfd9 are ancestors. Compared with accepted028dfd9, src/config/tests/scripts/data and all prior audit paths have zero changed bytes. No branch/tag/history is deleted or rewritten; no force-push. Integration brings earlier approved financial corrections to old main without cherry-picking only documentation. Permanent tracker bytes and all50IDs remain unchanged; R5 resolved, R6 unchecked. Raw vendor/model bundles remain private and licensing boundaries unchanged. No committed credential was found in the tracked example configuration; dependency security is gated by the existing CI audit.

## Inventory and navigation

One Git-tracked baseline inventory: 240 files, 27,412,058 bytes; categories {"AUDIT_EVIDENCE": 51, "CURRENT_AUTHORITATIVE": 9, "HISTORICAL_IMMUTABLE": 1, "OPTIONAL_SUPPORTING_DOCUMENTATION": 11, "SOURCE_OR_TEST": 168}. No `paper/` or `results/` tree exists in the accepted tracked baseline. GitHub repository size was8197KiB; no GitHub Releases existed. Existing original Git tags are retained. The inventory excludes ignored local datasets, runtime caches and virtual environments; it does not imply they are public. Five new focused evidence files are additions outside that baseline inventory.

Largest tracked files: outputs/audit/phase2b/PHASE2B_FACTOR_HOLDING_AUDIT.csv (11947292 bytes), outputs/audit/phase2b/PHASE2B_FACTOR_RECONCILIATION.csv (2217470 bytes), outputs/audit/phase2c/PHASE2C_NUMERICAL_DIFFERENCES.csv (1718232 bytes), outputs/audit/phase2c/PHASE2C_PORTFOLIO_LEVEL_CHECKS.csv (1111813 bytes), outputs/audit/phase2/PHASE2_ASSET_PRICING_DIAGNOSTICS.csv (1088279 bytes). These are accepted evidence, not candidates for deletion solely due to size. The README links and explicit historical labels solve navigation without moving immutable material. No redundant generated file or broken pointer required removal; .gitignore/.gitattributes remain unchanged.

## Documentation and technical verification

All 129 recorded link/document/value checks PASS: relative links, exact Git-pinned paths, six unique live external URLs, five matched-pricing rows, 24 scenario IDs/cumulative values, eight ML IC/interval families, count denominators and interpretation review. Existing178-row final-correction claim evidence was authenticated and reused, not rebuilt. Pricing R²/negative per-cycle alpha, geometric annualization/interval cash, L1 fee units,31cycles,27632/89/15/7286 and undefined constant IC remain consistent. No current table was overwritten with historical SSRN metrics.

Fresh local suite: ================ 372 passed, 105 warnings in 445.09s (0:07:25) ================. Local seven-command release sequence PASS. Coverage output:

```text
Name                                                                      Stmts   Miss Branch BrPart  Cover
-----------------------------------------------------------------------------------------------------------
src\institutional_factor_platform\__init__.py                                 6      2      0      0    67%
src\institutional_factor_platform\api\__init__.py                             2      0      0      0   100%
src\institutional_factor_platform\api\app.py                                126      3     12      1    97%
src\institutional_factor_platform\api\middleware.py                          82      3     28      3    95%
src\institutional_factor_platform\asset_pricing\__init__.py                   2      0      0      0   100%
src\institutional_factor_platform\asset_pricing\config.py                    54      0     14      0   100%
src\institutional_factor_platform\asset_pricing\inputs.py                    92      3     38      4    95%
src\institutional_factor_platform\asset_pricing\models.py                    22      0      8      0   100%
src\institutional_factor_platform\asset_pricing\service.py                  128     11     22      2    91%
src\institutional_factor_platform\backtest\__init__.py                        2      0      0      0   100%
src\institutional_factor_platform\backtest\costs.py                          25      2      8      2    88%
src\institutional_factor_platform\backtest\engine.py                         48      3     16      3    91%
src\institutional_factor_platform\cli.py                                    365     46    124     15    85%
src\institutional_factor_platform\configuration.py                           37      1      8      0    98%
src\institutional_factor_platform\constraints\__init__.py                     2      0      0      0   100%
src\institutional_factor_platform\constraints\models.py                      63      1     44      2    97%
src\institutional_factor_platform\dashboard\__init__.py                       2      0      0      0   100%
src\institutional_factor_platform\dashboard\app.py                           85      4     22      3    93%
src\institutional_factor_platform\dashboard\client.py                        53      7     18      4    79%
src\institutional_factor_platform\dashboard\launcher.py                      21      0      4      1    96%
src\institutional_factor_platform\dashboard\presentation.py                  35      0     10      0   100%
src\institutional_factor_platform\data\__init__.py                            0      0      0      0   100%
src\institutional_factor_platform\data\access.py                            143      9     30      4    92%
src\institutional_factor_platform\data\bound.py                              17      0      6      0   100%
src\institutional_factor_platform\data\calendar.py                           11      0      0      0   100%
src\institutional_factor_platform\data\config.py                            209      8     40     10    93%
src\institutional_factor_platform\data\contracts.py                          32      2      2      0    94%
src\institutional_factor_platform\data\domain.py                            265     18     46     15    88%
src\institutional_factor_platform\data\evidence.py                           48      5      8      0    91%
src\institutional_factor_platform\data\lineage.py                           244      0     66      0   100%
src\institutional_factor_platform\data\manifests.py                         166      6     30      6    94%
src\institutional_factor_platform\data\sec_concepts.py                       24      0      2      0   100%
src\institutional_factor_platform\data\sec_listing.py                       106      8     40      8    89%
src\institutional_factor_platform\data\sec_projection.py                    207     11    102     14    92%
src\institutional_factor_platform\data\security_master.py                   180      5     66      4    96%
src\institutional_factor_platform\data\services.py                          376     38    114     21    86%
src\institutional_factor_platform\data\sources\__init__.py                    0      0      0      0   100%
src\institutional_factor_platform\data\sources\alpha_vantage.py              53      5     16      5    86%
src\institutional_factor_platform\data\sources\base.py                       69      3     10      2    94%
src\institutional_factor_platform\data\sources\fred.py                       41      6     12      1    83%
src\institutional_factor_platform\data\sources\french.py                     50      6     16      6    82%
src\institutional_factor_platform\data\sources\hf_data_library.py            98     19     34     13    76%
src\institutional_factor_platform\data\sources\owner_supplied.py             97     10     44      7    87%
src\institutional_factor_platform\data\sources\sec_edgar.py                  69     13     24      6    80%
src\institutional_factor_platform\data\sources\sec_inline_xbrl.py           183     14     60     12    89%
src\institutional_factor_platform\data\sources\sec_legacy_xbrl.py           170     22     66     16    84%
src\institutional_factor_platform\data\sources\sec_submissions.py           111     17     32     10    81%
src\institutional_factor_platform\data\sources\yahoo.py                      60      7     18      3    87%
src\institutional_factor_platform\data\storage.py                           458     49    168     33    87%
src\institutional_factor_platform\data\validation.py                        180      7     80     11    93%
src\institutional_factor_platform\delivery\__init__.py                        2      0      0      0   100%
src\institutional_factor_platform\delivery\catalog.py                       132      3     50      3    97%
src\institutional_factor_platform\delivery\config.py                        101      1     14      0    99%
src\institutional_factor_platform\delivery\provenance.py                     24      2      4      0    93%
src\institutional_factor_platform\delivery\reporting.py                     110      9     26      3    91%
src\institutional_factor_platform\delivery\schemas.py                        33      0      0      0   100%
src\institutional_factor_platform\delivery\service.py                        31      0      0      0   100%
src\institutional_factor_platform\diagnostics\__init__.py                     2      0      0      0   100%
src\institutional_factor_platform\diagnostics\regression.py                  17      0      0      0   100%
src\institutional_factor_platform\exceptions.py                              20      0      0      0   100%
src\institutional_factor_platform\factors\__init__.py                         3      0      0      0   100%
src\institutional_factor_platform\factors\config.py                          83      4     10      4    91%
src\institutional_factor_platform\factors\contracts.py                        8      0      0      0   100%
src\institutional_factor_platform\factors\definitions.py                     89      0      8      0   100%
src\institutional_factor_platform\factors\diagnostics.py                     48      1     14      1    97%
src\institutional_factor_platform\factors\holding.py                         62      1     24      1    98%
src\institutional_factor_platform\factors\portfolio.py                       69      4     28      4    92%
src\institutional_factor_platform\factors\preprocessing.py                   44      1     20      1    97%
src\institutional_factor_platform\factors\service.py                        189     10     42      6    93%
src\institutional_factor_platform\factors\storage.py                        194     12     36     10    90%
src\institutional_factor_platform\factors\temporal.py                       102      5     56      4    94%
src\institutional_factor_platform\factors\validation.py                      60      1     28      1    98%
src\institutional_factor_platform\logging.py                                 20      1      6      1    92%
src\institutional_factor_platform\ml\__init__.py                              2      0      0      0   100%
src\institutional_factor_platform\ml\config.py                              115      2     12      2    97%
src\institutional_factor_platform\ml\contracts.py                           121      0      4      0   100%
src\institutional_factor_platform\ml\economic.py                             33      6     14      6    74%
src\institutional_factor_platform\ml\evaluation.py                           67      2     24      2    96%
src\institutional_factor_platform\ml\features.py                             57      2     20      2    95%
src\institutional_factor_platform\ml\models.py                              103      6     44      6    92%
src\institutional_factor_platform\ml\preprocessing.py                        78      6     36      7    89%
src\institutional_factor_platform\ml\publication.py                         164     16     50     11    86%
src\institutional_factor_platform\ml\service.py                             295     20     72     16    90%
src\institutional_factor_platform\ml\splits.py                               68      4     22      6    89%
src\institutional_factor_platform\ml\targets.py                              98      8     56      8    90%
src\institutional_factor_platform\ml\validation.py                          113      9     38      7    89%
src\institutional_factor_platform\model_validation\__init__.py                2      0      0      0   100%
src\institutional_factor_platform\model_validation\inputs.py                 29      2     14      2    91%
src\institutional_factor_platform\numeric.py                                  3      0      0      0   100%
src\institutional_factor_platform\observability\__init__.py                   2      0      0      0   100%
src\institutional_factor_platform\observability\logging.py                   10      0      0      0   100%
src\institutional_factor_platform\observability\metrics.py                   15      0      0      0   100%
src\institutional_factor_platform\optimization\__init__.py                    2      0      0      0   100%
src\institutional_factor_platform\optimization\black_litterman.py            26      1      4      1    93%
src\institutional_factor_platform\optimization\covariance.py                 40      3     18      3    90%
src\institutional_factor_platform\optimization\engine.py                    149     19     56     14    83%
src\institutional_factor_platform\optimization\hrp.py                        32      0      6      0   100%
src\institutional_factor_platform\performance\__init__.py                     2      0      0      0   100%
src\institutional_factor_platform\performance\metrics.py                     13      1      6      1    89%
src\institutional_factor_platform\portfolio\__init__.py                       2      0      0      0   100%
src\institutional_factor_platform\portfolio\allocations.py                   11      0      4      0   100%
src\institutional_factor_platform\portfolio\config.py                        63      2      8      2    94%
src\institutional_factor_platform\portfolio\service.py                      185     23     46     15    84%
src\institutional_factor_platform\project.py                                 17      2      6      0    91%
src\institutional_factor_platform\regression\__init__.py                      2      0      0      0   100%
src\institutional_factor_platform\regression\engine.py                       88      2     32      2    97%
src\institutional_factor_platform\research_outputs\__init__.py                2      0      0      0   100%
src\institutional_factor_platform\research_outputs\portfolio_storage.py      88      6     20      6    89%
src\institutional_factor_platform\research_outputs\storage.py               130     16     30      9    83%
src\institutional_factor_platform\risk\__init__.py                            2      0      0      0   100%
src\institutional_factor_platform\risk\metrics.py                            79      3     18      3    94%
src\institutional_factor_platform\scenarios\__init__.py                       2      0      0      0   100%
src\institutional_factor_platform\scenarios\engine.py                        27      1      8      1    94%
src\institutional_factor_platform\statistical_tests\__init__.py               2      0      0      0   100%
src\institutional_factor_platform\statistical_tests\tests.py                 26      2      4      2    87%
-----------------------------------------------------------------------------------------------------------
TOTAL                                                                      8727    593   2546    420    91%
```

Full command outputs and timings are in `FINAL_TEST_AND_CI_RESULTS.txt`. The accepted historical372/90.62% numbers are not substituted for this fresh run. CI checkpoint: `{"state": "PENDING", "run": 41477348077, "source": "028dfd9cd18bcd6ef8114d829cc789d5bffacc61"}`. Final PR-head validate/docker success and no outstanding review gate are mandatory before the normal merge attempt. Actual post-merge main CI must also be inspected. Initial API checks found main unprotected, no applicable branch rules/rulesets and no requested reviewers; these are refreshed before merge, never bypassed.

## Older PR review

PR7 (`51ae02815b20c1c857d17b243023847b32ad2934`) and draft PR8 (`ce36c399c1e64686de25d3f5702e22cd13647b8b`) remain open. Neither head is an ancestor. Holding-period pricing/cash fixes are superseded by the accepted Phase2/3 implementations and authenticated published evidence. However, both contain different risk-diagnostic (Jensen/excess-return Sortino) and constant-score allocation changes not present in accepted code. PR8 also changes ROE mapping from earnings yield to accounting roe, whereas accepted research explicitly preserves the historical earnings-yield q-style specification. These are not all equivalent patches; do not assert full supersession or merge them independently.

Keep both PRs and source branches open for separate scope review. Their alternative changes are not adopted or represented as verified in this frozen release. Existing current portfolio tables omit the legacy beta/Sortino cells; the paper makes no neutral-all-universe constant-allocation claim. No new numerical contradiction in the accepted published headlines was established by this bounded review. This release does not claim to settle every alternative software enhancement proposed by old PRs.

## Active limitations and author status

Retain the source-selected/survivorship-prone universe; unverified dividend-inclusive adjustment vintage; incomplete exhaustive SEC acceptance/capture/share-class chronology; modeled closes and no authenticated live fills/forecast timestamps; internal shared/duplicate factor-test exposures;956singleton quantile-cycle rows;no official external-factor validation/full conventional GRS;omitted constituent execution/financing/capacity;31portfolio cycles/two-tail-observation risk estimates;15dependent ML folds/five adjacent overlaps;100 exploratory block resamples/multiplicity;one-session reset economics rather than continuous21session investment;missing original H1/H3 approvals. Earnings yield is not accounting ROE. Stable incremental after-cost ML investment value remains unestablished. These are disclosed constraints, not newly repaired empirical findings.

M1/M2/R6 remain AUTHOR_CONFIRMATION_REQUIRED. All existing author/declaration/manuscript bytes are preserved; no personal or independent-human approval is fabricated. The user's repository-integration authorization is distinct from manuscript submission or personal attestation. No SSRN/journal upload, release/tag creation or author-declaration edit is authorized or performed.

## Merge record and outstanding gates

At this committed checkpoint, PR9 is OPEN and no merge is claimed. Main remains `4e7fbdc380b8042db72e9c628260f60077a205ef`. Final branch is the commit containing this report. CI/review checks still apply to the final published head; test success alone is not a merge. The [live PR](https://github.com/amitdudi04/institutional-multi-factor-asset-pricing-platform/pull/9) is the permanent actual merge-status/merge-SHA record. Post-merge checks, if successful, compare actual main ancestry/source trees, all manuscript/evidence bytes, refs/tags, homepage links and main CI. If CI or review fails, leave PR open and classify the exact blocker. No completed research branch is deleted.
