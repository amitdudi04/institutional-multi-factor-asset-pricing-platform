# Phase 1 financial and data validation

Evaluated 1 November 2026 (Asia/Calcutta). Run: `institutional-phase1-2026-11-01`.

**PHASE1_BLOCKED_BY_SOURCE_EVIDENCE**

All twelve permitted issues were investigated: D1–D9, V1, P1 and P2. Two implementation defects were demonstrated with failing tests and corrected: P1 initial-NAV drawdown and D8 incomplete constituent holding evidence. Their historical numerical effects cannot be established from the supplied repository. Eleven issue records are `SOURCE_EVIDENCE_BLOCKED`; D9 is `NEEDS_REVIEW`. All twelve checkboxes remain unchecked because their full empirical acceptance criteria have not been met. The other 38 issues remain unassessed. No later research phase was executed.

## Baseline and preservation

- Repository: https://github.com/amitdudi04/institutional-multi-factor-asset-pricing-platform
- Verified live main and initial clean checkout: `4e7fbdc380b8042db72e9c628260f60077a205ef`.
- Working branch: `research/institutional-phase1-financial-audit`, created directly from verified main.
- Initial tracker commit: `ea2846d`; initial correction commit: `3b435f30b76a2537e8ff0395fcfde691323af8ea`; final code checkpoint: `ef339ab1a7805242e67284cd54fbcf23fae86da1` (preserves the formation calendar). Final evidence is identified by the commit containing this report, avoiding a circular self-commit reference.
- Main's baseline Actions run [37338079331](https://github.com/amitdudi04/institutional-multi-factor-asset-pricing-platform/actions/runs/37338079331) completed successfully. This is observed software CI, not proof of the empirical numbers.
- Open PR #7: `51ae02815b20c1c857d17b243023847b32ad2934`, latest listed run failed. Draft PR #8: `ce36c399c1e64686de25d3f5702e22cd13647b8b`, latest listed run passed. Neither is merged. Their period-alignment/risk changes were inspected as prior evidence; neither branch was merged or wholesale cherry-picked. In particular, the initial-NAV defect remains in both baseline and inspected #8 risk code.
- Both empirical tags peel to `5a3e930665756fa7aaedeceb5f9ab90792bcf849`. The source manifest preserves their historical document hashes and the observed branch/PR/CI inventory.
- Current main contains methodology, aggregate result descriptions, code, tests and configuration. Its `data/` has access notes only. No frozen market/fundamental panels, screening decisions, empirical manifests, transactions or net-return paths are present. No release assets were returned by the GitHub releases endpoint.
- A historical Markdown research paper is available at `project-complete-public-data-v1:docs/FINAL_RESEARCH_PAPER.md`; its Git bytes are hashed. A targeted reachable-history search also recovered two 30-page PDFs: `c778a12404596a1a936ec58ddba7750b8795a8c4:paper/Institutional_Multi_Factor_Asset_Pricing_Research_Paper.pdf` (SHA256 `ab9bbbbdd5ddef1b84c46667fd4f02f5ee717ac5178761f79e7c95a4cdad4251`) and its successor `868baa9dd2770f118c30706ed37f62451aae9f38:paper/An_Auditable_Public_Data_US_Equity_Research_Pipeline.pdf` (SHA256 `2ea1a0767030e8693a91695940795996329302e898ac47163b3b395672e70a64`). The successor was removed in `4a419f7`. Relevant Phase 1 pages were text-inspected; this is not the later manuscript visual audit. Phase 1 claim pages 7–8, 13–15 and 23–25 have matching extracted text in both PDFs. No editable DOCX/TeX/bibliography source was found in reachable history. Identity with any separately posted external manuscript is not established.
- Historical engineering audits in the tag were inspected for unique evidence. They use earlier software-phase labels and include both failures and later remediation claims; no engineering verdict was silently reused as financial validation. They remain preserved in Git. Current main had no competing master tracker.
- Fresh clone had no uncommitted changes. Other owner checkouts were not modified or claimed clean. No original data, historical outputs, manuscript or README was edited. Audit outputs are explicitly added despite the existing generated-output ignore rule; that rule is not weakened for third-party data.

## What the evidence establishes

### P1

`risk/metrics.py::drawdown` formerly computed `W_t / cummax(W)_t - 1`, beginning with the first post-return wealth. It now computes `W_t / max(1, W_1, ..., W_t) - 1`, preserving the original return index. Initial capital is a running peak even if the first return loses money. `maximum_drawdown` and `risk_summary` use this function, so derived drawdown and Calmar can change on affected paths.

| Synthetic path | Original MDD | Corrected/reference MDD | Change, percentage points |
|---|---:|---:|---:|
| −20%, +10% | 0% | −20% | −20 |
| −10%, −10%, −10% | −19% | −27.1% | −8.1 |
| −20%, +25%, −10% | −10% | −20% | −10 |
| −2%, −2% | −2% | −3.96% | −1.96 |
| +2%, +2% | 0% | 0% | 0 |
| 0%, 0% | 0% | 0% | 0 |
| +10%, −20%, +30% | −20% | −20% | 0 |

These are independent scalar NAV calculations, not empirical portfolio results. Eight separate historical rows in the reconciliation CSV retain the reported MDDs from PDF Table 9 (p13) and Table 11 (p15): equal weight −8.57%, minimum variance −6.69%, mean variance −17.81%, maximum Sharpe −7.51%, maximum diversification −5.43%, risk parity −8.33%, hierarchical risk parity −8.13%, CVaR −8.55%. Their original return paths are unavailable and corrected values remain blank. The reported maximum-diversification −5.43% remains **unverified**, and this audit does **not** conclude it is wrong. If the historical worst drawdown occurred after an adequately high peak, its MDD might remain unchanged. Reconciliation requires genuine frozen BASE net-return paths and original manifests for all eight methods.

### P2

`TransactionCostModel.estimate` returns `turnover = sum(abs(trade_weight))`, the absolute traded-weight L1, and charges:

`fee/NAV = L1 × (commission_bps + full_quoted_spread_bps/2 + slippage_bps)/10000 + nonlinear_impact`.

The current BASE configuration has commission 0, quoted spread 10 bps, slippage 5 bps, nonlinear impact 0. The charged half-spread is 5 bps. The other 5 bps bundles the documented 2-bps slippage and 3-bps fixed-impact allowance. This allowance is a flat assumption, not estimated nonlinear market impact. Those components are not separately estimated in the engine.

PDF Table 8 (p13) specifies spread/slippage/fixed allowance as LOW 2/1/2, BASE 5/2/3 and HIGH 10/4/6 bps, with zero commissions. Interpreting the table's spread component as the charged half-spread gives engine `(spread_bps, slippage_bps)` parameters `(4,3)`, `(10,5)` and `(20,10)`, respectively. The numerical evidence script independently checks these exact documentary component sums for buys, sells, switches and drift trades. The actual frozen LOW/HIGH runtime snapshots remain unavailable; consistency of this interpretation is not proof those configurations produced the archived results.

| Modeled per-side rate | Buy/deploy L1=1 | Full A→B switch L1=2 | Drift trades −0.1/+0.1, L1=0.2 |
|---|---:|---:|---:|
| 5 bps | 5 bps NAV | 10 bps NAV | 1 bp NAV |
| 10 bps | 10 bps NAV | 20 bps NAV | 2 bps NAV |
| 20 bps | 20 bps NAV | 40 bps NAV | 4 bps NAV |

For a fully invested self-financing rebalance, half-L1 is one-way turnover. A full switch therefore has half-L1=1 but two traded sides. Initial cash deployment is different: L1=1 buys a whole NAV; half-L1=0.5 is not its purchase notional. A sale has the same modeled per-side fee as a buy. No costs were halved or parameters retuned.

Independent tests sum fees asset by asset and compare to the aggregate fee for all three rates. A two-asset backtest verifies initial deployment, price-driven drift to 11/21 and 10/21, rebalance L1=1/21, transaction-ledger sums, and the engine's explicit `net_return = gross_return - fee` convention. The reference net returns are 0.049 and −0.001/21. These tests validate the implemented additive fee convention; they do not establish measured execution realism or authenticate historical LOW/HIGH configurations. Original trade-by-trade ledger reconciliation remains blocked.

### D8

The old implementation compounded whatever returns survived per security and later inner-joined them to formation rows. A missing first session, early disappearance, wholly missing member or null return could therefore be accepted, change the realized horizon, or remove a formed holding. Its grouping by each security's realized end date could also split a formed quantile into differently dated rows.

The minimal correction fixes eligible membership at formation, then requires every formed security to have a unique, non-null return on every date in the supplied common benchmark holding calendar. Missing evidence raises `DataQualityError`; it is not filled with zero or a fabricated delisting return. The former benchmark-calendar fixture was made complete, and four new missing-evidence regressions demonstrate the failure before correction and the rejection afterward.

This is a fail-closed publication safeguard, not repaired historical data. It may block previously accepted runs. It cannot detect a session absent from the entire supplied market calendar, establish an unobserved terminal payment, or prove that the final sample end is a full scheduled month. A common truncated sample can still have a shorter-than-month interval; the actual formation/exit schedules must be examined before a new monthly series is accepted. Frozen membership and market evidence are required for empirical propagation. No corrected factor publication was manufactured.

<a name="d1"></a>
<a name="d6"></a>

### D1, D6

The historical Markdown paper reports 822 candidates, 487 admissions and 335 rejections. Its listed reasons sum to 335: attribution 114, splice 56, identity 68, shares 70, unresolved terminal event 16, split basis 7, asset type 2, venue/non-US 1 and fundamental projection 1. This checks documentary arithmetic only. Without security-level dispositions, dates, industries, delisting observations and accepted/rejected return histories, neither survivorship magnitude nor healthier-firm selection can be measured. The population must remain described as source-availability selected; missing comparisons are not zeros.

### D2

The HF adapter preserves `pitrading`/`iex` row tags and applies a 50% price-splice rejection threshold. Neither tag preservation nor this threshold demonstrates comparable consolidated/IEX volume. The implemented liquidity formulas use volume directly: turnover=`volume/shares`, dollar activity=`price*volume`, Amihud=`abs(return)/(price*volume)`. Matched frozen security rows around the claimed March 2022 boundary are absent, so structural jumps, exact source dates and factor sensitivities cannot be quantified. Current provider documentation covers IEX and cannot reconstruct the original earlier PiTrading vintage.

### D3

Configuration requires a minimum of three nonmissing cross-sectional raw values, and preprocessing returns missing scores below that threshold. Independent 1/2/3/4-security tests validate the configured behavior. The factor service checks whether any date ever meets the threshold, and the portfolio validator requires positive group counts; it does not impose a research standard larger than singleton terciles. PDF Table 4 (p8) reports 2018 minimum/median/mean/maximum breadth 1/4/3.7/4; 2019 4/14/17.8/46; 2020 46/333/295.5/357. These are documentary values, not independently recomputed breadth estimates. Appendix A's uniform date ranges and row counts cannot establish each factor's first valid observation. Per-factor earliest valid dates, quantile occupancy and later-period sensitivity remain source-blocked. No performance-selected threshold was introduced.

<a name="d4"></a>
<a name="d5"></a>

### D4, D5

Companyfacts stores filing-date end-of-UTC-day availability when exact acceptance is absent. SEC submissions preserves exact source timestamps when supplied; legacy/share projection handles accession and date context. Annual facts use filed observations and amendments remain later observations. Shares require exactly one authenticated listing, while appropriate issuer monetary facts may map to multiple listings. Effective-dated symbol and issuer/listing keys are distinct from CIK.

Existing synthetic tests for amendments, share classes, ticker/listing identity and future-share rejection were rerun. They establish code behaviors, not the authenticity of actual securities. The factor as-of join uses a UTC-day cutoff and permits same-day facts through that cutoff. It does not, by itself, prove availability strictly before an exchange-close decision. Original filing acceptance, amendment and execution records are required to establish next-session use. No specific real issuer is claimed validated without those records.

### D7

The SEC concept registry explicitly sets `net_equity_issuance` to `NOT_ESTIMABLE` pending a mutually exclusive issuance/repurchase policy. The characteristic is numerator/shareholder equity; missing numerator remains NaN. The independent fixture confirms this behavior. The 47-estimable count and zero observed issuance rows are consistent documentary claims, but the original factor diagnostics and concrete rejected SEC component examples are unavailable. The negative finding is retained, with no fabricated inputs or zero filling.

PDF Appendix A (p23) nevertheless lists 715,447 under an “Observations” heading even for non-estimable equity issuance. It gives the same count to all 48 factors, whereas Appendix C (p24) lists smaller nonmissing counts for book-to-market and momentum. The documentary identity `48 × 715,447 = 34,341,456` exactly matches the claimed long-form factor row total and supports a grid-row interpretation. This is an apparent row-domain versus valid-observation terminology problem, not proof of 715,447 observed issuance values or a fabricated calculation. It must be clarified during later manuscript reconciliation; the original factor diagnostics are still required to determine the exact count semantics.

### D9

`PHASE1_FACTOR_DEFINITION_INVENTORY.csv` lists all 48 stable IDs, formulas, units, inputs, signs and timing/window caveats. The registry has 48 unique names, but `rolling_market_beta`, `beta` and `rolling_beta` are assigned the same raw beta series. `beta` reverses the score direction; the other two do not. Thus unique registry names do not establish 48 independent economic exposures. Reciprocal book/price ratios and alternative risk measures can also be economically related; no unsupported independence count is substituted.

Independent reference tests verify leverage 30/100=0.3, turnover 100/1000=0.1, dollar volume 10×100=1000, range proxy (11−9)/10=0.2, daily Amihud and 12–1 momentum. The latter shifts by 21 sessions and compounds the preceding 231 returns. Rolling windows permit a 20-observation minimum, so warmup estimates can be shorter than their nominal horizons. This is disclosed rather than silently changing parameters. Full dated coverage and strict decision-time availability remain unverified. D9 stays `NEEDS_REVIEW`; no factor IDs are deleted or combined.

### V1

The provider's [dated errata](https://hfdatalibrary.com/pages/issues) reports an October 6, 2026 rebuild to a split-only basis, replacing a previously partly dividend-adjusted series. Its [documentation commit](https://huggingface.co/datasets/elkassabgi/hfdatalibrary/commit/a8ca2499e8ed104d7d56350fff81e5d3f8627321) warns against combining downloads across the change. This establishes a source-version risk, not the study's original bytes or its exact return basis.

The adapter copies `Close` into `adjusted_close`, records dividend and split fields as missing, and requests version `clean`; that name alone cannot prove total returns. No fresh vendor observations replaced historical evidence. Original retrieval metadata, hashes, raw archived files and corporate-action conventions remain required. Sensitivity cannot be quantified without legitimately paired frozen vintages.

## Validation and release gate

See `PHASE1_TEST_RESULTS.txt` for exact commands and observed outcomes. Initial regressions: 8 failed/16 passed. Corrected targeted tests: 88 passed; expanded independent tests: 29 passed. Full-suite outcome is recorded in the test evidence and final signoff below. These are software/reference tests, not an empirical replay of the research publication.

`PHASE1_SOURCE_MANIFEST.json` distinguishes exact Git-blob hashes from working-file hashes, records available documentary publication IDs and inventories missing empirical files explicitly. A publication name is not treated as an authenticated manifest or source hash. Reconciliation CSV rows distinguish synthetic calculations from unavailable historical observations.

The two code changes invalidate automatic reliance on prior downstream numerical claims. Once original inputs are restored, first authenticate their hashes and publication chain, then evaluate D8 coverage, regenerate only genuinely affected immutable outputs under new identities, and recompute the eight P1 paths and P2 ledgers. Do not start AP, remaining P or ML investigations until explicitly authorized. PR #7/#8 contain overlapping changes and must be reconciled during independent review; this branch does not imply their acceptance.

Before external claims are updated, the reviewer must receive the original screening and mapping stores, source/retrieval and SEC evidence, complete common-calendar returns, frozen factor memberships/outputs and eight strategy net/transaction paths. No source-evidence absence is represented as a successfully repaired calculation. Raw third-party data were not published. Main, both recovered historical PDF versions, the historical Markdown paper and their Git history remain unchanged. No external publication was edited; its exact posted identity remains unverified. README claims were not revised.


## Final Phase 1 signoff

- Full software gate: **330 passed, 115 warnings in 1444.39s (24m04s); 90.52% branch-aware coverage; pytest exit0; separate coverage report --fail-under=90 exit0**. Lint, formatting, strict type checks, lock verification, configuration/delivery checks and audit-integrity checks pass. Warnings and exact output are preserved in PHASE1_TEST_RESULTS.txt.
- Status: **PHASE1_BLOCKED_BY_SOURCE_EVIDENCE**. Investigated all 12 permitted issues; eleven source-blocked and D9 needs review; all remain unchecked. No historical metric is marked repaired.
- Corrected source checkpoint: `ef339ab1a7805242e67284cd54fbcf23fae86da1`, following initial correction `3b435f3`. Final report and evidence identity is the Git commit containing these files.
- Evidence set: the four requested phase outputs plus factor-definition inventory, numerical reproduction script and test evidence; the sole authoritative master tracker remains `docs/research_audit/MASTER_AUDIT_TRACKER.md`.
- Live main rechecked at `4e7fbdc380b8042db72e9c628260f60077a205ef`; no main, historical manuscript, data or README edit. No new remote CI success is inferred from this research-branch push.
- Independent review: **PENDING**. Upstream empirical dependency gate: **BLOCKED**. Stop here; no Phase2 work or manuscript rewrite authorized.
