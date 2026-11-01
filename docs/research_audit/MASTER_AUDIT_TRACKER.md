# Institutional Multi-Factor Asset Pricing Platform — Master Audit and Phase Tracker

> **WORKING RESEARCH CONTROL DOCUMENT — NOT A CLAIM OF COMPLETED VALIDATION**  
> Source: attached 1 November 2026 professor audit. Repo: https://github.com/amitdudi04/institutional-multi-factor-asset-pricing-platform  
> This file catalogs **49 numbered A–E audit issues (D1–D9, AP1–AP10, P1–P12, ML1–ML10, R1–R8)** plus **V1** (provider-vintage issue). Each starts **unchecked / UNASSESSED** until Codex collects evidence. Earlier audit severities are hypotheses; they are not automatic proof that all publication metrics are wrong.

## Rules of engagement

1. **Git safety:** record current `main` SHA; create `research/institutional-phase1-financial-audit` from it. Later phases use separate branches chained from accepted prior phase commits. No edits to `main`, force-push, deleted branches, source-vintage replacement, manuscripts or old CSVs until final review/authorized merge.
2. **Immutability:** preserve original manuscript, frozen public research outputs, all original manifests, price data and configuration hashes. Corrected evidence gets a new version and traceable before/after records. Do not make historical paper numbers silently match new computations.
3. **One issue at a time:** check this file at the start; choose first unresolved issue whose dependencies are ready; search for existing verified evidence first; run only missing targeted diagnostics; write evidence artifacts; mark and commit completion; continue. Avoid reading entire codebase every run. Full final tests once per accepted phase, not after each issue.
4. **Status vocabulary:** `UNASSESSED`, `IN_PROGRESS`, `VERIFIED_CORRECT`, `CONFIRMED_ERROR_FIXED`, `RESEARCH_LIMITATION_DISCLOSED`, `SOURCE_EVIDENCE_BLOCKED`, `NEEDS_REVIEW`. A checked box means evidence and acceptance criteria have been recorded, **not necessarily that an inherent limitation was eliminated**. Blocked items stay unchecked unless the evidence limitation and manuscript-safe wording were specifically reviewed and approved; then use `RESEARCH_LIMITATION_DISCLOSED`, not `VERIFIED_CORRECT`.
5. **Evidence minimum:** include source paths and relevant functions/lines, exact original and corrected formula/units, independent reference calculation when numerical, dated run ID, git SHA, input/source hashes, tests, output file(s), scientific consequence and reviewer rationale. No unsubstantiated "fixed" claims.
6. **Fail-fast gates:** stop dependent stages for a genuine uncorrected lookahead leak, invalid NAV/cost accounting, mismatched publication hashes or unresolved changed principal outputs. Do not upgrade unresolved results to supported claims.
7. **Research integrity:** no fake factor signals, backfilled delisted prices, fabricated SEC evidence, invented shareholder classes, parameter tuning for improved Sharpe, manufactured significant p-values or misleading AI/author attestations.
8. **Scope:** the research question remains public-source US equity factors, point-in-time data, asset pricing, portfolios and ML. Additional experiments must directly answer a listed issue and have a written ex-ante rationale.

## Frozen historical claims requiring source-level reconciliation

| Claim | Historical reported value | Final verification required |
|---|---:|---|
| Candidate / accepted / rejected securities | 822 / 487 / 335 | Screening tables and rejection reasons |
| Daily market / PIT fundamental rows | 715,447 / 37,273 | Source and deduplication keys; availability |
| Configured / estimable factor definitions | 48 / 47 | Registry and authenticated factor outputs |
| Factor long-form rows | 34,341,456 | Output schema and hashes |
| Asset pricing model test assets | 123 | Constituents, dates, independence and model intersection |
| CAPM / FF3 / Carhart / FF5 / configured q mean adjusted R² | .063 / .259 / .277 / .301 / .296 | Independent OLS and matched samples |
| Minimum-variance volatility | 10.00% | Monthly net return path / frequency |
| Maximum-diversification MDD | −5.43% | **Initial NAV=1** computation |
| CVaR cumulative net return / Sharpe | 83.17% / 1.667 | Trades, fees, NAV, risk-free series and constraints |
| ML observations / months / completed folds | 27,640 / 91 / 17 | Authenticated chronological fold files |
| Software tests | 301 passing, 90.52% branch-aware coverage | Re-run on exact code+environment; not proof of empirical reproduction |

## Dependency map and phase gates

| Phase | Work | Must be complete before next phase |
|---|---|---|
| 0 | Snapshot main, inventory source/vintages, file hashes, existing output and test manifests; create branch | Baseline manifest and immutable source IDs |
| 1 | D1–D9, V1, **early P1/P2 financial blockers** | Verified data dates/conventions and reported NAV/cost effect; versioned corrections |
| 2 | AP1–AP10 | Five model family comparisons checked against factors and matched portfolio samples |
| 3 | Remaining P1–P12, ML1–ML10 | Eight portfolio result paths and all 17 ML folds reconciled |
| 4 | R1–R8 | Paper vs source traceability; empirical corrections frozen; author-only declarations separated |
| 5 | README + clean GitHub publication | Only approved outputs, no lost provenance, CI and documentation pass |

**Do not automatically start Phase 2 from this first Codex prompt.** First create/commit this living tracker, then carry out Phase 1 and return the evidence and updated tracker for independent review. Subsequent phases should use the same tracker without restarting the review.

## Completion checklist index

- **Phase 1 — Raw financial integrity, point-in-time data and provenance** — D1–D9, V1, plus early escalation of P1/P2
- **Phase 2 — Factors and five asset-pricing models** — AP1–AP10 and Phase 1 dependencies
- **Phase 3 — Eight portfolios and walk-forward ML** — P1–P12, ML1–ML10
- **Phase 4 — Manuscript/results reconciliation and publication integrity** — R1–R8
- **Phase 5 — Final README and repository publication** — Only after Phase 1–4 signoff

## Issue register and detailed instructions


### Phase 1 — Raw financial integrity, point-in-time data and provenance

#### [ ] D1 — The initial 822 securities come from a source-selected universe, not a reconstructed historical US equity universe. How severe is the survivorship bias?

- **Phase / severity from initial audit:** 1 / High; **status:** `SOURCE_EVIDENCE_BLOCKED`.
- **Why this matters / failure mode:** The initial 822 securities come from a source-selected universe, not a reconstructed historical US equity universe. How severe is the survivorship bias? A mismatch can change empirical interpretation or make a paper claim stronger than the underlying data support; do not presume a defect before examining the archived outputs.
- **Inspect first:** `data universe screening manifests; docs/DATA_AND_SOURCES.md`. Resolve these to actual paths on the checked-out commit; record function names/line ranges rather than assuming they are unchanged.
- **Detailed verification and candidate correction:** Compare acceptance/rejection by calendar year and delisting status; quantify source-selected coverage, the number of terminal-event exclusions and the sensitivity of factor findings to later, deeper-coverage years. Never call this a CRSP-like historical universe.
- **Initial audit requested:** Check delisted-firm coverage and period-specific selection.
- **Deliverable:** `outputs/audit/yearly_screening_and_lifecycle.csv` (or an equivalent, documented path); record source input hashes, exact calculations and explanatory caveats. **Never overwrite old frozen result artifacts.**
- **Acceptance gate:** A defensible selection-bias diagnostic is filed; if original rejects cannot be reconstructed, mark SOURCE_BLOCKED and qualify population claims.
- **Progress record:** owner `Codex`; result `SOURCE_EVIDENCE_BLOCKED`; baseline SHA `4e7fbdc380b8042db72e9c628260f60077a205ef`; code/evidence checkpoint `ef339ab`; tests `PHASE1_TEST_RESULTS.txt`; evidence `../../outputs/audit/phase1/PHASE1_FINANCIAL_DATA_VALIDATION.md#d1`; numerical change `no historical before/after available; see reconciliation CSV`; research-paper impact `Population claims must remain source-availability selected; no CRSP-like representativeness or bias-free estimate.`; independent reviewer `PENDING`.

#### [ ] D2 — The data provider switches from PiTrading consolidated evidence to IEX around March 2022. Does this distort liquidity factors?

- **Phase / severity from initial audit:** 1 / High; **status:** `SOURCE_EVIDENCE_BLOCKED`.
- **Why this matters / failure mode:** The data provider switches from PiTrading consolidated evidence to IEX around March 2022. Does this distort liquidity factors? A mismatch can change empirical interpretation or make a paper claim stronger than the underlying data support; do not presume a defect before examining the archived outputs.
- **Inspect first:** `data provenance; factor liquidity definitions; docs/DATA_AND_SOURCES.md`. Resolve these to actual paths on the checked-out commit; record function names/line ranges rather than assuming they are unchanged.
- **Detailed verification and candidate correction:** Identify the PiTrading→IEX boundary and compare matched securities, adjusted price/volume continuity, bid/ask or turnover proxies where available; do not misinterpret a change in venue coverage as changed market liquidity. Quantify before/after factor coverage and structural jumps using frozen data.
- **Initial audit requested:** Compare liquidity-factor behavior before and after the source break.
- **Deliverable:** `outputs/audit/source_transition_comparison.csv` (or an equivalent, documented path); record source input hashes, exact calculations and explanatory caveats. **Never overwrite old frozen result artifacts.**
- **Acceptance gate:** Demonstrate which factor conclusions remain comparable across the source break, or limit them to source-consistent periods.
- **Progress record:** owner `Codex`; result `SOURCE_EVIDENCE_BLOCKED`; baseline SHA `4e7fbdc380b8042db72e9c628260f60077a205ef`; code/evidence checkpoint `ef339ab`; tests `PHASE1_TEST_RESULTS.txt`; evidence `../../outputs/audit/phase1/PHASE1_FINANCIAL_DATA_VALIDATION.md#d2`; numerical change `no historical before/after available; see reconciliation CSV`; research-paper impact `Liquidity findings spanning source regimes require source-consistent sensitivity; March boundary not reauthenticated from original rows.`; independent reviewer `PENDING`.

#### [ ] D3 — The market panel has only 1–4 securities on some 2018 dates. Can meaningful cross-sectional factors be constructed then?

- **Phase / severity from initial audit:** 1 / High; **status:** `NEEDS_REVIEW`.
- **Why this matters / failure mode:** The market panel has only 1–4 securities on some 2018 dates. Can meaningful cross-sectional factors be constructed then? A mismatch can change empirical interpretation or make a paper claim stronger than the underlying data support; do not presume a defect before examining the archived outputs.
- **Inspect first:** `factor portfolios; factors/portfolio.py; factor preprocessing configuration`. Resolve these to actual paths on the checked-out commit; record function names/line ranges rather than assuming they are unchanged.
- **Detailed verification and candidate correction:** Compute each date’s eligible-security count, each factor’s formation-date breadth, quantile occupancy and earliest valid date. Compare early sparse years with 2020+; reject tiny or single-name quantiles if the declared formation standard requires it.
- **Initial audit requested:** Identify the first valid formation date for each factor and exclude inadequate breadth.
- **Deliverable:** `outputs/audit/factor_breadth_by_date.csv` (or an equivalent, documented path); record source input hashes, exact calculations and explanatory caveats. **Never overwrite old frozen result artifacts.**
- **Acceptance gate:** Every reported factor observation has sufficient authenticated breadth under its stated rule; exceptions are labeled.
- **Progress record:** owner `Codex`; result `SOURCE_EVIDENCE_BLOCKED`; baseline SHA `4e7fbdc380b8042db72e9c628260f60077a205ef`; code/evidence checkpoint `ef339ab`; tests `PHASE1_TEST_RESULTS.txt`; evidence `../../outputs/audit/phase1/PHASE1_FINANCIAL_DATA_VALIDATION.md#d3`; numerical change `no historical before/after available; see reconciliation CSV`; research-paper impact `Early sparse cross-sections remain limited; no replacement breadth threshold chosen after inspecting performance.`; independent reviewer `PENDING`.


- **Phase2B evidence (1 November2026):** previous `SOURCE_EVIDENCE_BLOCKED`; current `NEEDS_REVIEW`. Source `factors/holding.py::form_quantiles`; empirical source commit `291447199fe603f0168d972ee77b88c4d949f205`. At least3 eligible names/all3 quantiles and positive cap weights; 956 singleton quantile observations remain. Remaining limitation/manuscript consequence: Tiny early cross-sections require predeclared robustness; no threshold tuning. Qualify early evidence. Evidence: `../../outputs/audit/phase2b/PHASE2B_EMPIRICAL_CORRECTION_REPORT.md`, issue CSV, source manifest and bound numerical/case evidence. Tests37targeted/358full PASS,90.68%coverage; independent returns/regressions/hashes PASS. New factor `factor-4ddee9ac6fb45cedfd62a2cc68676b58`; primary pricing `asset-pricing-d60bee7310b34976c80372a0f0f29e21`. Original hashes and values preserved; exact before/after/horizon distinctions in reconciliation CSVs. Reviewer `PENDING`.

#### [ ] D4 — Are SEC fundamental facts joined using filing acceptance and actual tradable availability, rather than fiscal period end?

- **Phase / severity from initial audit:** 1 / High; **status:** `SOURCE_EVIDENCE_BLOCKED`.
- **Why this matters / failure mode:** Are SEC fundamental facts joined using filing acceptance and actual tradable availability, rather than fiscal period end? A mismatch can change empirical interpretation or make a paper claim stronger than the underlying data support; do not presume a defect before examining the archived outputs.
- **Inspect first:** `SEC acquisition/normalization; factors/temporal.py; source manifests`. Resolve these to actual paths on the checked-out commit; record function names/line ranges rather than assuming they are unchanged.
- **Detailed verification and candidate correction:** Sample original EDGAR accession/acceptance timestamps, fiscal period ends, amendments, effective-dated security joins and first eligible trade sessions. Test same-day/after-close availability and reject stale hindsight replacement.
- **Initial audit requested:** Audit several securities and amendments independently.
- **Deliverable:** `outputs/audit/sec_pit_case_studies.csv` (or an equivalent, documented path); record source input hashes, exact calculations and explanatory caveats. **Never overwrite old frozen result artifacts.**
- **Acceptance gate:** All sampled features are available strictly before their claimed decisions, or affected values are corrected and propagated.
- **Progress record:** owner `Codex`; result `SOURCE_EVIDENCE_BLOCKED`; baseline SHA `4e7fbdc380b8042db72e9c628260f60077a205ef`; code/evidence checkpoint `ef339ab`; tests `PHASE1_TEST_RESULTS.txt`; evidence `../../outputs/audit/phase1/PHASE1_FINANCIAL_DATA_VALIDATION.md#d4`; numerical change `no historical before/after available; see reconciliation CSV`; research-paper impact `Do not certify all features available before close decisions; keep filing-date versus tradable availability distinction explicit.`; independent reviewer `PENDING`.


- **Phase2B evidence (1 November2026):** previous `SOURCE_EVIDENCE_BLOCKED`; current `SOURCE_EVIDENCE_BLOCKED`. Source `factors/temporal.py::point_in_time_panel; factors/holding.py::monthly_cycles`; empirical source commit `291447199fe603f0168d972ee77b88c4d949f205`. Every used score meets cutoff; next-session close execution; three actual SEC/accession/ratio/score/decision traces. Remaining limitation/manuscript consequence: Representative shares/amendments and cache hashes do not prove every historical capture or intraday availability. No strict PIT certificate. Evidence: `../../outputs/audit/phase2b/PHASE2B_EMPIRICAL_CORRECTION_REPORT.md`, issue CSV, source manifest and bound numerical/case evidence. Tests37targeted/358full PASS,90.68%coverage; independent returns/regressions/hashes PASS. New factor `factor-4ddee9ac6fb45cedfd62a2cc68676b58`; primary pricing `asset-pricing-d60bee7310b34976c80372a0f0f29e21`. Original hashes and values preserved; exact before/after/horizon distinctions in reconciliation CSVs. Reviewer `PENDING`.

#### [ ] D5 — Are share classes, ticker changes and issuer-level SEC facts properly separated?

- **Phase / severity from initial audit:** 1 / High; **status:** `RESEARCH_LIMITATION_DISCLOSED`.
- **Why this matters / failure mode:** Are share classes, ticker changes and issuer-level SEC facts properly separated? A mismatch can change empirical interpretation or make a paper claim stronger than the underlying data support; do not presume a defect before examining the archived outputs.
- **Inspect first:** `universe security mapping code; listing and CIK audit files`. Resolve these to actual paths on the checked-out commit; record function names/line ranges rather than assuming they are unchanged.
- **Detailed verification and candidate correction:** Select difficult ticker changes, delistings, multiple listed classes and multiple CIK/listing associations. Trace permanent keys and date-effective joins; reject a CIK used as a unique tradable share-class key.
- **Initial audit requested:** Verify difficult CIK/listing examples.
- **Deliverable:** `outputs/audit/identity_case_studies.csv` (or an equivalent, documented path); record source input hashes, exact calculations and explanatory caveats. **Never overwrite old frozen result artifacts.**
- **Acceptance gate:** No unsupported issuer-to-security lookahead mapping persists in the validated sample.
- **Progress record:** owner `Codex`; result `SOURCE_EVIDENCE_BLOCKED`; baseline SHA `4e7fbdc380b8042db72e9c628260f60077a205ef`; code/evidence checkpoint `ef339ab`; tests `PHASE1_TEST_RESULTS.txt`; evidence `../../outputs/audit/phase1/PHASE1_FINANCIAL_DATA_VALIDATION.md#d5`; numerical change `no historical before/after available; see reconciliation CSV`; research-paper impact `No real share-class sample authenticated; avoid claiming synthetic mapping tests validate all 487 identities.`; independent reviewer `PENDING`.


- **Phase2B evidence (1 November2026):** previous `SOURCE_EVIDENCE_BLOCKED`; current `RESEARCH_LIMITATION_DISCLOSED`. Source `PHASE2B_SOURCE_CASE_EVIDENCE.json::formed_member_listing_violations`; empirical source commit `291447199fe603f0168d972ee77b88c4d949f205`. All1,138,880 member intervals respect dated listing bounds; none of15 provider-documented reused tickers retained. Remaining limitation/manuscript consequence: Not exhaustive independent issuer/share-class or split/share-basis reconstruction; reviewer acceptance pending. Evidence: `../../outputs/audit/phase2b/PHASE2B_EMPIRICAL_CORRECTION_REPORT.md`, issue CSV, source manifest and bound numerical/case evidence. Tests37targeted/358full PASS,90.68%coverage; independent returns/regressions/hashes PASS. New factor `factor-4ddee9ac6fb45cedfd62a2cc68676b58`; primary pricing `asset-pricing-d60bee7310b34976c80372a0f0f29e21`. Original hashes and values preserved; exact before/after/horizon distinctions in reconciliation CSVs. Reviewer `PENDING`.

#### [ ] D6 — Could requiring complete shares, fundamentals and terminal-event evidence select financially healthier firms?

- **Phase / severity from initial audit:** 1 / High; **status:** `SOURCE_EVIDENCE_BLOCKED`.
- **Why this matters / failure mode:** Could requiring complete shares, fundamentals and terminal-event evidence select financially healthier firms? A mismatch can change empirical interpretation or make a paper claim stronger than the underlying data support; do not presume a defect before examining the archived outputs.
- **Inspect first:** `screening decisions; rejection evidence; annual breadth`. Resolve these to actual paths on the checked-out commit; record function names/line ranges rather than assuming they are unchanged.
- **Detailed verification and candidate correction:** Quantify rejected-versus-accepted groups by reason, time, industry, known lifecycle and available risk/returns; measure potential survivorship and selection bias, not assume missing returns are zero.
- **Initial audit requested:** Analyze rejection characteristics and missingness.
- **Deliverable:** `outputs/audit/selection_bias_report.csv` (or an equivalent, documented path); record source input hashes, exact calculations and explanatory caveats. **Never overwrite old frozen result artifacts.**
- **Acceptance gate:** Selection effects and excluded populations are explicitly bounded; missing comparisons are identified.
- **Progress record:** owner `Codex`; result `SOURCE_EVIDENCE_BLOCKED`; baseline SHA `4e7fbdc380b8042db72e9c628260f60077a205ef`; code/evidence checkpoint `ef339ab`; tests `PHASE1_TEST_RESULTS.txt`; evidence `../../outputs/audit/phase1/PHASE1_FINANCIAL_DATA_VALIDATION.md#d6`; numerical change `no historical before/after available; see reconciliation CSV`; research-paper impact `Selection on complete shares/fundamentals/terminal evidence can select healthier firms; direction and magnitude not quantified.`; independent reviewer `PENDING`.

#### [ ] D7 — Why is the equity_issuance factor non-estimable?

- **Phase / severity from initial audit:** 1 / Medium; **status:** `SOURCE_EVIDENCE_BLOCKED`.
- **Why this matters / failure mode:** Why is the equity_issuance factor non-estimable? A mismatch can change empirical interpretation or make a paper claim stronger than the underlying data support; do not presume a defect before examining the archived outputs.
- **Inspect first:** `factor definitions; SEC concept mappings`. Resolve these to actual paths on the checked-out commit; record function names/line ranges rather than assuming they are unchanged.
- **Detailed verification and candidate correction:** Inspect equity issuance formula, required input concepts, amendments and share-equity reconciliation. Give concrete rejected data examples; do not impute missing issuance or count 48 as 48 estimable.
- **Initial audit requested:** Provide concrete missing-source examples; retain the negative result.
- **Deliverable:** `outputs/audit/equity_issuance_evidence.md` (or an equivalent, documented path); record source input hashes, exact calculations and explanatory caveats. **Never overwrite old frozen result artifacts.**
- **Acceptance gate:** 47 estimable and one not-estimable remain consistently identified unless genuinely corrected source evidence changes status.
- **Progress record:** owner `Codex`; result `SOURCE_EVIDENCE_BLOCKED`; baseline SHA `4e7fbdc380b8042db72e9c628260f60077a205ef`; code/evidence checkpoint `ef339ab`; tests `PHASE1_TEST_RESULTS.txt`; evidence `../../outputs/audit/phase1/PHASE1_FINANCIAL_DATA_VALIDATION.md#d7`; numerical change `no historical before/after available; see reconciliation CSV`; research-paper impact `Retain 48 configured/47 reported estimable; PDF Appendix A Observations715447 appears to count grid rows even for non-estimable issuance, requiring later terminology clarification; valid counts remain source blocked.`; independent reviewer `PENDING`.

#### [x] D8 — Could partial holding-period observations create biased factor portfolio returns?

- **Phase / severity from initial audit:** 1 / High; **status:** `CONFIRMED_ERROR_FIXED`.
- **Why this matters / failure mode:** Could partial holding-period observations create biased factor portfolio returns? A mismatch can change empirical interpretation or make a paper claim stronger than the underlying data support; do not presume a defect before examining the archived outputs.
- **Inspect first:** `src/institutional_factor_platform/factors/portfolio.py; holding-period market rows`. Resolve these to actual paths on the checked-out commit; record function names/line ranges rather than assuming they are unchanged.
- **Detailed verification and candidate correction:** For every formed quantile, compare scheduled formation/exit dates and constituent realized-return coverage. Identify securities ending early, missing terminal-event returns, partial holding periods, and whether aggregation mistakenly treats them as full-period investments. Test synthetic delisting/partial-history cases.
- **Initial audit requested:** Verify common holding calendars and incomplete histories.
- **Deliverable:** `outputs/audit/holding_period_coverage.csv` (or an equivalent, documented path); record source input hashes, exact calculations and explanatory caveats. **Never overwrite old frozen result artifacts.**
- **Acceptance gate:** A matched holding-calendar accounting rule is validated; any corrected factor series receives versioned outputs.
- **Progress record:** owner `Codex`; result `SOURCE_EVIDENCE_BLOCKED`; baseline SHA `4e7fbdc380b8042db72e9c628260f60077a205ef`; code/evidence checkpoint `ef339ab`; tests `PHASE1_TEST_RESULTS.txt`; evidence `../../outputs/audit/phase1/PHASE1_FINANCIAL_DATA_VALIDATION.md#d8`; numerical change `no historical before/after available; see reconciliation CSV`; research-paper impact `All dependent factor/pricing/portfolio/ML claims need targeted review when authenticated corrected factors exist; no new empirical values published.`; independent reviewer `PENDING`.


- **Phase2B evidence (1 November2026):** previous `SOURCE_EVIDENCE_BLOCKED`; current `CONFIRMED_ERROR_FIXED`. Source `factors/holding.py::endpoint_chain; scripts/research_phase2b.py::build_factors`; empirical source commit `291447199fe603f0168d972ee77b88c4d949f205`. 265groups/277occurrences:195 valid interior-gap endpoint chains,70 missing old endpoints. New11352 full-cycle rows, zero endpoint-rejected formed groups. Remaining limitation/manuscript consequence: No recovered old endpoint, daily mark, terminal payout, zero/cash/stale fill or survivor reweighting. Correct old incomplete-history interpretation. Evidence: `../../outputs/audit/phase2b/PHASE2B_EMPIRICAL_CORRECTION_REPORT.md`, issue CSV, source manifest and bound numerical/case evidence. Tests37targeted/358full PASS,90.68%coverage; independent returns/regressions/hashes PASS. New factor `factor-4ddee9ac6fb45cedfd62a2cc68676b58`; primary pricing `asset-pricing-d60bee7310b34976c80372a0f0f29e21`. Original hashes and values preserved; exact before/after/horizon distinctions in reconciliation CSVs. Reviewer `PENDING`.

#### [x] D9 — Are the 48 factor definitions genuinely distinct and point-in-time?

- **Phase / severity from initial audit:** 1 / High; **status:** `RESEARCH_LIMITATION_DISCLOSED`.
- **Why this matters / failure mode:** Are the 48 factor definitions genuinely distinct and point-in-time? A mismatch can change empirical interpretation or make a paper claim stronger than the underlying data support; do not presume a defect before examining the archived outputs.
- **Inspect first:** `factor definitions; config/factors.yaml or actual configuration`. Resolve these to actual paths on the checked-out commit; record function names/line ranges rather than assuming they are unchanged.
- **Detailed verification and candidate correction:** List all 48 factor IDs, economic formula, units, required inputs, lookback, availability lag, direction, duplicate proxies and dates with valid cross-sections. Independently reproduce representative calculations including 12–1 momentum, leverage and liquidity.
- **Initial audit requested:** Audit definitions, timing, annualization and duplicate economic exposures.
- **Deliverable:** `outputs/audit/factor_definition_inventory.csv` (or an equivalent, documented path); record source input hashes, exact calculations and explanatory caveats. **Never overwrite old frozen result artifacts.**
- **Acceptance gate:** All 48 registry entries are distinct as defined, 47 estimable status is supported, and no lookahead/units error remains.
- **Progress record:** owner `Codex`; result `NEEDS_REVIEW`; baseline SHA `4e7fbdc380b8042db72e9c628260f60077a205ef`; code/evidence checkpoint `ef339ab`; tests `PHASE1_TEST_RESULTS.txt`; evidence `../../outputs/audit/phase1/PHASE1_FINANCIAL_DATA_VALIDATION.md#d9`; numerical change `no historical before/after available; see reconciliation CSV`; research-paper impact `48 distinct independent exposures not supported. Preserve IDs and disclose aliases; short warmups and UTC-day cutoff need interpretation review.`; independent reviewer `PENDING`.


- **Phase2B evidence (1 November2026):** previous `NEEDS_REVIEW`; current `RESEARCH_LIMITATION_DISCLOSED`. Source `factors/definitions.py; PHASE2B_SOURCE_CASE_EVIDENCE.json::factor_counts`; empirical source commit `291447199fe603f0168d972ee77b88c4d949f205`. 48names/47raw estimable;28,550,589 nonmissing raw and24,255,559 scores;41portfolio characteristics/123series/six repeated pairs. Remaining limitation/manuscript consequence: Names do not imply independent signals. Frozen score values/IDs preserved; describe duplicates and missing equity_issuance. Evidence: `../../outputs/audit/phase2b/PHASE2B_EMPIRICAL_CORRECTION_REPORT.md`, issue CSV, source manifest and bound numerical/case evidence. Tests37targeted/358full PASS,90.68%coverage; independent returns/regressions/hashes PASS. New factor `factor-4ddee9ac6fb45cedfd62a2cc68676b58`; primary pricing `asset-pricing-d60bee7310b34976c80372a0f0f29e21`. Original hashes and values preserved; exact before/after/horizon distinctions in reconciliation CSVs. Reviewer `PENDING`.

#### [ ] V1 — HF Data Library historical price-adjustment vintage may differ from current files

- **Phase / severity from initial audit:** 1 / High; **status:** `SOURCE_EVIDENCE_BLOCKED`.
- **Why this matters / failure mode:** HF Data Library historical price-adjustment vintage may differ from current files A mismatch can change empirical interpretation or make a paper claim stronger than the underlying data support; do not presume a defect before examining the archived outputs.
- **Inspect first:** `HF Data Library archives; acquisition checksums; provider release history`. Resolve these to actual paths on the checked-out commit; record function names/line ranges rather than assuming they are unchanged.
- **Detailed verification and candidate correction:** Inspect HF Data Library original retrieval manifests and source archives to identify adjusted-vs-split-adjusted-vs-dividend-total-return vintage. Compare provider change documentation only as a source-version risk; never replace historical files with fresh download. Quantify sensitivity where paired legitimate frozen vintages exist.
- **Initial audit requested:** Check original archived return basis.
- **Deliverable:** `outputs/audit/price_vintage_verification.csv` (or an equivalent, documented path); record source input hashes, exact calculations and explanatory caveats. **Never overwrite old frozen result artifacts.**
- **Acceptance gate:** The price-return convention and archived source vintage are proved, or manuscript return labels are limited accordingly.
- **Progress record:** owner `Codex`; result `SOURCE_EVIDENCE_BLOCKED`; baseline SHA `4e7fbdc380b8042db72e9c628260f60077a205ef`; code/evidence checkpoint `ef339ab`; tests `PHASE1_TEST_RESULTS.txt`; evidence `../../outputs/audit/phase1/PHASE1_FINANCIAL_DATA_VALIDATION.md#v1`; numerical change `no historical before/after available; see reconciliation CSV`; research-paper impact `Total-return terminology remains unverified for original HF inputs; provider change is established, study-specific numerical effect unknown.`; independent reviewer `PENDING`.


### Phase 2 — Factors and five asset-pricing models


- **Phase2B evidence (1 November2026):** previous `SOURCE_EVIDENCE_BLOCKED`; current `SOURCE_EVIDENCE_BLOCKED`. Source `original HF raw/source manifests; PHASE2B_SOURCE_CASE_EVIDENCE.json::vintage_examples`; empirical source commit `291447199fe603f0168d972ee77b88c4d949f205`. Split continuity, dividend-date quotes and PiTrading/IEX splice checked; normalized quotes match raw Close. Provider documents old mixed basis. Remaining limitation/manuscript consequence: No same-vintage distribution/unadjusted control proves complete total returns. Label frozen provider-vintage adjusted-quote returns. Evidence: `../../outputs/audit/phase2b/PHASE2B_EMPIRICAL_CORRECTION_REPORT.md`, issue CSV, source manifest and bound numerical/case evidence. Tests37targeted/358full PASS,90.68%coverage; independent returns/regressions/hashes PASS. New factor `factor-4ddee9ac6fb45cedfd62a2cc68676b58`; primary pricing `asset-pricing-d60bee7310b34976c80372a0f0f29e21`. Original hashes and values preserved; exact before/after/horizon distinctions in reconciliation CSVs. Reviewer `PENDING`.

#### [x] AP1 — Why is mean CAPM adjusted R² only 0.063?

- **Phase / severity from initial audit:** 2 / High; **status:** `CONFIRMED_ERROR_FIXED`.
- **Why this matters / failure mode:** Why is mean CAPM adjusted R² only 0.063? A mismatch can change empirical interpretation or make a paper claim stronger than the underlying data support; do not presume a defect before examining the archived outputs.
- **Inspect first:** `src/institutional_factor_platform/asset_pricing/inputs.py; regression engine; config/asset_pricing.yaml`. Resolve these to actual paths on the checked-out commit; record function names/line ranges rather than assuming they are unchanged.
- **Detailed verification and candidate correction:** Reconstruct CAPM regressions for selected test assets from frozen monthly excess returns and market_excess. Check dates, benchmark composition, decimal units, missingness, adjusted R² calculation and 24-observation minimum.
- **Initial audit requested:** Inspect benchmark definition, portfolio return units and aligned regression samples.
- **Deliverable:** `outputs/audit/capm_regression_reproduction.csv` (or an equivalent, documented path); record source input hashes, exact calculations and explanatory caveats. **Never overwrite old frozen result artifacts.**
- **Acceptance gate:** Explain or correct the mean adjusted R²=0.063 from independent aligned samples.
- **Progress record:** owner `Codex`; result `NEEDS_REVIEW`; baseline `10b3dc353f604ef332f55c153b093d1628a4ff7f`; source checkpoint `62343e686475552a0b629d63b5445a6203ea90f7`; evidence `outputs/audit/phase2/PHASE2_ASSET_PRICING_VALIDATION.md#ap1` and issue-results CSV; independent check `All 615 archived regressions reproduced. Confirmed daily-versus-holding-period input defect fixed, with failing regression before correction. HF SPY proxy identity matches 2128/2128 dates exactly.`; numerical result `Archived CAPM adjustedR2=.0634395196779754; conditional interval diagnostic=.6614998064308784, holding old quantile returns fixed.`; tests `343 passed,90.58% coverage;35 targeted`; paper consequence `Published model fit and alpha tables require review; do not silently substitute the larger diagnostic fit.`; remaining limitation `Conditional result is not a regenerated factor/pricing publication. Resolve D8 incomplete holdings and D4/V1 timing/return basis before new principal claims.`; independent reviewer `PENDING`.


- **Phase2B evidence (1 November2026):** previous `NEEDS_REVIEW`; current `CONFIRMED_ERROR_FIXED`. Source `asset_pricing/inputs.py::_holding_period_market_factors`; empirical source commit `291447199fe603f0168d972ee77b88c4d949f205`. Exact execution-to-exit market and cash gross compounding; independent interval errors0. Primary CAPM adjR2 .7608181374. Remaining limitation/manuscript consequence: SPY is inherited market proxy; source limits remain. Replace frequency-mismatched conclusions only after review. Evidence: `../../outputs/audit/phase2b/PHASE2B_EMPIRICAL_CORRECTION_REPORT.md`, issue CSV, source manifest and bound numerical/case evidence. Tests37targeted/358full PASS,90.68%coverage; independent returns/regressions/hashes PASS. New factor `factor-4ddee9ac6fb45cedfd62a2cc68676b58`; primary pricing `asset-pricing-d60bee7310b34976c80372a0f0f29e21`. Original hashes and values preserved; exact before/after/horizon distinctions in reconciliation CSVs. Reviewer `PENDING`.

#### [x] AP2 — Are all 123 diagnostic portfolios valid, sufficiently populated and independently informative?

- **Phase / severity from initial audit:** 2 / High; **status:** `CONFIRMED_ERROR_FIXED`.
- **Why this matters / failure mode:** Are all 123 diagnostic portfolios valid, sufficiently populated and independently informative? A mismatch can change empirical interpretation or make a paper claim stronger than the underlying data support; do not presume a defect before examining the archived outputs.
- **Inspect first:** `factor portfolio publication; asset pricing comparisons`. Resolve these to actual paths on the checked-out commit; record function names/line ranges rather than assuming they are unchanged.
- **Detailed verification and candidate correction:** Inventory all 123 dependent portfolios: unique underlying factor/quantile, holdings, overlap, observation counts, formation timing and effective exposure. Identify reused or highly correlated test assets.
- **Initial audit requested:** Inspect asset IDs, formation dates and overlap.
- **Deliverable:** `outputs/audit/test_asset_inventory.csv` (or an equivalent, documented path); record source input hashes, exact calculations and explanatory caveats. **Never overwrite old frozen result artifacts.**
- **Acceptance gate:** 123 counts and effective degrees of independence are transparently described.
- **Progress record:** owner `Codex`; result `NEEDS_REVIEW`; baseline `10b3dc353f604ef332f55c153b093d1628a4ff7f`; source checkpoint `62343e686475552a0b629d63b5445a6203ea90f7`; evidence `outputs/audit/phase2/PHASE2_ASSET_PRICING_VALIDATION.md#ap2` and issue-results CSV; independent check `123 frozen IDs authenticated; all11545 group counts and weighted returns reconstructed (max error5.56e-17). 265 groups contain incomplete constituent paths; memberships are reconstructed, not independently persisted decision records.`; numerical result `11545 original groups; 70 single-quantile factor intervals cannot form spreads; 3825 complete triples. Six equal-return name pairs on shared observations.`; tests `343 passed,90.58% coverage;35 targeted`; paper consequence `123 means labeled dependent portfolios, not 123 independent experiments or uniformly valid complete-period investments.`; remaining limitation `Full investable/common-horizon validity not established. Frozen input authenticity does not prove strict historical availability or complete terminal-event accounting.`; independent reviewer `PENDING`.


- **Phase2B evidence (1 November2026):** previous `NEEDS_REVIEW`; current `CONFIRMED_ERROR_FIXED`. Source `factors/holding.py; asset_pricing/inputs.py::build_research_panel`; empirical source commit `291447199fe603f0168d972ee77b88c4d949f205`. 123 estimable portfolios;11352 full-cycle observations;615primary+615supplementary fits. Q2 cannot substitute for Q1. Remaining limitation/manuscript consequence: Dependent constructed assets and singleton groups remain; new counts/identities required in later paper. Evidence: `../../outputs/audit/phase2b/PHASE2B_EMPIRICAL_CORRECTION_REPORT.md`, issue CSV, source manifest and bound numerical/case evidence. Tests37targeted/358full PASS,90.68%coverage; independent returns/regressions/hashes PASS. New factor `factor-4ddee9ac6fb45cedfd62a2cc68676b58`; primary pricing `asset-pricing-d60bee7310b34976c80372a0f0f29e21`. Original hashes and values preserved; exact before/after/horizon distinctions in reconciliation CSVs. Reviewer `PENDING`.

#### [x] AP3 — Are some explanatory factors constructed using securities that also define the dependent test portfolios?

- **Phase / severity from initial audit:** 2 / High; **status:** `RESEARCH_LIMITATION_DISCLOSED`.
- **Why this matters / failure mode:** Are some explanatory factors constructed using securities that also define the dependent test portfolios? A mismatch can change empirical interpretation or make a paper claim stronger than the underlying data support; do not presume a defect before examining the archived outputs.
- **Inspect first:** `asset_pricing/inputs.py; factor portfolio memberships`. Resolve these to actual paths on the checked-out commit; record function names/line ranges rather than assuming they are unchanged.
- **Detailed verification and candidate correction:** Trace test-portfolio holdings and explanatory H–L factor long/short legs to the same source membership. Quantify overlap and evaluate feasible leave-one-group-out or externally published factor benchmarks without searching for better performance.
- **Initial audit requested:** Assess mechanical overlap and propose a disjoint-universe or external-factor check.
- **Deliverable:** `outputs/audit/factor_test_asset_overlap.csv` (or an equivalent, documented path); record source input hashes, exact calculations and explanatory caveats. **Never overwrite old frozen result artifacts.**
- **Acceptance gate:** Mechanical common-composition effects are quantified or expressly acknowledged.
- **Progress record:** owner `Codex`; result `RESEARCH_LIMITATION_DISCLOSED`; baseline `10b3dc353f604ef332f55c153b093d1628a4ff7f`; source checkpoint `62343e686475552a0b629d63b5445a6203ea90f7`; evidence `outputs/audit/phase2/PHASE2_ASSET_PRICING_VALIDATION.md#ap3` and issue-results CSV; independent check `Shared construction established in code and reconstructed memberships. Full-available-interval overlap summarized by eight aliases; representative2022-05-31 mean weight overlap=.6128445036 over984 comparisons.`; numerical result `Full interval mean overlap ranges .2640(RMW) to .8035(SMB/ME); all extrema spreads observed are Q3-Q1.`; tests `343 passed,90.58% coverage;35 targeted`; paper consequence `Treat in-sample fit as dependent diagnostic evidence; do not claim externally independent explanatory factors/test assets.`; remaining limitation `Overlap mixes legitimate systematic exposure and mechanical leg reuse. Reconstruction is consistent with frozen counts/returns, not an independent holdings attestation. No disjoint-universe experiment introduced.`; independent reviewer `PENDING`.


- **Phase2B evidence (1 November2026):** previous `RESEARCH_LIMITATION_DISCLOSED`; current `RESEARCH_LIMITATION_DISCLOSED`. Source `PHASE2B_INDEPENDENT_VALIDATION.json::overlap`; empirical source commit `291447199fe603f0168d972ee77b88c4d949f205`. Shared constituent means SMB/ME .681716,HML .577757,MOM .574423,RMW .250764,CMA/IA .557992,ROE .571497. Remaining limitation/manuscript consequence: Overlap is descriptive, not a percentage of artificially inflated R2; independent-factor robustness deferred. Evidence: `../../outputs/audit/phase2b/PHASE2B_EMPIRICAL_CORRECTION_REPORT.md`, issue CSV, source manifest and bound numerical/case evidence. Tests37targeted/358full PASS,90.68%coverage; independent returns/regressions/hashes PASS. New factor `factor-4ddee9ac6fb45cedfd62a2cc68676b58`; primary pricing `asset-pricing-d60bee7310b34976c80372a0f0f29e21`. Original hashes and values preserved; exact before/after/horizon distinctions in reconciliation CSVs. Reviewer `PENDING`.


- **Phase2C independent-referee evidence (1 November2026):** status `RESEARCH_LIMITATION_DISCLOSED` and checkbox unchanged. The predetermined all-dependent-constituent exclusion retains109assets and leaves14empty-leg cases unestimable. Baseline and diagnostic use identical dates/assets. Richer-model mean fit changes modestly; no independent-factor or overlap-generated-R2 claim follows. Source: `scripts/research_phase2c.py`, `scripts/phase2c_reference.py`; numerical calculation commit `ac478bb59027e27212c7f5da28846dd1107434cb`. Evidence `../../outputs/audit/phase2c/PHASE2C_REGRESSION_VERIFICATION.md`, portfolio/model/difference/dependence CSVs and source manifest. Same authenticated Phase2B publications/parents, no value change or new publication.45targeted/366full PASS,90.68%coverage; exact hashes and numerical errors recorded. Manuscript consequence: support qualified descriptive tables only; economic/PIT/provider limits persist. Reviewer `PENDING`.

#### [x] AP4 — Does the study's “q mapping” genuinely represent the Hou–Xue–Zhang model?

- **Phase / severity from initial audit:** 2 / High; **status:** `RESEARCH_LIMITATION_DISCLOSED`.
- **Why this matters / failure mode:** Does the study's “q mapping” genuinely represent the Hou–Xue–Zhang model? A mismatch can change empirical interpretation or make a paper claim stronger than the underlying data support; do not presume a defect before examining the archived outputs.
- **Inspect first:** `config/asset_pricing.yaml; cited q factor literature`. Resolve these to actual paths on the checked-out commit; record function names/line ranges rather than assuming they are unchanged.
- **Detailed verification and candidate correction:** For each configured q mapping, compare research-defined ME, IA and ROE with published q-factor definitions. Specifically establish that earnings_yield is not accounting ROE, and that log market cap is not necessarily the published q-size return factor. Rename the specification when appropriate.
- **Initial audit requested:** Retain study-specific labeling; clarify earnings yield versus return on equity.
- **Deliverable:** `outputs/audit/q_mapping_definition_audit.md` (or an equivalent, documented path); record source input hashes, exact calculations and explanatory caveats. **Never overwrite old frozen result artifacts.**
- **Acceptance gate:** No claim of exact Hou–Xue–Zhang factor replication remains without matching methodology.
- **Progress record:** owner `Codex`; result `RESEARCH_LIMITATION_DISCLOSED`; baseline `10b3dc353f604ef332f55c153b093d1628a4ff7f`; source checkpoint `62343e686475552a0b629d63b5445a6203ea90f7`; evidence `outputs/audit/phase2/PHASE2_ASSET_PRICING_VALIDATION.md#ap4` and issue-results CSV; independent check `Study-specific q-style terminology clarified in code comments/config and future publication assumptions. Stable model/alias IDs and historical numerical mapping retained.`; numerical result `Numerical configuration hash unchanged:734e675a123eddae5cc25ff3008e5b453f66f5696c42ea3af847bc3c4b321268.`; tests `343 passed,90.58% coverage;35 targeted`; paper consequence `Use study-specific q-style mapping; preserve historical labels as historical identities. No manuscript edit or unannounced ROE substitution.`; remaining limitation `Simple monthly characteristic terciles differ from official2x3x3 construction, annual investment/size timing and quarterly lagged-book-equity ROE. No claim of exact HXZ replication.`; independent reviewer `PENDING`.


- **Phase2B evidence (1 November2026):** previous `RESEARCH_LIMITATION_DISCLOSED`; current `RESEARCH_LIMITATION_DISCLOSED`. Source `config/asset_pricing.yaml::factor_mappings`; empirical source commit `291447199fe603f0168d972ee77b88c4d949f205`. Historical q ID and ROE=earnings_yield unchanged; ME=SMB and IA=CMA aliases. Remaining limitation/manuscript consequence: Study-specific q-style proxy, not exact HXZ replication; retain qualified description. Evidence: `../../outputs/audit/phase2b/PHASE2B_EMPIRICAL_CORRECTION_REPORT.md`, issue CSV, source manifest and bound numerical/case evidence. Tests37targeted/358full PASS,90.68%coverage; independent returns/regressions/hashes PASS. New factor `factor-4ddee9ac6fb45cedfd62a2cc68676b58`; primary pricing `asset-pricing-d60bee7310b34976c80372a0f0f29e21`. Original hashes and values preserved; exact before/after/horizon distinctions in reconciliation CSVs. Reviewer `PENDING`.

#### [x] AP5 — Why do 85.4% of CAPM portfolio intercept tests and 92.7% of FF5 tests have unadjusted p-values below 0.05?

- **Phase / severity from initial audit:** 2 / High; **status:** `CONFIRMED_ERROR_FIXED`.
- **Why this matters / failure mode:** Why do 85.4% of CAPM portfolio intercept tests and 92.7% of FF5 tests have unadjusted p-values below 0.05? A mismatch can change empirical interpretation or make a paper claim stronger than the underlying data support; do not presume a defect before examining the archived outputs.
- **Inspect first:** `regression engine, diagnostics, asset pricing coefficient parquet`. Resolve these to actual paths on the checked-out commit; record function names/line ranges rather than assuming they are unchanged.
- **Detailed verification and candidate correction:** Recompute HAC intercept estimate, SE, t, p and monthly alpha for each of 123×5 tests. Check intercept reference return, lags and two-sided p distribution; report multiplicity-aware exploratory summaries and dependence caveats.
- **Initial audit requested:** Reconstruct intercept tests, factor alignments and multiplicity.
- **Deliverable:** `outputs/audit/intercept_significance_audit.csv` (or an equivalent, documented path); record source input hashes, exact calculations and explanatory caveats. **Never overwrite old frozen result artifacts.**
- **Acceptance gate:** 85.4% and 92.7% nominal rejection shares are reconciled or corrected; no unadjusted evidence called FDR-controlled.
- **Progress record:** owner `Codex`; result `NEEDS_REVIEW`; baseline `10b3dc353f604ef332f55c153b093d1628a4ff7f`; source checkpoint `62343e686475552a0b629d63b5445a6203ea90f7`; evidence `outputs/audit/phase2/PHASE2_ASSET_PRICING_VALIDATION.md#ap5` and issue-results CSV; independent check `All estimates/SEs/p/residuals reproduced from authentic frozen matrices. CAPM105/123 and FF5114/123 nominal p<.05 confirmed. Supplementary multiplicity summaries retained as diagnostics.`; numerical result `Interval-aligned diagnostic has CAPM1/123 and FF510/123 nominal rejections on retained old quantile inputs.`; tests `343 passed,90.58% coverage;35 targeted`; paper consequence `85.4%/92.7% are reproduced nominal arithmetic, not validated discovery rates or persistent alpha.`; remaining limitation `Historical high shares arise under confirmed frequency mismatch; scientific inference must be reviewed after upstream rebuild. BH dependence assumptions and original test-family approval not established.`; independent reviewer `PENDING`.


- **Phase2B evidence (1 November2026):** previous `NEEDS_REVIEW`; current `CONFIRMED_ERROR_FIXED`. Source `regression/engine.py::fit_regression; scripts/research_phase2b.py::reference_fit`; empirical source commit `291447199fe603f0168d972ee77b88c4d949f205`. Original/conditional/new supplementary/new primary nominal rejections CAPM105/1/3/8;FF5 114/10/8/8, denominator123. Remaining limitation/manuscript consequence: Nominal dependent tests; fewer rejections do not prove superior pricing; no significance tuning. Evidence: `../../outputs/audit/phase2b/PHASE2B_EMPIRICAL_CORRECTION_REPORT.md`, issue CSV, source manifest and bound numerical/case evidence. Tests37targeted/358full PASS,90.68%coverage; independent returns/regressions/hashes PASS. New factor `factor-4ddee9ac6fb45cedfd62a2cc68676b58`; primary pricing `asset-pricing-d60bee7310b34976c80372a0f0f29e21`. Original hashes and values preserved; exact before/after/horizon distinctions in reconciliation CSVs. Reviewer `PENDING`.


- **Phase2C independent-referee evidence (1 November2026):** status `CONFIRMED_ERROR_FIXED` and checkbox unchanged. All615primary intercepts, HAC/t/CI and sign counts reproduce via independent QR. Positive/negative point counts24/99,20/103,21/102,15/108,16/107; significant negative8/12/14/8/9, significant positive0 in every model. Holm within123/across615 rejects none, conditional on valid marginal p-values; no exactly-zero-alpha proof. Source: `scripts/research_phase2c.py`, `scripts/phase2c_reference.py`; numerical calculation commit `ac478bb59027e27212c7f5da28846dd1107434cb`. Evidence `../../outputs/audit/phase2c/PHASE2C_REGRESSION_VERIFICATION.md`, portfolio/model/difference/dependence CSVs and source manifest. Same authenticated Phase2B publications/parents, no value change or new publication.45targeted/366full PASS,90.68%coverage; exact hashes and numerical errors recorded. Manuscript consequence: support qualified descriptive tables only; economic/PIT/provider limits persist. Reviewer `PENDING`.

#### [x] AP6 — Why does FF5 improve adjusted R² but have a higher mean alpha and higher share of nominally significant intercepts than several other models?

- **Phase / severity from initial audit:** 2 / High; **status:** `RESEARCH_LIMITATION_DISCLOSED`.
- **Why this matters / failure mode:** Why does FF5 improve adjusted R² but have a higher mean alpha and higher share of nominally significant intercepts than several other models? A mismatch can change empirical interpretation or make a paper claim stronger than the underlying data support; do not presume a defect before examining the archived outputs.
- **Inspect first:** `asset pricing comparisons and coefficients`. Resolve these to actual paths on the checked-out commit; record function names/line ranges rather than assuming they are unchanged.
- **Detailed verification and candidate correction:** Compare matched-sample adjusted R² against pricing-error magnitudes: signed alpha, absolute alpha, RMSE and nominal/adjusted rejection shares. Identify why FF5 may fit better while leaving larger intercept errors; separate descriptive fit from pricing success.
- **Initial audit requested:** Discuss model fit and pricing errors as separate criteria.
- **Deliverable:** `outputs/audit/pricing_fit_vs_alpha.csv` (or an equivalent, documented path); record source input hashes, exact calculations and explanatory caveats. **Never overwrite old frozen result artifacts.**
- **Acceptance gate:** Model comparison explains, rather than conceals, the conflicting rankings.
- **Progress record:** owner `Codex`; result `RESEARCH_LIMITATION_DISCLOSED`; baseline `10b3dc353f604ef332f55c153b093d1628a4ff7f`; source checkpoint `62343e686475552a0b629d63b5445a6203ea90f7`; evidence `outputs/audit/phase2/PHASE2_ASSET_PRICING_VALIDATION.md#ap6` and issue-results CSV; independent check `Archived and same-sample alpha/R2 summaries reproduced. FF5 has higher fit but higher mean alpha than FF3; a small orthogonal reference demonstrates this can be mathematically correct.`; numerical result `Historical FF3 mean alpha .00923057 vs FF5 .01055936; same-sample historical .01002030 vs .01055936. All historical alphas positive, so signed/absolute means coincide.`; tests `343 passed,90.58% coverage;35 targeted`; paper consequence `Do not rank pricing success by adjustedR2 alone; show mean signed/absolute/RMS alpha, sample and inference separately.`; remaining limitation `Original samples differ, and input frequency defect affects interpretation. Same-sample diagnostic and interval-corrected control are separate from the original table.`; independent reviewer `PENDING`.


- **Phase2B evidence (1 November2026):** previous `RESEARCH_LIMITATION_DISCLOSED`; current `RESEARCH_LIMITATION_DISCLOSED`. Source `PHASE2B_MODEL_COMPARISON.csv`; empirical source commit `291447199fe603f0168d972ee77b88c4d949f205`. Primary mean adjR2 .760818/.802438/.811021/.817658/.814361; signed/absolute/RMS alpha and SE separately reported. Remaining limitation/manuscript consequence: Explanatory fit is not zero pricing error, economic alpha or investable performance. Evidence: `../../outputs/audit/phase2b/PHASE2B_EMPIRICAL_CORRECTION_REPORT.md`, issue CSV, source manifest and bound numerical/case evidence. Tests37targeted/358full PASS,90.68%coverage; independent returns/regressions/hashes PASS. New factor `factor-4ddee9ac6fb45cedfd62a2cc68676b58`; primary pricing `asset-pricing-d60bee7310b34976c80372a0f0f29e21`. Original hashes and values preserved; exact before/after/horizon distinctions in reconciliation CSVs. Reviewer `PENDING`.


- **Phase2C independent-referee evidence (1 November2026):** status `RESEARCH_LIMITATION_DISCLOSED` and checkbox unchanged. All individual R2/adjustedR2 distributions and ten paired-model differences verified. The identity alpha=mean(y)-beta mean(f) confirms negative mean intercepts with positive mean excess and high centered fit. The mean of dependent alpha estimates is descriptive, not an iid population-mean test. Source: `scripts/research_phase2c.py`, `scripts/phase2c_reference.py`; numerical calculation commit `ac478bb59027e27212c7f5da28846dd1107434cb`. Evidence `../../outputs/audit/phase2c/PHASE2C_REGRESSION_VERIFICATION.md`, portfolio/model/difference/dependence CSVs and source manifest. Same authenticated Phase2B publications/parents, no value change or new publication.45targeted/366full PASS,90.68%coverage; exact hashes and numerical errors recorded. Manuscript consequence: support qualified descriptive tables only; economic/PIT/provider limits persist. Reviewer `PENDING`.

#### [x] AP7 — Is Newey–West lag 3 appropriate for these monthly series?

- **Phase / severity from initial audit:** 2 / High; **status:** `RESEARCH_LIMITATION_DISCLOSED`.
- **Why this matters / failure mode:** Is Newey–West lag 3 appropriate for these monthly series? A mismatch can change empirical interpretation or make a paper claim stronger than the underlying data support; do not presume a defect before examining the archived outputs.
- **Inspect first:** `regression/engine.py, diagnostics and dated residual series`. Resolve these to actual paths on the checked-out commit; record function names/line ranges rather than assuming they are unchanged.
- **Detailed verification and candidate correction:** Check monthly residual ACF and HAC choices 0,3,6 and 12 where enough observations exist. Record estimator implementation, finite sample and differences in t/p values without choosing lags based on desired significance.
- **Initial audit requested:** Examine residual autocorrelation and lag sensitivity.
- **Deliverable:** `outputs/audit/hac_lag_sensitivity.csv` (or an equivalent, documented path); record source input hashes, exact calculations and explanatory caveats. **Never overwrite old frozen result artifacts.**
- **Acceptance gate:** Inference robustness is reported alongside the pre-existing lag-3 choice.
- **Progress record:** owner `Codex`; result `RESEARCH_LIMITATION_DISCLOSED`; baseline `10b3dc353f604ef332f55c153b093d1628a4ff7f`; source checkpoint `62343e686475552a0b629d63b5445a6203ea90f7`; evidence `outputs/audit/phase2/PHASE2_ASSET_PRICING_VALIDATION.md#ap7` and issue-results CSV; independent check `Independent deterministic sandwich tests pass for L0/3/6/12. Authentic archived residual/score matrices support the predeclared four-lag sensitivity and residual ACF summaries.`; numerical result `CAPM rejection counts81/105/106/109; FF584/114/116/118 at lags0/3/6/12; n68-102. No missing or repeated calendar months in retained archived regression samples.`; tests `343 passed,90.58% coverage;35 targeted`; paper consequence `Report estimator and sensitivity alongside original lag3; greater lag is not automatically more conservative or evidence of robustness.`; remaining limitation `Lag3 is preserved, not optimized. Asymptotic HAC accuracy, short sample and partial-final-period issues remain; original matrices carry frequency defect.`; independent reviewer `PENDING`.


- **Phase2B evidence (1 November2026):** previous `RESEARCH_LIMITATION_DISCLOSED`; current `RESEARCH_LIMITATION_DISCLOSED`. Source `regression/engine.py::fit_regression; scripts/research_phase2b.py::reference_fit`; empirical source commit `291447199fe603f0168d972ee77b88c4d949f205`. All1230 fits independently reproduce HAC3; lags0/3/6/12 checked; primary CAPM counts7/8/10/15,FF5 6/8/16/22. Remaining limitation/manuscript consequence: Bartlett,n/(n-k),two-sided Student-t/95% CI retained; no finite-sample validity or FDR certification. Evidence: `../../outputs/audit/phase2b/PHASE2B_EMPIRICAL_CORRECTION_REPORT.md`, issue CSV, source manifest and bound numerical/case evidence. Tests37targeted/358full PASS,90.68%coverage; independent returns/regressions/hashes PASS. New factor `factor-4ddee9ac6fb45cedfd62a2cc68676b58`; primary pricing `asset-pricing-d60bee7310b34976c80372a0f0f29e21`. Original hashes and values preserved; exact before/after/horizon distinctions in reconciliation CSVs. Reviewer `PENDING`.


- **Phase2C independent-referee evidence (1 November2026):** status `RESEARCH_LIMITATION_DISCLOSED` and checkbox unchanged. Independent pivoted QR/triangular bread and score-by-score Bartlett covariance reproduce all615primary and615supplementary fits; lags0/3/6/12 agree. Allprimary designs fullrank; standardized condition max3.391,VIFmax3.105. Correct nominal HAC/t arithmetic does not establish exact finite-sample validity. Source: `scripts/research_phase2c.py`, `scripts/phase2c_reference.py`; numerical calculation commit `ac478bb59027e27212c7f5da28846dd1107434cb`. Evidence `../../outputs/audit/phase2c/PHASE2C_REGRESSION_VERIFICATION.md`, portfolio/model/difference/dependence CSVs and source manifest. Same authenticated Phase2B publications/parents, no value change or new publication.45targeted/366full PASS,90.68%coverage; exact hashes and numerical errors recorded. Manuscript consequence: support qualified descriptive tables only; economic/PIT/provider limits persist. Reviewer `PENDING`.

#### [x] AP8 — Do the 123 tests share correlated test assets?

- **Phase / severity from initial audit:** 2 / High; **status:** `RESEARCH_LIMITATION_DISCLOSED`.
- **Why this matters / failure mode:** Do the 123 tests share correlated test assets? A mismatch can change empirical interpretation or make a paper claim stronger than the underlying data support; do not presume a defect before examining the archived outputs.
- **Inspect first:** `asset pricing residual series; factor holdings`. Resolve these to actual paths on the checked-out commit; record function names/line ranges rather than assuming they are unchanged.
- **Detailed verification and candidate correction:** Compute return/residual correlation between the 123 overlapping portfolios, identify repeated constituents and correlated test errors, and explain why the shares of significant intercepts are not independent trials.
- **Initial audit requested:** Evaluate cross-portfolio dependence and reject naïve independent-test interpretations.
- **Deliverable:** `outputs/audit/test_asset_dependence.csv` (or an equivalent, documented path); record source input hashes, exact calculations and explanatory caveats. **Never overwrite old frozen result artifacts.**
- **Acceptance gate:** Inference discussion reflects correlation and effective test-family structure.
- **Progress record:** owner `Codex`; result `RESEARCH_LIMITATION_DISCLOSED`; baseline `10b3dc353f604ef332f55c153b093d1628a4ff7f`; source checkpoint `62343e686475552a0b629d63b5445a6203ea90f7`; evidence `outputs/audit/phase2/PHASE2_ASSET_PRICING_VALIDATION.md#ap8` and issue-results CSV; independent check `All7503 raw-return pairs measured: mean .76588985, median .77705309, 47 abs correlations>.95; six equal-return pairs. Five residual correlation summaries also computed.`; numerical result `Mean archived residual correlation ranges .73737-.81182, depending on model. Shared periods/sorts, repeated legs and aliases create dependence.`; tests `343 passed,90.58% coverage;35 targeted`; paper consequence `Individual regression uncertainty is distinct from uncertainty about a collection of123 dependent regressions.`; remaining limitation `Original residual dependence partly reflects frequency error. Pairwise shared samples vary, and equality on overlap is not an assertion about unobserved dates.`; independent reviewer `PENDING`.


- **Phase2B evidence (1 November2026):** previous `RESEARCH_LIMITATION_DISCLOSED`; current `RESEARCH_LIMITATION_DISCLOSED`. Source `PHASE2B_INDEPENDENT_VALIDATION.json::return_correlation/residual_correlation`; empirical source commit `291447199fe603f0168d972ee77b88c4d949f205`. 7503return correlations mean .776274,median .792259;51>.95;six exact pairs; residual dependence documented. Remaining limitation/manuscript consequence: Do not count123assets as independent trials; univariate HAC does not remove cross-asset dependence. Evidence: `../../outputs/audit/phase2b/PHASE2B_EMPIRICAL_CORRECTION_REPORT.md`, issue CSV, source manifest and bound numerical/case evidence. Tests37targeted/358full PASS,90.68%coverage; independent returns/regressions/hashes PASS. New factor `factor-4ddee9ac6fb45cedfd62a2cc68676b58`; primary pricing `asset-pricing-d60bee7310b34976c80372a0f0f29e21`. Original hashes and values preserved; exact before/after/horizon distinctions in reconciliation CSVs. Reviewer `PENDING`.


- **Phase2C independent-referee evidence (1 November2026):** status `RESEARCH_LIMITATION_DISCLOSED` and checkbox unchanged. Six exact duplicate return pairs and dependent factor legs persist; model residual mean correlations .293-.332. All123asset common residual matrices have67dates/rank66, so naive inverse-covariance joint alpha tests are unsupported. Holm uses no test-independence assumption but depends on valid marginal tests. Source: `scripts/research_phase2c.py`, `scripts/phase2c_reference.py`; numerical calculation commit `ac478bb59027e27212c7f5da28846dd1107434cb`. Evidence `../../outputs/audit/phase2c/PHASE2C_REGRESSION_VERIFICATION.md`, portfolio/model/difference/dependence CSVs and source manifest. Same authenticated Phase2B publications/parents, no value change or new publication.45targeted/366full PASS,90.68%coverage; exact hashes and numerical errors recorded. Manuscript consequence: support qualified descriptive tables only; economic/PIT/provider limits persist. Reviewer `PENDING`.

#### [x] AP9 — Are the FF5, Carhart and q specifications actually estimated on identical dates and portfolio populations?

- **Phase / severity from initial audit:** 2 / Medium; **status:** `CONFIRMED_ERROR_FIXED`.
- **Why this matters / failure mode:** Are the FF5, Carhart and q specifications actually estimated on identical dates and portfolio populations? A mismatch can change empirical interpretation or make a paper claim stronger than the underlying data support; do not presume a defect before examining the archived outputs.
- **Inspect first:** `asset pricing model comparisons`. Resolve these to actual paths on the checked-out commit; record function names/line ranges rather than assuming they are unchanged.
- **Detailed verification and candidate correction:** Match portfolio IDs, sample start/end, observation counts, risk-free rate and input timestamps across CAPM/FF3/Carhart/FF5/q; provide complete-case intersection comparison where required.
- **Initial audit requested:** Confirm matched-sample comparison.
- **Deliverable:** `outputs/audit/model_common_sample_audit.csv` (or an equivalent, documented path); record source input hashes, exact calculations and explanatory caveats. **Never overwrite old frozen result artifacts.**
- **Acceptance gate:** Fit comparisons reflect genuinely matched assets and dates or are labeled non-comparable.
- **Progress record:** owner `Codex`; result `RESEARCH_LIMITATION_DISCLOSED`; baseline `10b3dc353f604ef332f55c153b093d1628a4ff7f`; source checkpoint `62343e686475552a0b629d63b5445a6203ea90f7`; evidence `outputs/audit/phase2/PHASE2_ASSET_PRICING_VALIDATION.md#ap9` and issue-results CSV; independent check `All five models cover123 IDs, but102 asset IDs use different month samples across models. Same-calendar comparisons computed both with historical inputs and interval-aligned inputs.`; numerical result `Historical CAPM n68-102 vs FF5 n68-78; common sample n68-78 for all models of each asset. Historical matched CAPM mean adjustedR2=.08291435, not .06343952.`; tests `343 passed,90.58% coverage;35 targeted`; paper consequence `Original cross-model table is not a like-for-like monthly comparison; retain historical values and present supplementary common-sample results separately.`; remaining limitation `Same-sample controls isolate composition effects but do not fix D8/PIT/vintage. No default estimator/sample policy was silently replaced.`; independent reviewer `PENDING`.


- **Phase2B evidence (1 November2026):** previous `RESEARCH_LIMITATION_DISCLOSED`; current `CONFIRMED_ERROR_FIXED`. Source `factors/holding.py::matched_sample; scripts/research_phase2b.py::pricing`; empirical source commit `291447199fe603f0168d972ee77b88c4d949f205`. 123assets identical per-asset five-model dates,N67-77,9441 observations/model,no month gaps. Model-specific publication separate. Remaining limitation/manuscript consequence: Per-asset calendars differ across assets; supplementary model-specific samples are not primary fair model rankings. Evidence: `../../outputs/audit/phase2b/PHASE2B_EMPIRICAL_CORRECTION_REPORT.md`, issue CSV, source manifest and bound numerical/case evidence. Tests37targeted/358full PASS,90.68%coverage; independent returns/regressions/hashes PASS. New factor `factor-4ddee9ac6fb45cedfd62a2cc68676b58`; primary pricing `asset-pricing-d60bee7310b34976c80372a0f0f29e21`. Original hashes and values preserved; exact before/after/horizon distinctions in reconciliation CSVs. Reviewer `PENDING`.


- **Phase2C independent-referee evidence (1 November2026):** status `CONFIRMED_ERROR_FIXED` and checkbox unchanged. Full independent primary date/interval reconstruction matches all615fits and11352returns. Every model uses the same per-asset dates; monthly cycles have19-23sessions, not identical duration. Sensitivity comparisons refit baseline on identical109asset dates; no effect is attributed to changed sample composition. Among retained assets57lose163cycles/model and44have internal month gaps; diagnostic HAC lags count retained observations. Primary/supplementary official dates remain gap-free. Source: `scripts/research_phase2c.py`, `scripts/phase2c_reference.py`; numerical calculation commit `ac478bb59027e27212c7f5da28846dd1107434cb`. Evidence `../../outputs/audit/phase2c/PHASE2C_REGRESSION_VERIFICATION.md`, portfolio/model/difference/dependence CSVs and source manifest. Same authenticated Phase2B publications/parents, no value change or new publication.45targeted/366full PASS,90.68%coverage; exact hashes and numerical errors recorded. Manuscript consequence: support qualified descriptive tables only; economic/PIT/provider limits persist. Reviewer `PENDING`.

#### [ ] AP10 — Why do H1 and H3 remain inconclusive despite the project containing a large factor registry and rolling regressions?

- **Phase / severity from initial audit:** 2 / High; **status:** `SOURCE_EVIDENCE_BLOCKED`.
- **Why this matters / failure mode:** Why do H1 and H3 remain inconclusive despite the project containing a large factor registry and rolling regressions? A mismatch can change empirical interpretation or make a paper claim stronger than the underlying data support; do not presume a defect before examining the archived outputs.
- **Inspect first:** `hypothesis registry; rolling regressions; original manifests`. Resolve these to actual paths on the checked-out commit; record function names/line ranges rather than assuming they are unchanged.
- **Detailed verification and candidate correction:** Find the frozen hypothesis definitions, complete factor-level cost comparisons and original rolling-decision rules for H1/H3. Recover authentic artifacts; do not recreate a preregistration after observing results.
- **Initial audit requested:** Recover original decision artifacts if possible, without inventing tests.
- **Deliverable:** `outputs/audit/hypothesis_h1_h3_provenance.md` (or an equivalent, documented path); record source input hashes, exact calculations and explanatory caveats. **Never overwrite old frozen result artifacts.**
- **Acceptance gate:** H1/H3 become supported/not-supported only with reconstructable preregistered criteria; otherwise remain inconclusive.
- **Progress record:** owner `Codex`; result `SOURCE_EVIDENCE_BLOCKED`; baseline `10b3dc353f604ef332f55c153b093d1628a4ff7f`; source checkpoint `62343e686475552a0b629d63b5445a6203ea90f7`; evidence `outputs/audit/phase2/PHASE2_ASSET_PRICING_VALIDATION.md#ap10` and issue-results CSV; independent check `H1/H3 remain inconclusive. Authentic rolling coefficients exist, but complete original cost/FDR and temporal-stability decision artifacts were not located. Specification labels policy PROPOSED/OWNER APPROVAL REQUIRED.`; numerical result `Earlier H3 null is stable relations versus material instability; later paper phrases H3 as stability. Approved hypothesis direction and decision rule are not authenticated.`; tests `343 passed,90.58% coverage;35 targeted`; paper consequence `Retain inconclusive status and flag wording/approval mismatch for later author/reviewer reconciliation; do not revise hypotheses after observing outcomes.`; remaining limitation `Missing approval/decision evidence cannot be recreated ex post. Existing coefficient p-values or new exploratory BH summaries do not complete H1/H3.`; independent reviewer `PENDING`.


### Phase 3 — Eight portfolios and walk-forward ML


- **Phase2B evidence (1 November2026):** previous `SOURCE_EVIDENCE_BLOCKED`; current `SOURCE_EVIDENCE_BLOCKED`. Source `unchanged Phase2 H1/H3 original-record evidence`; empirical source commit `291447199fe603f0168d972ee77b88c4d949f205`. No authentic new owner approval or original H1/H3 decision evidence located. Remaining limitation/manuscript consequence: New regressions cannot invent missing authority or retrospective hypothesis success. Evidence: `../../outputs/audit/phase2b/PHASE2B_EMPIRICAL_CORRECTION_REPORT.md`, issue CSV, source manifest and bound numerical/case evidence. Tests37targeted/358full PASS,90.68%coverage; independent returns/regressions/hashes PASS. New factor `factor-4ddee9ac6fb45cedfd62a2cc68676b58`; primary pricing `asset-pricing-d60bee7310b34976c80372a0f0f29e21`. Original hashes and values preserved; exact before/after/horizon distinctions in reconciliation CSVs. Reviewer `PENDING`.

#### [x] P1 — Does maximum drawdown include initial wealth?

- **Phase / severity from initial audit:** 3 / Critical; **status:** `VERIFIED_CORRECT`.
- **Why this matters / failure mode:** Does maximum drawdown include initial wealth? A mismatch can change empirical interpretation or make a paper claim stronger than the underlying data support; do not presume a defect before examining the archived outputs.
- **Inspect first:** `src/institutional_factor_platform/risk/metrics.py; monthly portfolio return parquet`. Resolve these to actual paths on the checked-out commit; record function names/line ranges rather than assuming they are unchanged.
- **Detailed verification and candidate correction:** Construct initial NAV=1 before return observations; test [-20%,+10%], strictly falling, flat and rebound paths. Independently recompute eight strategies from frozen net returns, compare old/new max drawdown and propagate genuine changes into a new output version.
- **Initial audit requested:** Correct and independently rerun the risk metric.
- **Deliverable:** `outputs/audit/mdd_before_after.csv` (or an equivalent, documented path); record source input hashes, exact calculations and explanatory caveats. **Never overwrite old frozen result artifacts.**
- **Acceptance gate:** Both function tests and all eight authentic empirical MDDs reconcile; historical published numbers remain archived.
- **Progress record:** owner `Codex`; result `SOURCE_EVIDENCE_BLOCKED`; baseline SHA `4e7fbdc380b8042db72e9c628260f60077a205ef`; code/evidence checkpoint `ef339ab`; tests `PHASE1_TEST_RESULTS.txt`; evidence `../../outputs/audit/phase1/PHASE1_FINANCIAL_DATA_VALIDATION.md#p1`; numerical change `no historical before/after available; see reconciliation CSV`; research-paper impact `Published maximum-diversification -5.43% is neither disproved nor verified. Related Calmar may change only if actual path establishes changed MDD.`; independent reviewer `PENDING`.


- **Phase3 complete validation (1 November2026):** previous `SOURCE_EVIDENCE_BLOCKED`; current `VERIFIED_CORRECT`. Exact source `risk/metrics.py::drawdown,maximum_drawdown` under `src/institutional_factor_platform` unless explicitly scripts/config. All8actual BASE paths reconcile from NAV1; initial-NAV effect0 for all historical minima. Original maximum-diversification MDD-.05432343856 is correct on its historical path. Limit/manuscript consequence: New MDD belongs to changed inputs/sample; do not claim -5.43%was disproved. Evidence `../../outputs/audit/phase3/PHASE3_COMPLETE_VALIDATION.md`, issue/reconciliation files and full source manifest. Portfolio/MLfit source `0fe382f`; MLmetric-only source `9df5455`; final evidence is the containing commit.6new regressions,91targeted and372full pass/90.62%; originals preserved; all before/after values and hashes recorded. Reviewer `PENDING`.

#### [x] P2 — Do the stated one-way transaction costs match the actual L1 implementation?

- **Phase / severity from initial audit:** 3 / Critical; **status:** `VERIFIED_CORRECT`.
- **Why this matters / failure mode:** Do the stated one-way transaction costs match the actual L1 implementation? A mismatch can change empirical interpretation or make a paper claim stronger than the underlying data support; do not presume a defect before examining the archived outputs.
- **Inspect first:** `src/institutional_factor_platform/backtest/costs.py; config/portfolio.yaml; frozen transaction parquet`. Resolve these to actual paths on the checked-out commit; record function names/line ranges rather than assuming they are unchanged.
- **Detailed verification and candidate correction:** Define one-way turnover=0.5×sum(abs(trade)) for fully invested rebalances; compare current cost expression commission*L1 + half-spread*L1 + slippage*L1 with claimed 5/10/20-bps cost labels. Show buy, sell, full switch, initial deployment, and drift rebalance examples. Reconcile the original trade-by-trade fees without automatically halving costs or retuning.
- **Initial audit requested:** Derive and test the fee convention.
- **Deliverable:** `outputs/audit/fee_units_and_reconciliation.csv` (or an equivalent, documented path); record source input hashes, exact calculations and explanatory caveats. **Never overwrite old frozen result artifacts.**
- **Acceptance gate:** Cost convention is explicit and every fee equals the recorded trades, with any convention error versioned and propagated.
- **Progress record:** owner `Codex`; result `SOURCE_EVIDENCE_BLOCKED`; baseline SHA `4e7fbdc380b8042db72e9c628260f60077a205ef`; code/evidence checkpoint `ef339ab`; tests `PHASE1_TEST_RESULTS.txt`; evidence `../../outputs/audit/phase1/PHASE1_FINANCIAL_DATA_VALIDATION.md#p2`; numerical change `no historical before/after available; see reconciliation CSV`; research-paper impact `Use explicit per-traded-side rate; half-L1 is one-way rebalance turnover only for self-financing trades, not initial cash deployment. Fixed impact is bundled flat slippage, nonlinear impact0.`; independent reviewer `PENDING`.


- **Phase3 complete validation (1 November2026):** previous `SOURCE_EVIDENCE_BLOCKED`; current `VERIFIED_CORRECT`. Exact source `backtest/costs.py::TransactionCostModel.estimate;backtest/engine.py::run_backtest` under `src/institutional_factor_platform` unless explicitly scripts/config. Actual old/new trade,fee,drift and NAV identities reconcile for all5/10/20bps scenarios. InitialL1=1,BASEfee=.001; full switchL1=2 costs20bps. Limit/manuscript consequence: Half-L1 is self-financing one-way turnover, not initial deployment. Rates are per-L1/per-traded-side; no unjustified halving. Evidence `../../outputs/audit/phase3/PHASE3_COMPLETE_VALIDATION.md`, issue/reconciliation files and full source manifest. Portfolio/MLfit source `0fe382f`; MLmetric-only source `9df5455`; final evidence is the containing commit.6new regressions,91targeted and372full pass/90.62%; originals preserved; all before/after values and hashes recorded. Reviewer `PENDING`.

#### [x] P3 — Are eight strategies evaluated on exactly the same portfolio returns and rebalance dates?

- **Phase / severity from initial audit:** 3 / High; **status:** `VERIFIED_CORRECT`.
- **Why this matters / failure mode:** Are eight strategies evaluated on exactly the same portfolio returns and rebalance dates? A mismatch can change empirical interpretation or make a paper claim stronger than the underlying data support; do not presume a defect before examining the archived outputs.
- **Inspect first:** `portfolio manifests; src/institutional_factor_platform/portfolio/service.py`. Resolve these to actual paths on the checked-out commit; record function names/line ranges rather than assuming they are unchanged.
- **Detailed verification and candidate correction:** Compare all eight strategy return matrices, factor-asset IDs, calendar dates, training windows, rebalance dates, benchmark and risk-free settings. Detect asset drift and unequal time horizons.
- **Initial audit requested:** Verify matched data and accounting.
- **Deliverable:** `outputs/audit/strategy_calendar_comparison.csv` (or an equivalent, documented path); record source input hashes, exact calculations and explanatory caveats. **Never overwrite old frozen result artifacts.**
- **Acceptance gate:** Like-for-like comparison is verified or incomparable strategies are labeled.
- **Progress record:** owner `Codex`; result `UNASSESSED`; baseline SHA `TBD`; updated SHA `TBD`; test `TBD`; evidence link `TBD`; numerical change `TBD`; research-paper impact `TBD`; independent reviewer `PENDING`.


- **Phase3 complete validation (1 November2026):** previous `UNASSESSED`; current `VERIFIED_CORRECT`. Exact source `portfolio/service.py::_return_matrix,compute_and_publish` under `src/institutional_factor_platform` unless explicitly scripts/config. Eight methods share123sleeves,36-cycle history and identical32original/31corrected test cycles; objectives legitimately differ. Limit/manuscript consequence: Input/sample/cash changes must not be attributed to a single metric fix; pricing coefficients are not optimizer inputs. Evidence `../../outputs/audit/phase3/PHASE3_COMPLETE_VALIDATION.md`, issue/reconciliation files and full source manifest. Portfolio/MLfit source `0fe382f`; MLmetric-only source `9df5455`; final evidence is the containing commit.6new regressions,91targeted and372full pass/90.62%; originals preserved; all before/after values and hashes recorded. Reviewer `PENDING`.

#### [x] P4 — Do factor-portfolio test assets represent investable returns?

- **Phase / severity from initial audit:** 3 / High; **status:** `RESEARCH_LIMITATION_DISCLOSED`.
- **Why this matters / failure mode:** Do factor-portfolio test assets represent investable returns? A mismatch can change empirical interpretation or make a paper claim stronger than the underlying data support; do not presume a defect before examining the archived outputs.
- **Inspect first:** `factor portfolio definitions, portfolio service, docs/LIMITATIONS.md`. Resolve these to actual paths on the checked-out commit; record function names/line ranges rather than assuming they are unchanged.
- **Detailed verification and candidate correction:** Identify portfolio building blocks as research factor quantiles rather than directly traded products. Document whether each quantile requires short legs, stale weights, infeasible component trades or omitted constituent transaction costs.
- **Initial audit requested:** Disclose constituent and short-leg implementation constraints.
- **Deliverable:** `outputs/audit/factor_portfolio_investability.md` (or an equivalent, documented path); record source input hashes, exact calculations and explanatory caveats. **Never overwrite old frozen result artifacts.**
- **Acceptance gate:** Reported results are correctly labeled diagnostic/theoretical rather than implementable alpha absent execution evidence.
- **Progress record:** owner `Codex`; result `UNASSESSED`; baseline SHA `TBD`; updated SHA `TBD`; test `TBD`; evidence link `TBD`; numerical change `TBD`; research-paper impact `TBD`; independent reviewer `PENDING`.


- **Phase3 complete validation (1 November2026):** previous `UNASSESSED`; current `RESEARCH_LIMITATION_DISCLOSED`. Exact source `portfolio/service.py::_return_matrix` under `src/institutional_factor_platform` unless explicitly scripts/config. Optimizer invests in123constructed long-only quantiles, not direct487equities or long-short spreads. Limit/manuscript consequence: Overlapping sleeves and omitted inner constituent fees,liquidity/capacity prevent an executable-alpha claim. Evidence `../../outputs/audit/phase3/PHASE3_COMPLETE_VALIDATION.md`, issue/reconciliation files and full source manifest. Portfolio/MLfit source `0fe382f`; MLmetric-only source `9df5455`; final evidence is the containing commit.6new regressions,91targeted and372full pass/90.62%; originals preserved; all before/after values and hashes recorded. Reviewer `PENDING`.

#### [x] P5 — Are equal-weight and optimized strategies evaluated with identical costs and initial deployment?

- **Phase / severity from initial audit:** 3 / High; **status:** `VERIFIED_CORRECT`.
- **Why this matters / failure mode:** Are equal-weight and optimized strategies evaluated with identical costs and initial deployment? A mismatch can change empirical interpretation or make a paper claim stronger than the underlying data support; do not presume a defect before examining the archived outputs.
- **Inspect first:** `backtest/engine.py, costs.py and allocations/transactions files`. Resolve these to actual paths on the checked-out commit; record function names/line ranges rather than assuming they are unchanged.
- **Detailed verification and candidate correction:** Confirm initial cash→weights, rebalance pretrade drift, one-way trade notional, cost deduction, buy/hold cash assumptions, budget balance and equivalent costs for 1/N and optimized methods. Test a 2-asset hand-calculated path.
- **Initial audit requested:** Reconcile trading decisions, pretrade holdings and fees.
- **Deliverable:** `outputs/audit/portfolio_accounting_identity.csv` (or an equivalent, documented path); record source input hashes, exact calculations and explanatory caveats. **Never overwrite old frozen result artifacts.**
- **Acceptance gate:** All eight reconciled NAV paths match modeled fees; treatment is consistent.
- **Progress record:** owner `Codex`; result `UNASSESSED`; baseline SHA `TBD`; updated SHA `TBD`; test `TBD`; evidence link `TBD`; numerical change `TBD`; research-paper impact `TBD`; independent reviewer `PENDING`.


- **Phase3 complete validation (1 November2026):** previous `UNASSESSED`; current `VERIFIED_CORRECT`. Exact source `backtest/engine.py::run_backtest;portfolio/allocations.py::equal_weight` under `src/institutional_factor_platform` unless explicitly scripts/config. EW and optimized methods start from cash/NAV1, charge initial deployment and use identical drift/fees. All16old/new method scenario comparisons have identical weights and monotonic fee effects. Limit/manuscript consequence: External SPY is an uncosted proxy, not an executed net benchmark. Evidence `../../outputs/audit/phase3/PHASE3_COMPLETE_VALIDATION.md`, issue/reconciliation files and full source manifest. Portfolio/MLfit source `0fe382f`; MLmetric-only source `9df5455`; final evidence is the containing commit.6new regressions,91targeted and372full pass/90.62%; originals preserved; all before/after values and hashes recorded. Reviewer `PENDING`.

#### [x] P6 — Why does CVaR have the highest observed cumulative return, 83.17%, despite not optimizing mean return?

- **Phase / severity from initial audit:** 3 / High; **status:** `RESEARCH_LIMITATION_DISCLOSED`.
- **Why this matters / failure mode:** Why does CVaR have the highest observed cumulative return, 83.17%, despite not optimizing mean return? A mismatch can change empirical interpretation or make a paper claim stronger than the underlying data support; do not presume a defect before examining the archived outputs.
- **Inspect first:** `optimization/engine.py; portfolio weights; scenarios`. Resolve these to actual paths on the checked-out commit; record function names/line ranges rather than assuming they are unchanged.
- **Detailed verification and candidate correction:** Reconstruct CVaR weights, factor exposures, turnover and worst-case outcomes by date; verify optimizer only minimizes trailing historical tail-loss and did not use future window scenarios. Attribute 83.17% gain to observed exposures rather than assuming objective rewards return.
- **Initial audit requested:** Review allocation concentration and the short sample's historical exposures.
- **Deliverable:** `outputs/audit/cvar_exposure_attribution.csv` (or an equivalent, documented path); record source input hashes, exact calculations and explanatory caveats. **Never overwrite old frozen result artifacts.**
- **Acceptance gate:** CVaR return and risk are reconciled and short-sample interpretation is qualified.
- **Progress record:** owner `Codex`; result `UNASSESSED`; baseline SHA `TBD`; updated SHA `TBD`; test `TBD`; evidence link `TBD`; numerical change `TBD`; research-paper impact `TBD`; independent reviewer `PENDING`.


- **Phase3 complete validation (1 November2026):** previous `UNASSESSED`; current `RESEARCH_LIMITATION_DISCLOSED`. Exact source `optimization/engine.py::_cvar,optimize` under `src/institutional_factor_platform` unless explicitly scripts/config. Original CVaR.83173655874/Sharpe1.666656947 reproduces; cash-only repair on old path1.378572122; corrected inputs.73684195642/1.252326967. Scenario objectives and feasible weights reconcile. Limit/manuscript consequence: High observed return does not show future information or a return-maximizing CVaR objective; short-window ranking remains descriptive. Evidence `../../outputs/audit/phase3/PHASE3_COMPLETE_VALIDATION.md`, issue/reconciliation files and full source manifest. Portfolio/MLfit source `0fe382f`; MLmetric-only source `9df5455`; final evidence is the containing commit.6new regressions,91targeted and372full pass/90.62%; originals preserved; all before/after values and hashes recorded. Reviewer `PENDING`.

#### [x] P7 — Why is the portfolio test only about 32 months?

- **Phase / severity from initial audit:** 3 / High; **status:** `RESEARCH_LIMITATION_DISCLOSED`.
- **Why this matters / failure mode:** Why is the portfolio test only about 32 months? A mismatch can change empirical interpretation or make a paper claim stronger than the underlying data support; do not presume a defect before examining the archived outputs.
- **Inspect first:** `portfolio dates and net paths`. Resolve these to actual paths on the checked-out commit; record function names/line ranges rather than assuming they are unchanged.
- **Detailed verification and candidate correction:** Calculate portfolio test sample duration/effective rebalance count; compare ranking stability by calendar segments or subperiods only where observations suffice. Avoid unjustified bootstrap precision from 32 months.
- **Initial audit requested:** Evaluate statistical power and regime dependence.
- **Deliverable:** `outputs/audit/portfolio_sample_uncertainty.md` (or an equivalent, documented path); record source input hashes, exact calculations and explanatory caveats. **Never overwrite old frozen result artifacts.**
- **Acceptance gate:** Rankings are treated as sample-specific rather than persistent outperformance.
- **Progress record:** owner `Codex`; result `UNASSESSED`; baseline SHA `TBD`; updated SHA `TBD`; test `TBD`; evidence link `TBD`; numerical change `TBD`; research-paper impact `TBD`; independent reviewer `PENDING`.


- **Phase3 complete validation (1 November2026):** previous `UNASSESSED`; current `RESEARCH_LIMITATION_DISCLOSED`. Exact source `portfolio/service.py;authenticated net-return paths` under `src/institutional_factor_platform` unless explicitly scripts/config. Original32cycles become31full corrected cycles after terminal partial exclusion. Limit/manuscript consequence: Short selected window cannot establish persistence; no new history or bootstrap grid. Evidence `../../outputs/audit/phase3/PHASE3_COMPLETE_VALIDATION.md`, issue/reconciliation files and full source manifest. Portfolio/MLfit source `0fe382f`; MLmetric-only source `9df5455`; final evidence is the containing commit.6new regressions,91targeted and372full pass/90.62%; originals preserved; all before/after values and hashes recorded. Reviewer `PENDING`.

#### [ ] P8 — Does the CVaR optimizer use genuine past observations exclusively?

- **Phase / severity from initial audit:** 3 / Medium; **status:** `SOURCE_EVIDENCE_BLOCKED`.
- **Why this matters / failure mode:** Does the CVaR optimizer use genuine past observations exclusively? A mismatch can change empirical interpretation or make a paper claim stronger than the underlying data support; do not presume a defect before examining the archived outputs.
- **Inspect first:** `portfolio/service.py; optimizer/engine.py`. Resolve these to actual paths on the checked-out commit; record function names/line ranges rather than assuming they are unchanged.
- **Detailed verification and candidate correction:** For every rebalance, verify optimizer scenario matrix and risk estimates use returns strictly before trading date; inject a future observation as an adversarial temporal test.
- **Initial audit requested:** Check scenario timing at every rebalance.
- **Deliverable:** `outputs/audit/cvar_timing_test_record.md` (or an equivalent, documented path); record source input hashes, exact calculations and explanatory caveats. **Never overwrite old frozen result artifacts.**
- **Acceptance gate:** No forward scenario leaks into investment decisions.
- **Progress record:** owner `Codex`; result `UNASSESSED`; baseline SHA `TBD`; updated SHA `TBD`; test `TBD`; evidence link `TBD`; numerical change `TBD`; research-paper impact `TBD`; independent reviewer `PENDING`.


- **Phase3 complete validation (1 November2026):** previous `UNASSESSED`; current `SOURCE_EVIDENCE_BLOCKED`. Exact source `portfolio/service.py::allocator;backtest/engine.py::run_backtest` under `src/institutional_factor_platform` unless explicitly scripts/config. Every optimizer uses36observations before evaluated return; training_end<=holding_start and no future array row. Limit/manuscript consequence: Strict pre-close availability/execution not proved: latest training mark can equal holding start; allocations label exits and sources use UTC-day availability. D4/V1remain. Evidence `../../outputs/audit/phase3/PHASE3_COMPLETE_VALIDATION.md`, issue/reconciliation files and full source manifest. Portfolio/MLfit source `0fe382f`; MLmetric-only source `9df5455`; final evidence is the containing commit.6new regressions,91targeted and372full pass/90.62%; originals preserved; all before/after values and hashes recorded. Reviewer `PENDING`.

#### [x] P9 — Are maximum-Sharpe and mean–variance optimizers subject to identical feasible sets?

- **Phase / severity from initial audit:** 3 / Medium; **status:** `VERIFIED_CORRECT`.
- **Why this matters / failure mode:** Are maximum-Sharpe and mean–variance optimizers subject to identical feasible sets? A mismatch can change empirical interpretation or make a paper claim stronger than the underlying data support; do not presume a defect before examining the archived outputs.
- **Inspect first:** `optimization/engine.py; config/portfolio.yaml`. Resolve these to actual paths on the checked-out commit; record function names/line ranges rather than assuming they are unchanged.
- **Detailed verification and candidate correction:** Inspect constraint sets, objectives, estimation windows, annualization, risk-free input and optimizer convergence for all eight models. Compare feasible sets explicitly; avoid presenting different objectives as a controlled single-variable experiment.
- **Initial audit requested:** Inspect objectives, risk-free assumptions and constraints.
- **Deliverable:** `outputs/audit/optimizer_fairness_matrix.csv` (or an equivalent, documented path); record source input hashes, exact calculations and explanatory caveats. **Never overwrite old frozen result artifacts.**
- **Acceptance gate:** Constraint/frequency differences are justified and documented.
- **Progress record:** owner `Codex`; result `UNASSESSED`; baseline SHA `TBD`; updated SHA `TBD`; test `TBD`; evidence link `TBD`; numerical change `TBD`; research-paper impact `TBD`; independent reviewer `PENDING`.


- **Phase3 complete validation (1 November2026):** previous `UNASSESSED`; current `VERIFIED_CORRECT`. Exact source `optimization/engine.py::optimize;constraints/models.py;optimization/covariance.py` under `src/institutional_factor_platform` unless explicitly scripts/config. Feasible long-only fully-invested weights,positive Ledoit-Wolf covariances and all expected-return/volatility/objective identities reconcile. Limit/manuscript consequence: Optimizer maximum-Sharpe defaultRF0 retained; performance cash differs. No global-optimum certificate for every nonconvex solver. Evidence `../../outputs/audit/phase3/PHASE3_COMPLETE_VALIDATION.md`, issue/reconciliation files and full source manifest. Portfolio/MLfit source `0fe382f`; MLmetric-only source `9df5455`; final evidence is the containing commit.6new regressions,91targeted and372full pass/90.62%; originals preserved; all before/after values and hashes recorded. Reviewer `PENDING`.

#### [x] P10 — Is “fixed impact allowance” an empirical market-impact estimate?

- **Phase / severity from initial audit:** 3 / Medium; **status:** `RESEARCH_LIMITATION_DISCLOSED`.
- **Why this matters / failure mode:** Is “fixed impact allowance” an empirical market-impact estimate? A mismatch can change empirical interpretation or make a paper claim stronger than the underlying data support; do not presume a defect before examining the archived outputs.
- **Inspect first:** `costs.py, config/portfolio.yaml, README and paper`. Resolve these to actual paths on the checked-out commit; record function names/line ranges rather than assuming they are unchanged.
- **Detailed verification and candidate correction:** Identify fixed impact allowance as a flat modeled bps assumption folded into slippage, not estimated square-root market impact. Check no text claims nonlinear observed execution.
- **Initial audit requested:** Clarify that it is only a cost assumption.
- **Deliverable:** `outputs/audit/impact_assumption_audit.md` (or an equivalent, documented path); record source input hashes, exact calculations and explanatory caveats. **Never overwrite old frozen result artifacts.**
- **Acceptance gate:** Cost wording matches implementation and capacity is not claimed.
- **Progress record:** owner `Codex`; result `UNASSESSED`; baseline SHA `TBD`; updated SHA `TBD`; test `TBD`; evidence link `TBD`; numerical change `TBD`; research-paper impact `TBD`; independent reviewer `PENDING`.


- **Phase3 complete validation (1 November2026):** previous `UNASSESSED`; current `RESEARCH_LIMITATION_DISCLOSED`. Exact source `backtest/costs.py::estimate;config/portfolio.yaml` under `src/institutional_factor_platform` unless explicitly scripts/config. BASE half-spread5bps plus modeled5bps slippage(2slippage+3fixed allowance),commission0,nonlinear impact0. Limit/manuscript consequence: Flat allowance is not measured order-book impact or capacity calibration. Evidence `../../outputs/audit/phase3/PHASE3_COMPLETE_VALIDATION.md`, issue/reconciliation files and full source manifest. Portfolio/MLfit source `0fe382f`; MLmetric-only source `9df5455`; final evidence is the containing commit.6new regressions,91targeted and372full pass/90.62%; originals preserved; all before/after values and hashes recorded. Reviewer `PENDING`.

#### [x] P11 — Are VaR and CVaR reported for monthly returns with the correct horizon labels?

- **Phase / severity from initial audit:** 3 / Medium; **status:** `CONFIRMED_ERROR_FIXED`.
- **Why this matters / failure mode:** Are VaR and CVaR reported for monthly returns with the correct horizon labels? A mismatch can change empirical interpretation or make a paper claim stronger than the underlying data support; do not presume a defect before examining the archived outputs.
- **Inspect first:** `risk/metrics.py and portfolio returns`. Resolve these to actual paths on the checked-out commit; record function names/line ranges rather than assuming they are unchanged.
- **Detailed verification and candidate correction:** Independently recompute monthly VaR95/ES95 on net monthly portfolio returns, check 5% tail sample size, unit signs and distinction from daily risk horizons.
- **Initial audit requested:** Verify return frequency and quantile definitions.
- **Deliverable:** `outputs/audit/var_es_horizon_audit.csv` (or an equivalent, documented path); record source input hashes, exact calculations and explanatory caveats. **Never overwrite old frozen result artifacts.**
- **Acceptance gate:** Risk labels specify frequency and the positive-loss convention.
- **Progress record:** owner `Codex`; result `UNASSESSED`; baseline SHA `TBD`; updated SHA `TBD`; test `TBD`; evidence link `TBD`; numerical change `TBD`; research-paper impact `TBD`; independent reviewer `PENDING`.


- **Phase3 complete validation (1 November2026):** previous `UNASSESSED`; current `CONFIRMED_ERROR_FIXED`. Exact source `portfolio/service.py::_risk_free_series;risk/metrics.py::risk_summary,value_at_risk,expected_shortfall` under `src/institutional_factor_platform` unless explicitly scripts/config. Confirmed daily-cash/monthly-return mismatch fixed by exact interval compounding. Independent Sharpe,volatility,NAV,VaR95/ES95 reconcile. Limit/manuscript consequence: Unannualized monthly-cycle positive-loss quantiles; two realized tail observations. Inclusive tail mean differs from fractional training-LP tail. Evidence `../../outputs/audit/phase3/PHASE3_COMPLETE_VALIDATION.md`, issue/reconciliation files and full source manifest. Portfolio/MLfit source `0fe382f`; MLmetric-only source `9df5455`; final evidence is the containing commit.6new regressions,91targeted and372full pass/90.62%; originals preserved; all before/after values and hashes recorded. Reviewer `PENDING`.

#### [x] P12 — Does the paper include sufficient uncertainty around portfolio performance rankings?

- **Phase / severity from initial audit:** 3 / High; **status:** `RESEARCH_LIMITATION_DISCLOSED`.
- **Why this matters / failure mode:** Does the paper include sufficient uncertainty around portfolio performance rankings? A mismatch can change empirical interpretation or make a paper claim stronger than the underlying data support; do not presume a defect before examining the archived outputs.
- **Inspect first:** `portfolio monthly return parquet`. Resolve these to actual paths on the checked-out commit; record function names/line ranges rather than assuming they are unchanged.
- **Detailed verification and candidate correction:** Compute same-date paired performance differences and confidence bounds on 8 strategy returns where feasible; account for small 32-month sample and multiplicity. Keep otherwise descriptive ranks.
- **Initial audit requested:** Use appropriate paired tests or state that rankings are descriptive.
- **Deliverable:** `outputs/audit/portfolio_rank_uncertainty.csv` (or an equivalent, documented path); record source input hashes, exact calculations and explanatory caveats. **Never overwrite old frozen result artifacts.**
- **Acceptance gate:** No strategy proclaimed superior solely on point estimates.
- **Progress record:** owner `Codex`; result `UNASSESSED`; baseline SHA `TBD`; updated SHA `TBD`; test `TBD`; evidence link `TBD`; numerical change `TBD`; research-paper impact `TBD`; independent reviewer `PENDING`.


- **Phase3 complete validation (1 November2026):** previous `UNASSESSED`; current `RESEARCH_LIMITATION_DISCLOSED`. Exact source `scripts/research_phase3_verify.py::portfolio_audit` under `src/institutional_factor_platform` unless explicitly scripts/config. One predeclared paired CVaR-EW mean:original.00689120060,LOO.00508077666-.00980775974; corrected.00598371896,LOO.00408710902-.00875998275. Limit/manuscript consequence: LOO ranges are descriptive, not confidence intervals,superiority tests or persistence proof. Evidence `../../outputs/audit/phase3/PHASE3_COMPLETE_VALIDATION.md`, issue/reconciliation files and full source manifest. Portfolio/MLfit source `0fe382f`; MLmetric-only source `9df5455`; final evidence is the containing commit.6new regressions,91targeted and372full pass/90.62%; originals preserved; all before/after values and hashes recorded. Reviewer `PENDING`.

#### [x] ML1 — Are there truly 91 usable monthly dates but only 17 complete final folds?

- **Phase / severity from initial audit:** 3 / High; **status:** `CONFIRMED_ERROR_FIXED`.
- **Why this matters / failure mode:** Are there truly 91 usable monthly dates but only 17 complete final folds? A mismatch can change empirical interpretation or make a paper claim stronger than the underlying data support; do not presume a defect before examining the archived outputs.
- **Inspect first:** `ml/splits.py; ML manifest; feature target dates`. Resolve these to actual paths on the checked-out commit; record function names/line ranges rather than assuming they are unchanged.
- **Detailed verification and candidate correction:** Rebuild all monthly decision and 60/12/1 fold boundaries with 1-month embargo; count 91 months, excluded months, 17 complete tests and any gaps.
- **Initial audit requested:** Reconstruct the exact fold schedule.
- **Deliverable:** `outputs/audit/ml_fold_calendar.csv` (or an equivalent, documented path); record source input hashes, exact calculations and explanatory caveats. **Never overwrite old frozen result artifacts.**
- **Acceptance gate:** Every claimed fold is derived from actual dated observations.
- **Progress record:** owner `Codex`; result `UNASSESSED`; baseline SHA `TBD`; updated SHA `TBD`; test `TBD`; evidence link `TBD`; numerical change `TBD`; research-paper impact `TBD`; independent reviewer `PENDING`.


- **Phase3 complete validation (1 November2026):** previous `UNASSESSED`; current `CONFIRMED_ERROR_FIXED`. Exact source `ml/features.py::monthly_decision_features;ml/splits.py::temporal_folds` under `src/institutional_factor_platform` unless explicitly scripts/config. 91original distinct dates=89months+2earlier security dates. Corrected27632rows/89common dates/15complete folds rather than27640/91/17. Limit/manuscript consequence: Preserve old publications. Original initial60date labels represented58months; corrected training60expands to74months. Evidence `../../outputs/audit/phase3/PHASE3_COMPLETE_VALIDATION.md`, issue/reconciliation files and full source manifest. Portfolio/MLfit source `0fe382f`; MLmetric-only source `9df5455`; final evidence is the containing commit.6new regressions,91targeted and372full pass/90.62%; originals preserved; all before/after values and hashes recorded. Reviewer `PENDING`.

#### [x] ML2 — Does label purging eliminate every 21-session overlap at train/validation/test boundaries?

- **Phase / severity from initial audit:** 3 / High; **status:** `CONFIRMED_ERROR_FIXED`.
- **Why this matters / failure mode:** Does label purging eliminate every 21-session overlap at train/validation/test boundaries? A mismatch can change empirical interpretation or make a paper claim stronger than the underlying data support; do not presume a defect before examining the archived outputs.
- **Inspect first:** `ml/splits.py; ml/targets.py`. Resolve these to actual paths on the checked-out commit; record function names/line ranges rather than assuming they are unchanged.
- **Detailed verification and candidate correction:** For each fold intersect target [start,end] intervals with validation/test dates; assert training targets cannot overlap later partitions and validate boundary inclusivity on month ends.
- **Initial audit requested:** Test interval intersections.
- **Deliverable:** `outputs/audit/ml_purge_interval_tests.md` (or an equivalent, documented path); record source input hashes, exact calculations and explanatory caveats. **Never overwrite old frozen result artifacts.**
- **Acceptance gate:** No label leakage at partition boundaries.
- **Progress record:** owner `Codex`; result `UNASSESSED`; baseline SHA `TBD`; updated SHA `TBD`; test `TBD`; evidence link `TBD`; numerical change `TBD`; research-paper impact `TBD`; independent reviewer `PENDING`.


- **Phase3 complete validation (1 November2026):** previous `UNASSESSED`; current `CONFIRMED_ERROR_FIXED`. Exact source `ml/targets.py::build_targets;ml/splits.py::assign_and_purge` under `src/institutional_factor_platform` unless explicitly scripts/config. 8original ends violate common21-session horizon. Remove2off-month-end features and exclude6incomplete labels; every retained corrected window is21complete sessions. Partition interval checks pass. Limit/manuscript consequence: No missing observation was recovered,filled,extended or made cash. Evidence `../../outputs/audit/phase3/PHASE3_COMPLETE_VALIDATION.md`, issue/reconciliation files and full source manifest. Portfolio/MLfit source `0fe382f`; MLmetric-only source `9df5455`; final evidence is the containing commit.6new regressions,91targeted and372full pass/90.62%; originals preserved; all before/after values and hashes recorded. Reviewer `PENDING`.

#### [x] ML3 — Is the one-month embargo consistently applied without unnecessary use of later information?

- **Phase / severity from initial audit:** 3 / High; **status:** `VERIFIED_CORRECT`.
- **Why this matters / failure mode:** Is the one-month embargo consistently applied without unnecessary use of later information? A mismatch can change empirical interpretation or make a paper claim stronger than the underlying data support; do not presume a defect before examining the archived outputs.
- **Inspect first:** `ML split config; preprocessing/model selection`. Resolve these to actual paths on the checked-out commit; record function names/line ranges rather than assuming they are unchanged.
- **Detailed verification and candidate correction:** Compute effective embargo durations relative to the 21-session target horizon; test first/last eligible training observations and ensure no future validation metric enters training.
- **Initial audit requested:** Check boundary dates and feature timestamps.
- **Deliverable:** `outputs/audit/ml_embargo_audit.csv` (or an equivalent, documented path); record source input hashes, exact calculations and explanatory caveats. **Never overwrite old frozen result artifacts.**
- **Acceptance gate:** Embargo and purging constraints protect each test decision.
- **Progress record:** owner `Codex`; result `UNASSESSED`; baseline SHA `TBD`; updated SHA `TBD`; test `TBD`; evidence link `TBD`; numerical change `TBD`; research-paper impact `TBD`; independent reviewer `PENDING`.


- **Phase3 complete validation (1 November2026):** previous `UNASSESSED`; current `VERIFIED_CORRECT`. Exact source `ml/splits.py::temporal_folds,assign_and_purge` under `src/institutional_factor_platform` unless explicitly scripts/config. All17original/15corrected folds preserve1-month embargo at both boundaries; train/validation label ends precede later formation. Limit/manuscript consequence: Adjacent OOS targets overlap6/16original and5/14corrected pairs; folds are not independent. Evidence `../../outputs/audit/phase3/PHASE3_COMPLETE_VALIDATION.md`, issue/reconciliation files and full source manifest. Portfolio/MLfit source `0fe382f`; MLmetric-only source `9df5455`; final evidence is the containing commit.6new regressions,91targeted and372full pass/90.62%; originals preserved; all before/after values and hashes recorded. Reviewer `PENDING`.

#### [ ] ML4 — Are all cross-sectional input features available before the monthly investment decision?

- **Phase / severity from initial audit:** 3 / High; **status:** `SOURCE_EVIDENCE_BLOCKED`.
- **Why this matters / failure mode:** Are all cross-sectional input features available before the monthly investment decision? A mismatch can change empirical interpretation or make a paper claim stronger than the underlying data support; do not presume a defect before examining the archived outputs.
- **Inspect first:** `features provenance; ml feature table; factors/temporal.py`. Resolve these to actual paths on the checked-out commit; record function names/line ranges rather than assuming they are unchanged.
- **Detailed verification and candidate correction:** Trace book-to-market SEC availability and 12–1 momentum formation dates to prediction timestamps; inspect securities with amendments, holidays, after-close filings, missing-price histories.
- **Initial audit requested:** Independently sample point-in-time feature rows.
- **Deliverable:** `outputs/audit/ml_feature_pit_samples.csv` (or an equivalent, documented path); record source input hashes, exact calculations and explanatory caveats. **Never overwrite old frozen result artifacts.**
- **Acceptance gate:** No feature timestamp after the decision is used.
- **Progress record:** owner `Codex`; result `UNASSESSED`; baseline SHA `TBD`; updated SHA `TBD`; test `TBD`; evidence link `TBD`; numerical change `TBD`; research-paper impact `TBD`; independent reviewer `PENDING`.


- **Phase3 complete validation (1 November2026):** previous `UNASSESSED`; current `SOURCE_EVIDENCE_BLOCKED`. Exact source `ml/features.py::assemble_factor_features;ml/preprocessing.py::SafePreprocessor` under `src/institutional_factor_platform` unless explicitly scripts/config. Only frozen book-to-market and12-1momentum reused. UTC-day gate passes; final scalers match permitted training data; independent linear/Ridge/baseline forecasts and coefficients match all folds. Limit/manuscript consequence: Complete actual filing/share capture/pre-trade timing remains D4/V1-qualified. Earlier fitted tree objects are not retained independently. Evidence `../../outputs/audit/phase3/PHASE3_COMPLETE_VALIDATION.md`, issue/reconciliation files and full source manifest. Portfolio/MLfit source `0fe382f`; MLmetric-only source `9df5455`; final evidence is the containing commit.6new regressions,91targeted and372full pass/90.62%; originals preserved; all before/after values and hashes recorded. Reviewer `PENDING`.

#### [ ] ML5 — Is the reported economic strategy constructed only from predictions actually generated before the corresponding holding period?

- **Phase / severity from initial audit:** 3 / High; **status:** `SOURCE_EVIDENCE_BLOCKED`.
- **Why this matters / failure mode:** Is the reported economic strategy constructed only from predictions actually generated before the corresponding holding period? A mismatch can change empirical interpretation or make a paper claim stronger than the underlying data support; do not presume a defect before examining the archived outputs.
- **Inspect first:** `ml/economic.py; predictions; folds; costs`. Resolve these to actual paths on the checked-out commit; record function names/line ranges rather than assuming they are unchanged.
- **Detailed verification and candidate correction:** For representative folds verify prediction file is authenticated, generated at or before decision, joined only to future realized returns, and ranking allocator does not use future outcomes. Reconcile selected assets with economic portfolio trades.
- **Initial audit requested:** Reconcile decisions, forecasts and realized returns.
- **Deliverable:** `outputs/audit/ml_prediction_to_pnl_trace.csv` (or an equivalent, documented path); record source input hashes, exact calculations and explanatory caveats. **Never overwrite old frozen result artifacts.**
- **Acceptance gate:** Forecast-to-trade-to-PnL chain is reproducible without future information.
- **Progress record:** owner `Codex`; result `UNASSESSED`; baseline SHA `TBD`; updated SHA `TBD`; test `TBD`; evidence link `TBD`; numerical change `TBD`; research-paper impact `TBD`; independent reviewer `PENDING`.


- **Phase3 complete validation (1 November2026):** previous `UNASSESSED`; current `SOURCE_EVIDENCE_BLOCKED`. Exact source `ml/service.py::_economic_evaluation;ml/economic.py::evaluate_ranked_signal` under `src/institutional_factor_platform` unless explicitly scripts/config. Held-out predictions map to next common session without realized return entering ranking. Limit/manuscript consequence: Retrospective output is not historical live-forecast evidence. Same-close acquisition versus UTC-day cutoff/intraday availability remains unresolved; target21sessions versus economic1session. Evidence `../../outputs/audit/phase3/PHASE3_COMPLETE_VALIDATION.md`, issue/reconciliation files and full source manifest. Portfolio/MLfit source `0fe382f`; MLmetric-only source `9df5455`; final evidence is the containing commit.6new regressions,91targeted and372full pass/90.62%; originals preserved; all before/after values and hashes recorded. Reviewer `PENDING`.

#### [x] ML6 — Why do linear and factor-composite ICs match to six decimals?

- **Phase / severity from initial audit:** 3 / Medium; **status:** `RESEARCH_LIMITATION_DISCLOSED`.
- **Why this matters / failure mode:** Why do linear and factor-composite ICs match to six decimals? A mismatch can change empirical interpretation or make a paper claim stronger than the underlying data support; do not presume a defect before examining the archived outputs.
- **Inspect first:** `ML predictions, model fits and benchmark outputs`. Resolve these to actual paths on the checked-out commit; record function names/line ranges rather than assuming they are unchanged.
- **Detailed verification and candidate correction:** Compare factor composite and linear predictions vector-by-vector, coefficients, training design matrix and rank transformation; explain exact six-decimal IC identity and check duplicate output artifacts.
- **Initial audit requested:** Verify whether they are identical or nearly equivalent forecasts.
- **Deliverable:** `outputs/audit/ml_linear_composite_equivalence.csv` (or an equivalent, documented path); record source input hashes, exact calculations and explanatory caveats. **Never overwrite old frozen result artifacts.**
- **Acceptance gate:** Identical results are explained by identical rankings or traced to a real duplication defect.
- **Progress record:** owner `Codex`; result `UNASSESSED`; baseline SHA `TBD`; updated SHA `TBD`; test `TBD`; evidence link `TBD`; numerical change `TBD`; research-paper impact `TBD`; independent reviewer `PENDING`.


- **Phase3 complete validation (1 November2026):** previous `UNASSESSED`; current `RESEARCH_LIMITATION_DISCLOSED`. Exact source `ml/models.py::create_model` under `src/institutional_factor_platform` unless explicitly scripts/config. factor_composite and linear both use LinearRegression; vectors/ranks exactly identical in all32original+corrected folds. Limit/manuscript consequence: Intentional estimator alias;8names are not8independent methods. No artificial differences introduced. Evidence `../../outputs/audit/phase3/PHASE3_COMPLETE_VALIDATION.md`, issue/reconciliation files and full source manifest. Portfolio/MLfit source `0fe382f`; MLmetric-only source `9df5455`; final evidence is the containing commit.6new regressions,91targeted and372full pass/90.62%; originals preserved; all before/after values and hashes recorded. Reviewer `PENDING`.

#### [x] ML7 — Why is Ridge almost identical to linear?

- **Phase / severity from initial audit:** 3 / Medium; **status:** `VERIFIED_CORRECT`.
- **Why this matters / failure mode:** Why is Ridge almost identical to linear? A mismatch can change empirical interpretation or make a paper claim stronger than the underlying data support; do not presume a defect before examining the archived outputs.
- **Inspect first:** `ML model settings and fit records`. Resolve these to actual paths on the checked-out commit; record function names/line ranges rather than assuming they are unchanged.
- **Detailed verification and candidate correction:** Measure Ridge vs linear coefficient/forecast/rank differences under scaling, feature collinearity and chosen alpha. Test that regularization was implemented and applied to training folds only.
- **Initial audit requested:** Inspect standardized feature distributions and regularization strength.
- **Deliverable:** `outputs/audit/ml_ridge_linear_check.csv` (or an equivalent, documented path); record source input hashes, exact calculations and explanatory caveats. **Never overwrite old frozen result artifacts.**
- **Acceptance gate:** Near-matching results are explained and correctly labeled.
- **Progress record:** owner `Codex`; result `UNASSESSED`; baseline SHA `TBD`; updated SHA `TBD`; test `TBD`; evidence link `TBD`; numerical change `TBD`; research-paper impact `TBD`; independent reviewer `PENDING`.


- **Phase3 complete validation (1 November2026):** previous `UNASSESSED`; current `VERIFIED_CORRECT`. Exact source `ml/models.py::create_model;hyperparameter_trials` under `src/institutional_factor_platform` unless explicitly scripts/config. Ridge grid.1/1/10 and training-only scaling preserved; finalalpha.1. Penalized normal equations reproduce fold forecasts/coefficients; max linear-Ridge gap7.66e-6. Limit/manuscript consequence: Weak penalty relative to training Gram matrix explains similarity; some rankings differ. No retuning. Evidence `../../outputs/audit/phase3/PHASE3_COMPLETE_VALIDATION.md`, issue/reconciliation files and full source manifest. Portfolio/MLfit source `0fe382f`; MLmetric-only source `9df5455`; final evidence is the containing commit.6new regressions,91targeted and372full pass/90.62%; originals preserved; all before/after values and hashes recorded. Reviewer `PENDING`.

#### [x] ML8 — Are the 17 fold-level ICs independent enough for ordinary bootstrap resampling?

- **Phase / severity from initial audit:** 3 / High; **status:** `CONFIRMED_ERROR_FIXED`.
- **Why this matters / failure mode:** Are the 17 fold-level ICs independent enough for ordinary bootstrap resampling? A mismatch can change empirical interpretation or make a paper claim stronger than the underlying data support; do not presume a defect before examining the archived outputs.
- **Inspect first:** `fold metrics and resampling code`. Resolve these to actual paths on the checked-out commit; record function names/line ranges rather than assuming they are unchanged.
- **Detailed verification and candidate correction:** Examine serial dependence of 17 fold ICs; compare basic bootstrap with conservative block-based or leave-period-out sensitivity when sample size permits, without promising strong significance.
- **Initial audit requested:** Evaluate temporal dependence and alternative uncertainty reporting.
- **Deliverable:** `outputs/audit/ml_ic_uncertainty_sensitivity.csv` (or an equivalent, documented path); record source input hashes, exact calculations and explanatory caveats. **Never overwrite old frozen result artifacts.**
- **Acceptance gate:** IC intervals and limits are accurately communicated.
- **Progress record:** owner `Codex`; result `UNASSESSED`; baseline SHA `TBD`; updated SHA `TBD`; test `TBD`; evidence link `TBD`; numerical change `TBD`; research-paper impact `TBD`; independent reviewer `PENDING`.


- **Phase3 complete validation (1 November2026):** previous `UNASSESSED`; current `CONFIRMED_ERROR_FIXED`. Exact source `ml/evaluation.py::block_bootstrap_ic,_correlation` under `src/institutional_factor_platform` unless explicitly scripts/config. Bootstrap now targets observed mean date IC instead of pooled ranks/bootstrap mean. Constant nonzero forecasts now yield unavailable IC rather thanNaN. Same block3/100resamples/seed17. Limit/manuscript consequence: 15dependent folds and overlapping outcomes limit interval coverage; nominal positive/negative intervals are not robust discoveries. Evidence `../../outputs/audit/phase3/PHASE3_COMPLETE_VALIDATION.md`, issue/reconciliation files and full source manifest. Portfolio/MLfit source `0fe382f`; MLmetric-only source `9df5455`; final evidence is the containing commit.6new regressions,91targeted and372full pass/90.62%; originals preserved; all before/after values and hashes recorded. Reviewer `PENDING`.

#### [x] ML9 — Are economic gains compared on a consistent capital-allocation and transaction-cost basis?

- **Phase / severity from initial audit:** 3 / High; **status:** `RESEARCH_LIMITATION_DISCLOSED`.
- **Why this matters / failure mode:** Are economic gains compared on a consistent capital-allocation and transaction-cost basis? A mismatch can change empirical interpretation or make a paper claim stronger than the underlying data support; do not presume a defect before examining the archived outputs.
- **Inspect first:** `ml/economic.py; backtest engine; economic folds`. Resolve these to actual paths on the checked-out commit; record function names/line ranges rather than assuming they are unchanged.
- **Detailed verification and candidate correction:** Reconcile one-period selected holdings, gross/net return, transaction costs, ranking selection fraction, benchmark exposure, zero/historical-mean baselines and cumulative effect across folds.
- **Initial audit requested:** Verify actual portfolio turnover and benchmark returns.
- **Deliverable:** `outputs/audit/ml_after_cost_reconciliation.csv` (or an equivalent, documented path); record source input hashes, exact calculations and explanatory caveats. **Never overwrite old frozen result artifacts.**
- **Acceptance gate:** The reported economic signals correspond to actual out-of-sample decisions and fees.
- **Progress record:** owner `Codex`; result `UNASSESSED`; baseline SHA `TBD`; updated SHA `TBD`; test `TBD`; evidence link `TBD`; numerical change `TBD`; research-paper impact `TBD`; independent reviewer `PENDING`.


- **Phase3 complete validation (1 November2026):** previous `UNASSESSED`; current `RESEARCH_LIMITATION_DISCLOSED`. Exact source `ml/economic.py::evaluate_ranked_signal;ml/service.py::_economic_evaluation` under `src/institutional_factor_platform` unless explicitly scripts/config. Every family uses20%equal-weight selected equities,cash reset,one next session and10bps initialL1fee; all economic identities reconcile. Limit/manuscript consequence: Not a continuous21-session strategy; no exit liquidation charge or capital chain. Constant ties select arbitrary IDs. Stable incremental after-cost value remains unestablished. Evidence `../../outputs/audit/phase3/PHASE3_COMPLETE_VALIDATION.md`, issue/reconciliation files and full source manifest. Portfolio/MLfit source `0fe382f`; MLmetric-only source `9df5455`; final evidence is the containing commit.6new regressions,91targeted and372full pass/90.62%; originals preserved; all before/after values and hashes recorded. Reviewer `PENDING`.

#### [x] ML10 — Can the SHAP versus permutation-importance disagreement be explained by feature correlation and sample size?

- **Phase / severity from initial audit:** 3 / Medium; **status:** `RESEARCH_LIMITATION_DISCLOSED`.
- **Why this matters / failure mode:** Can the SHAP versus permutation-importance disagreement be explained by feature correlation and sample size? A mismatch can change empirical interpretation or make a paper claim stronger than the underlying data support; do not presume a defect before examining the archived outputs.
- **Inspect first:** `ml explainability outputs and configurations`. Resolve these to actual paths on the checked-out commit; record function names/line ranges rather than assuming they are unchanged.
- **Detailed verification and candidate correction:** Trace SHAP/permutation/coefficient definitions; compare feature correlations, fold sample sizes and model stability; distinguish model diagnostics from causal factor importance.
- **Initial audit requested:** Inspect attribution definitions and stability.
- **Deliverable:** `outputs/audit/ml_explainability_comparison.md` (or an equivalent, documented path); record source input hashes, exact calculations and explanatory caveats. **Never overwrite old frozen result artifacts.**
- **Acceptance gate:** Different rankings are explained or labeled inconclusive, not causal.
- **Progress record:** owner `Codex`; result `UNASSESSED`; baseline SHA `TBD`; updated SHA `TBD`; test `TBD`; evidence link `TBD`; numerical change `TBD`; research-paper impact `TBD`; independent reviewer `PENDING`.


### Phase 4 — Manuscript/results reconciliation and publication integrity


- **Phase3 complete validation (1 November2026):** previous `UNASSESSED`; current `RESEARCH_LIMITATION_DISCLOSED`. Exact source `ml/validation.py::tree_explanations` under `src/institutional_factor_platform` unless explicitly scripts/config. Permutation uses validation prediction loss; SHAP explains test predictions with historical background. Top disagreement RF7/17→7/15;XGB10/17→6/15; feature correlation≈-.1875. Limit/manuscript consequence: Different estimands/samples and instability can disagree; causal explanation/importance is not established. Evidence `../../outputs/audit/phase3/PHASE3_COMPLETE_VALIDATION.md`, issue/reconciliation files and full source manifest. Portfolio/MLfit source `0fe382f`; MLmetric-only source `9df5455`; final evidence is the containing commit.6new regressions,91targeted and372full pass/90.62%; originals preserved; all before/after values and hashes recorded. Reviewer `PENDING`.

#### [x] R1 — Does the tagged research commit reproduce every manuscript table?

- **Phase / severity from initial audit:** 4 / High; **status:** `RESEARCH_LIMITATION_DISCLOSED`.
- **Why this matters / failure mode:** Does the tagged research commit reproduce every manuscript table? A mismatch can change empirical interpretation or make a paper claim stronger than the underlying data support; do not presume a defect before examining the archived outputs.
- **Inspect first:** `research paper PDF; docs/RESULTS.md; published manifests`. Resolve these to actual paths on the checked-out commit; record function names/line ranges rather than assuming they are unchanged.
- **Detailed verification and candidate correction:** Map each manuscript number, table and figure to frozen publication ID, source file, sha256, transform and display precision. Check contradictions including 487/715447/37273, R², 83.17%, MDD and ML folds.
- **Initial audit requested:** Generate a source-to-table evidence matrix.
- **Deliverable:** `outputs/audit/paper_to_source_traceability.csv` (or an equivalent, documented path); record source input hashes, exact calculations and explanatory caveats. **Never overwrite old frozen result artifacts.**
- **Acceptance gate:** Every material manuscript claim is reproducible or explicitly marked pending.
- **Progress record:** owner `Codex`; result `UNASSESSED`; baseline SHA `TBD`; updated SHA `TBD`; test `TBD`; evidence link `TBD`; numerical change `TBD`; research-paper impact `TBD`; independent reviewer `PENDING`.


- **Phase4 manuscript reconciliation (1 November2026):** previous `UNASSESSED`; current `RESEARCH_LIMITATION_DISCLOSED`. All359 digit-containing original PDF passages inventoried;249 legacy field records inspected;222 revised table rows,81 numerical narrative paragraphs and26equations mapped. Unsupported scenario/legacy-only risk cells omitted explicitly. Original hypotheses preserved; author statements pending. Evidence: `../../outputs/audit/phase4/PHASE4_MANUSCRIPT_VALIDATION.md`, `PHASE4_CLAIM_TRACEABILITY.csv; manuscript Tables I-XV and Appendices A-L` and source/checksum manifest. Source baseline `f22f5cbe365e98c8d5fef6b5308ff765703df173`; new manuscript `IMFP-P4-2026-11-01`; exact review checkpoint is the containing Phase4 commit. Tests:27rendered pages/26tables/6figures/26equations;843cells and all corrected table/interval values pass;27reference identities; author preservation PASS. Remaining limitation and paper consequence: Every material claim is reproducible within stated evidence or explicitly qualified/pending; missing H1/H3 approval is not repaired. Independent human review `PENDING`.

#### [x] R2 — Are frozen raw inputs and complete manifests available to an independent authorized researcher?

- **Phase / severity from initial audit:** 4 / High; **status:** `RESEARCH_LIMITATION_DISCLOSED`.
- **Why this matters / failure mode:** Are frozen raw inputs and complete manifests available to an independent authorized researcher? A mismatch can change empirical interpretation or make a paper claim stronger than the underlying data support; do not presume a defect before examining the archived outputs.
- **Inspect first:** `source catalogs; manifests; docs/REPRODUCIBILITY.md`. Resolve these to actual paths on the checked-out commit; record function names/line ranges rather than assuming they are unchanged.
- **Detailed verification and candidate correction:** List raw/provider files, hash, retrieved date, license and lawful availability; test original-input provenance without redistributing restricted bytes.
- **Initial audit requested:** Check archival inventory and data access.
- **Deliverable:** `outputs/audit/frozen_inputs_and_rights.csv` (or an equivalent, documented path); record source input hashes, exact calculations and explanatory caveats. **Never overwrite old frozen result artifacts.**
- **Acceptance gate:** A third party can distinguish reproducible code from unavailable raw data.
- **Progress record:** owner `Codex`; result `UNASSESSED`; baseline SHA `TBD`; updated SHA `TBD`; test `TBD`; evidence link `TBD`; numerical change `TBD`; research-paper impact `TBD`; independent reviewer `PENDING`.


- **Phase4 manuscript reconciliation (1 November2026):** previous `UNASSESSED`; current `RESEARCH_LIMITATION_DISCLOSED`. Public code/configuration/audit evidence separated from private frozen Parquet and model bundles. Lawful original-input access is required; current vendor downloads do not reproduce source vintage. Evidence: `../../outputs/audit/phase4/PHASE4_MANUSCRIPT_VALIDATION.md`, `Manuscript Data and code availability; PHASE4_PUBLICATION_SOURCE_MANIFEST.json` and source/checksum manifest. Source baseline `f22f5cbe365e98c8d5fef6b5308ff765703df173`; new manuscript `IMFP-P4-2026-11-01`; exact review checkpoint is the containing Phase4 commit. Tests:27rendered pages/26tables/6figures/26equations;843cells and all corrected table/interval values pass;27reference identities; author preservation PASS. Remaining limitation and paper consequence: Original vendor retrieval/adjustment and redistribution permissions remain bounded; no private raw data published. Independent human review `PENDING`.

#### [x] R3 — Does 301 passing tests prove empirical correctness?

- **Phase / severity from initial audit:** 4 / Medium; **status:** `VERIFIED_CORRECT`.
- **Why this matters / failure mode:** Does 301 passing tests prove empirical correctness? A mismatch can change empirical interpretation or make a paper claim stronger than the underlying data support; do not presume a defect before examining the archived outputs.
- **Inspect first:** `pytest/CI reports; run manifests`. Resolve these to actual paths on the checked-out commit; record function names/line ranges rather than assuming they are unchanged.
- **Detailed verification and candidate correction:** Separate synthetic correctness tests, CI, integrity hashes, archived data reconstruction and full empirical rerun. Test selected arithmetic identities independently.
- **Initial audit requested:** Distinguish software tests from financial-result reproduction.
- **Deliverable:** `outputs/audit/validation_coverage_matrix.md` (or an equivalent, documented path); record source input hashes, exact calculations and explanatory caveats. **Never overwrite old frozen result artifacts.**
- **Acceptance gate:** 301 tests never described as proof of independent empirical correctness.
- **Progress record:** owner `Codex`; result `UNASSESSED`; baseline SHA `TBD`; updated SHA `TBD`; test `TBD`; evidence link `TBD`; numerical change `TBD`; research-paper impact `TBD`; independent reviewer `PENDING`.


- **Phase4 manuscript reconciliation (1 November2026):** previous `UNASSESSED`; current `VERIFIED_CORRECT`. 372tests/90.62%coverage are attributed to accepted Phase3,not new Phase4 execution or proof of causality/PIT/investability. Document checks independently verify843table cells and corrected values. Evidence: `../../outputs/audit/phase4/PHASE4_MANUSCRIPT_VALIDATION.md`, `Manuscript Section X/Appendix J; PHASE4_TEST_AND_FORMAT_QA.txt` and source/checksum manifest. Source baseline `f22f5cbe365e98c8d5fef6b5308ff765703df173`; new manuscript `IMFP-P4-2026-11-01`; exact review checkpoint is the containing Phase4 commit. Tests:27rendered pages/26tables/6figures/26equations;843cells and all corrected table/interval values pass;27reference identities; author preservation PASS. Remaining limitation and paper consequence: Software assurance is distinct from empirical provenance and economic generalizability. Independent human review `PENDING`.

#### [x] R4 — Are the factor, portfolio and ML result IDs tied to exact parent data hashes?

- **Phase / severity from initial audit:** 4 / Medium; **status:** `VERIFIED_CORRECT`.
- **Why this matters / failure mode:** Are the factor, portfolio and ML result IDs tied to exact parent data hashes? A mismatch can change empirical interpretation or make a paper claim stronger than the underlying data support; do not presume a defect before examining the archived outputs.
- **Inspect first:** `publication manifests, source lineage`. Resolve these to actual paths on the checked-out commit; record function names/line ranges rather than assuming they are unchanged.
- **Detailed verification and candidate correction:** Trace source market/fundamental hashes through factor, asset-pricing, portfolio and ML publications; check each parent-child ID and stale cache rejection.
- **Initial audit requested:** Authenticate complete lineage.
- **Deliverable:** `outputs/audit/publication_lineage_graph.csv` (or an equivalent, documented path); record source input hashes, exact calculations and explanatory caveats. **Never overwrite old frozen result artifacts.**
- **Acceptance gate:** Every output has a valid immutable parent chain or an explicit blocker.
- **Progress record:** owner `Codex`; result `UNASSESSED`; baseline SHA `TBD`; updated SHA `TBD`; test `TBD`; evidence link `TBD`; numerical change `TBD`; research-paper impact `TBD`; independent reviewer `PENDING`.


- **Phase4 manuscript reconciliation (1 November2026):** previous `UNASSESSED`; current `VERIFIED_CORRECT`. 32final accepted corrected portfolio/ML authority pairs and264smallJSON artifacts authenticate against stored hashes. Corrected factor/pricing parents retained; ML actual historical raw-score/cost dependencies distinguished from quantile returns. Evidence: `../../outputs/audit/phase4/PHASE4_MANUSCRIPT_VALIDATION.md`, `Manuscript Appendix H; PHASE4_PUBLICATION_SOURCE_MANIFEST.json` and source/checksum manifest. Source baseline `f22f5cbe365e98c8d5fef6b5308ff765703df173`; new manuscript `IMFP-P4-2026-11-01`; exact review checkpoint is the containing Phase4 commit. Tests:27rendered pages/26tables/6figures/26equations;843cells and all corrected table/interval values pass;27reference identities; author preservation PASS. Remaining limitation and paper consequence: No result IDs regenerated; final ML IDs exclude superseded intermediates. Large source hashes reused through540stat guards. Independent human review `PENDING`.

#### [ ] R5 — Are the README and paper using the same nomenclature, windows, and units?

- **Phase / severity from initial audit:** 4 / Medium; **status:** `RESEARCH_LIMITATION_DISCLOSED`.
- **Why this matters / failure mode:** Are the README and paper using the same nomenclature, windows, and units? A mismatch can change empirical interpretation or make a paper claim stronger than the underlying data support; do not presume a defect before examining the archived outputs.
- **Inspect first:** `README.md; docs; PDF; config`. Resolve these to actual paths on the checked-out commit; record function names/line ranges rather than assuming they are unchanged.
- **Detailed verification and candidate correction:** Search README, methods, results, paper and configs for mismatch in annualized vs cumulative, gross vs net, cost bps, sample dates, q label, significant alpha and point-in-time terms.
- **Initial audit requested:** Audit sentence-level claims.
- **Deliverable:** `outputs/audit/claims_consistency_register.csv` (or an equivalent, documented path); record source input hashes, exact calculations and explanatory caveats. **Never overwrite old frozen result artifacts.**
- **Acceptance gate:** No unresolved substantive internal wording or value contradiction.
- **Progress record:** owner `Codex`; result `UNASSESSED`; baseline SHA `TBD`; updated SHA `TBD`; test `TBD`; evidence link `TBD`; numerical change `TBD`; research-paper impact `TBD`; independent reviewer `PENDING`.


- **Phase4 manuscript reconciliation (1 November2026):** previous `UNASSESSED`; current `RESEARCH_LIMITATION_DISCLOSED`. Revised manuscript consistently uses matched cycle alphas,31portfolio cycles,89common monthly dates/15folds,internal q-style mapping and L1 fees. README lines17,19-22 retain historical/conflicting wording; deferred to Phase5 by instruction. Evidence: `../../outputs/audit/phase4/PHASE4_MANUSCRIPT_VALIDATION.md`, `Manuscript Tables VI-XIV; Phase4 validation report README conflict register` and source/checksum manifest. Source baseline `f22f5cbe365e98c8d5fef6b5308ff765703df173`; new manuscript `IMFP-P4-2026-11-01`; exact review checkpoint is the containing Phase4 commit. Tests:27rendered pages/26tables/6figures/26equations;843cells and all corrected table/interval values pass;27reference identities; author preservation PASS. Remaining limitation and paper consequence: Cross-document acceptance remains open because README must remain unchanged; this checkbox stays unchecked. Independent human review `PENDING`.

#### [ ] R6 — Are the author funding, conflict, supervisory and AI-assistance statements fully verified?

- **Phase / severity from initial audit:** 4 / High; **status:** `SOURCE_EVIDENCE_BLOCKED`.
- **Why this matters / failure mode:** Are the author funding, conflict, supervisory and AI-assistance statements fully verified? A mismatch can change empirical interpretation or make a paper claim stronger than the underlying data support; do not presume a defect before examining the archived outputs.
- **Inspect first:** `manuscript declarations and relevant publisher policy`. Resolve these to actual paths on the checked-out commit; record function names/line ranges rather than assuming they are unchanged.
- **Detailed verification and candidate correction:** Prepare author-only attestation checklist for funding, conflicts, supervision, AI assistance, actual consulted sources and independent human review; never auto-sign or silently delete material disclosure.
- **Initial audit requested:** Confirm personally; do not invent declarations.
- **Deliverable:** `outputs/audit/author_attestations_pending.md` (or an equivalent, documented path); record source input hashes, exact calculations and explanatory caveats. **Never overwrite old frozen result artifacts.**
- **Acceptance gate:** Personal facts remain pending until verified by the author.
- **Progress record:** owner `Codex`; result `UNASSESSED`; baseline SHA `TBD`; updated SHA `TBD`; test `TBD`; evidence link `TBD`; numerical change `TBD`; research-paper impact `TBD`; independent reviewer `PENDING`.


- **Phase4 manuscript reconciliation (1 November2026):** previous `UNASSESSED`; current `SOURCE_EVIDENCE_BLOCKED`. User explicitly authorizes supplied14pageSSRN source and instructs verbatim preservation of author name,SRM/contact,funding,conflicts,supervision and other declarations. Native-text comparison confirms all4declaration blocks/headings unchanged after whitespace normalization. Evidence: `../../outputs/audit/phase4/PHASE4_MANUSCRIPT_VALIDATION.md`, `PHASE4_AUTHOR_CONFIRMATIONS.md; PHASE4_CLAIM_TRACEABILITY.csv author records` and source/checksum manifest. Source baseline `f22f5cbe365e98c8d5fef6b5308ff765703df173`; new manuscript `IMFP-P4-2026-11-01`; exact review checkpoint is the containing Phase4 commit. Tests:27rendered pages/26tables/6figures/26equations;843cells and all corrected table/interval values pass;27reference identities; author preservation PASS. Remaining limitation and paper consequence: Preservation instruction is not independent verification or final author attestation. AI wording is retained verbatim; actual audit/revision assistance and human review require author assessment. No venue selected. Independent human review `PENDING`.

#### [x] R7 — Are the paper's IEEE-style figure and table layouts sufficiently readable?

- **Phase / severity from initial audit:** 4 / Medium; **status:** `VERIFIED_CORRECT`.
- **Why this matters / failure mode:** Are the paper's IEEE-style figure and table layouts sufficiently readable? A mismatch can change empirical interpretation or make a paper claim stronger than the underlying data support; do not presume a defect before examining the archived outputs.
- **Inspect first:** `paper DOCX/PDF and figure sources`. Resolve these to actual paths on the checked-out commit; record function names/line ranges rather than assuming they are unchanged.
- **Detailed verification and candidate correction:** Render all paper pages, inspect dense tables, formulas, references and appendix; preserve editable version, ensure no clipping or unreadable legends.
- **Initial audit requested:** Inspect all pages and legends.
- **Deliverable:** `outputs/audit/manuscript_visual_qc.md` (or an equivalent, documented path); record source input hashes, exact calculations and explanatory caveats. **Never overwrite old frozen result artifacts.**
- **Acceptance gate:** Every page is visually checked only when actually rendered and inspected.
- **Progress record:** owner `Codex`; result `UNASSESSED`; baseline SHA `TBD`; updated SHA `TBD`; test `TBD`; evidence link `TBD`; numerical change `TBD`; research-paper impact `TBD`; independent reviewer `PENDING`.


- **Phase4 manuscript reconciliation (1 November2026):** previous `UNASSESSED`; current `VERIFIED_CORRECT`. Final27pages rendered via native Word PDF export and bundled Poppler;allpages visually inspected. Final pages1-26are pixel-byte-identical to inspected pages;final27reinspected.26tables/6figures/26editableOMML equations;no clipped or missing content. Evidence: `../../outputs/audit/phase4/PHASE4_MANUSCRIPT_VALIDATION.md`, `FINAL_REVISED_MANUSCRIPT.pdf; PHASE4_TEST_AND_FORMAT_QA.txt` and source/checksum manifest. Source baseline `f22f5cbe365e98c8d5fef6b5308ff765703df173`; new manuscript `IMFP-P4-2026-11-01`; exact review checkpoint is the containing Phase4 commit. Tests:27rendered pages/26tables/6figures/26equations;843cells and all corrected table/interval values pass;27reference identities; author preservation PASS. Remaining limitation and paper consequence: Packaged render_docx failed because LibreOffice unavailable; native Word fallback and PNG review are recorded. Neutral academic review format,no invented journal template. Independent human review `PENDING`.

#### [x] R8 — Are all references and dataset DOIs correct and accessible?

- **Phase / severity from initial audit:** 4 / Medium; **status:** `VERIFIED_CORRECT`.
- **Why this matters / failure mode:** Are all references and dataset DOIs correct and accessible? A mismatch can change empirical interpretation or make a paper claim stronger than the underlying data support; do not presume a defect before examining the archived outputs.
- **Inspect first:** `bibliography and provider docs`. Resolve these to actual paths on the checked-out commit; record function names/line ranges rather than assuming they are unchanged.
- **Detailed verification and candidate correction:** Verify references, provider URLs and DOIs against authoritative sources; correct metadata without inventing consulted editions or author claims.
- **Initial audit requested:** Verify publisher/provider metadata.
- **Deliverable:** `outputs/audit/reference_verification.csv` (or an equivalent, documented path); record source input hashes, exact calculations and explanatory caveats. **Never overwrite old frozen result artifacts.**
- **Acceptance gate:** Citations are complete, relevant and supported.
- **Progress record:** owner `Codex`; result `UNASSESSED`; baseline SHA `TBD`; updated SHA `TBD`; test `TBD`; evidence link `TBD`; numerical change `TBD`; research-paper impact `TBD`; independent reviewer `PENDING`.

## Mandatory cross-cutting corrections and adversarial tests

- **Initial-NAV drawdown (early blocker P1):** test `[-0.2,+0.1]` against an expected −20% drawdown, strictly declining series, first-period losses, all-positive and zero-return paths. Include starting wealth in running peak. Report whether each published portfolio MDD actually changes; do not extrapolate from a synthetic test.
- **Fee convention (early blocker P2):** define `L1 = Σ|Δw|` and one-way notional `½L1` for self-financing rebalances. Current code uses spread/2 and slippage per absolute traded-weight unit. A 100% A→B switch has `L1=2`, so a quoted 10 bps per traded side can produce 20 bps NAV fee. That is not automatically an error: independently reconcile all 5/10/20 bps definitions, including initial deployment and observed archived trade logs, before changing costs.
- **Horizon consistency:** factor portfolios must not silently use only the returns available for securities that disappear before the common exit date. Check terminal events, delisting risk, constituent source gaps and treatment of monthly factor portfolios as non-investable research building blocks.
- **Price adjustments:** verify actual acquisition vintage, split/dividend conventions, source-change date and hashes. Claims about an external October 2026 provider change must be checked against primary provider documentation before being treated as established. Never assume present-day provider data equal the original vintage.
- **Pricing factor definition:** a project-specific q-factor mapping based on `earnings_yield` is not accounting ROE; a high-minus-low characteristic spread is not automatically the published factor portfolio definition. Check units, signs and paired sample alignment.
- **Multiple comparisons:** report number of regression alphas and inferential dependencies; 85.4% CAPM and 92.7% FF5 *nominal* significant shares cannot by themselves support a pricing discovery. Adjusted R² improvement need not imply lower pricing errors.
- **ML economics:** a 21-session forward target requires timestamp-aware purging, month-close/market-close availability validation and predictions frozen before the holding window. Check fold calendar and economic strategy fills separately.
- **Publication controls:** original manuscript remains historical; any corrected output must have a new manifest, before/after comparison and author-approved wording. The author, not Codex, must verify actual funding, conflicts, supervision and AI-assisted work.

## Checkpoint template — append once per completed issue

```
Issue: <ID>
Status: <one permitted status>
Phase: <1-5>
Observed failure / verified-correct behavior: <specific evidence>
Original code/output hash: <sha256 or N/A with explanation>
Independent numerical calculation: <formula, values, units, test>
Source files and lines: <paths + symbol/line>
Changed files: <minimal diff>
Historical value -> corrected value: <both, or unchanged>
Empirical impact: <what findings change, and what does not>
Paper claim / table impact: <table/section and proposed correction>
CI and test evidence: <command, observed outcome, run URL>
Residual limitation: <what still cannot be known>
Commit SHA and validation date: <value>
Reviewer approval / next blocker: <result>
```

## Per-phase signoff template

```
Phase number:
Branch and baseline SHA:
Issue IDs completed / unresolved:
Before/after outputs and publication IDs:
True implementation errors fixed:
Items still source blocked or research-limited:
Exact tests actually run (with counts):
Verified immutable original evidence:
Files changed and justification:
Paper/README intentionally not edited? [yes/no]
Next dependency gate: PASS / PASS_WITH_LIMITATIONS / BLOCKED
```

## Final professor/committee gate

Judge **financial accuracy, point-in-time validity, source-vintage clarity, pricing-test independence, investability of factor portfolios, net portfolio accounting, valid ML chronology, inference and claims**. Passing software tests alone does not satisfy any empirical gate. Favor precise negative or inconclusive results over artificially high metrics. No applicant-specific admissions score or claimed university endorsement is part of the empirical audit.

## Final Git safety and publication gate

- Commit all tracker updates and versioned evidence to phase-specific working branches. `main` remains unchanged during Phases 1–4.
- Preserve original empirical source hashes, old manuscript, and evidence history. Avoid deleting artifacts that have provenance value.
- Only an explicitly authorized, reviewed Phase 5 PR may update the public `main` branch after all critical issues are resolved or accurately bounded.
- A concise README should link to the final verified sources and distinguish paper-vintage results from later revised study results. No paper changes silently applied to the already-posted SSRN version.

## Verified repository baseline — 1 November 2026

- Live GitHub main and clean fresh clone: `4e7fbdc380b8042db72e9c628260f60077a205ef`.
- Working branch: `research/institutional-phase1-financial-audit`, created directly from that main.
- Other remote branches: `audit/fix-period-alignment-risk-metrics` at `ce36c399c1e64686de25d3f5702e22cd13647b8b`; `research/correct-return-frequency-and-risk-metrics-2026-10-13` at `51ae02815b20c1c857d17b243023847b32ad2934`.
- Open PRs: #8 (draft, ce36c39) and #7 (51ae028); both propose financial corrections, neither merged. Closed PRs #2–6 merged; #1 closed unmerged. Existing PR evidence must be independently checked before reuse.
- Baseline Actions run 37338079331: completed/success. PR #8 run 38409266153 success; PR #7 run 38303222633 failure. These are software CI observations, not independent empirical reproduction.
- README and methodology: `README.md`, `docs/METHODOLOGY.md`, `docs/DATA_AND_SOURCES.md`, `docs/RESULTS.md`, `docs/LIMITATIONS.md`, `docs/REPRODUCIBILITY.md`.
- Structure: `src/institutional_factor_platform` data/adapters, factors, asset pricing, backtest, portfolio, risk, ML, research-output storage and delivery; `tests/`, `config/`, `.github/workflows/quality.yml`.
- Both research tags resolve to the historical empirical release identified as `5a3e930665756fa7aaedeceb5f9ab90792bcf849` (tag target verification recorded in Phase 1 manifest).
- Current main contains no original PDF/DOCX/TeX manuscript or empirical source/output files. Historical `docs/FINAL_RESEARCH_PAPER.md` is available through the research tag; it names factor publication `factor-5a73616f131fca2102fa2ca4141ad64f` and pricing publication `asset-pricing-c0a72fae5349f1048e18557250da1927`. Names alone do not authenticate absent publications.
- `data/` contains only access notes; third-party data, generated Parquet, manifests and outputs are excluded by `.gitignore`. No original market/fundamental observations, frozen portfolio net paths or transactions are supplied in the clean clone. Existing source hashes/manifests cannot be validated until their actual bytes are located.
- No prior master tracker exists in current main. Earlier engineering audit reports survive in the research tag, including `docs/PHASE1_AUDIT_REPORT.md`, `docs/PHASE1_REAUDIT_REPORT.md`, `docs/PHASE1_FINAL_REAUDIT_REPORT.md`; these use a different historical engineering phase taxonomy. Their unique evidence is retained in Git history and is not automatically treated as financial-issue closure.
- No pre-existing uncommitted changes in this fresh clone. Other user checkouts were not altered or assumed clean.
- This initial commit establishes all 50 issue IDs unchanged. Phase 1 investigation follows this commit; no issue is yet resolved.

## Phase 1 calculation checkpoint — 1 November 2026

P1: confirmed function defect in `risk/metrics.py::drawdown`: the initial peak omitted NAV=1. Synthetic [-0.2,0.1] originally returned 0 drawdown, independently expected -0.2. Running peak now has a floor of 1.0. The seven path regressions include falling, recovery, positive/negative constant and flat paths. Published strategy effects remain SOURCE_EVIDENCE_BLOCKED; no frozen net paths are present.

D8: confirmed incomplete-history publication defect in `factors/portfolio.py::compute_factor_portfolios`: constituent returns could cover fewer sessions, or an inner join could remove a formed security. Added a fail-closed check for every formed member against the supplied common benchmark calendar, including duplicate or null returns. No synthetic terminal return is inserted. The benchmark-calendar test now uses complete security histories; four additional regressions reject first/last/all/null missing evidence. A missing session for the entire supplied panel remains undetectable without the external trading calendar, and a final truncated sample is not established as a full monthly observation.

Before correction: `uv run pytest tests/test_research_phase1_audit.py --no-cov -q` produced 8 failed / 16 passed (four initial-loss cases and four incomplete-holding cases failed). After correction: six targeted modules produced 88 passed; expanded independent reference suite produced 29 passed. Full phase verification is pending. No historical numerical output was recalculated or overwritten. Complete issue records and unresolved acceptance gates follow in the phase report.


## Phase 1 evaluated outcome — 1 November 2026

`PHASE1_BLOCKED_BY_SOURCE_EVIDENCE`. Investigated D1–D9, V1, P1 and P2; none satisfy the full empirical acceptance gate. All remain unchecked. D9 is NEEDS_REVIEW (raw beta aliases and timing interpretation); the other eleven are SOURCE_EVIDENCE_BLOCKED. P1 and D8 have code-level corrections with passing regressions but retain unresolved empirical propagation. P2 arithmetic is verified on synthetic trades; historical transactions remain absent. No other issues assessed or changed.

The authoritative supporting report is `outputs/audit/phase1/PHASE1_FINANCIAL_DATA_VALIDATION.md`; issue-level findings, formulas, hashes, tests, manuscript consequences and precise missing-source requests are recorded in that report and PHASE1_ISSUE_RESULTS.csv. The initial tracker commit is ea2846d; source corrections are 3b435f3. Final validation and evidence are identified by the Git commit containing the report. No Phase 2 work authorized or started. Independent review remains pending.

### Baseline manuscript-history addendum

A targeted reachable-history filename search recovered two 30-page PDF versions removed before current main: `c778a12404596a1a936ec58ddba7750b8795a8c4:paper/Institutional_Multi_Factor_Asset_Pricing_Research_Paper.pdf` (SHA256 `ab9bbbbdd5ddef1b84c46667fd4f02f5ee717ac5178761f79e7c95a4cdad4251`) and `868baa9dd2770f118c30706ed37f62451aae9f38:paper/An_Auditable_Public_Data_US_Equity_Research_Pipeline.pdf` (SHA256 `2ea1a0767030e8693a91695940795996329302e898ac47163b3b395672e70a64`). Relevant Phase 1 pages were text-inspected without manuscript edits or a Phase 4 visual audit. All eight reported MDDs and Table 8 cost components are now documentary inputs in the Phase 1 report/reconciliation; their frozen empirical paths remain absent. Appendix A's uniform row counts versus valid-observation terminology requires later clarification (D3/D7/D9). No editable DOCX/TeX/bibliography sources were found in reachable history. Exact identity with any externally posted version remains unverified. Both PDFs remain immutable in their historical Git blobs.


### Final Phase 1 verification and stop gate

Full phase-level software verification: 330 passed, 115 warnings in 1444.39s (24m04s); 90.52% branch-aware coverage; pytest exit0; separate coverage report --fail-under=90 exit0. Relevant targeted tests passed (88 initial targeted, 29 expanded independent, 50 final calendar/reference). Static, configuration, delivery and audit-integrity checks pass. Source checkpoint `ef339ab1a7805242e67284cd54fbcf23fae86da1`; final evidence is identified by the commit containing the phase report.

Final status: `PHASE1_BLOCKED_BY_SOURCE_EVIDENCE`. D1–D9/V1/P1/P2 were investigated; eleven are source-blocked and D9 needs review. P1/D8 source defects have regression-proven code corrections; historical propagation remains blocked. All 50 issue IDs and all checkboxes remain preserved; later 38 issues remain UNASSESSED. Main was live-rechecked unchanged at the baseline; both historical PDFs and the Markdown paper remain unchanged. Independent review pending. Do not begin Phase2 or rewrite the manuscript.

## Phase 2 source-evidence gate — 1 November 2026

Branch `research/institutional-phase2-asset-pricing-validation` starts at accepted Phase 1 commit `10b3dc353f604ef332f55c153b093d1628a4ff7f`. Live main remains `4e7fbdc380b8042db72e9c628260f60077a205ef`. Phase 1 and historical correction branches are preserved.

The newly authorized broader local search located `G:\4- Institutional Multi-Factor Asset Pricing & Portfolio Analytics Platform`, containing the actual historical factor/pricing publications and normalized parent datasets. Read-only authentication passed factor and pricing manifests, all bound artifacts, factor-parent linkage and finalized parent lifecycle evidence. This adds available evidence; it does not rewrite the historically scoped Phase 1 report or silently close D4/D8/D9/V1. Full inventory and qualifications will be recorded in `outputs/audit/phase2/PHASE2_SOURCE_MANIFEST.json`.

AP1 checkpoint: independent OLS/Bartlett-HAC matrix reconstruction of all 615 archived regressions agrees within numerical roundoff (maximum coefficient discrepancy 2.67e-15; p-value discrepancy 8.24e-15). CAPM mean adjusted R² 0.0634395196779754 is reproduced as an archived implementation result. Confirmed construction defect: daily realization-date market/cash observations were joined to holding-period returns. The targeted reference test failed before correction (1 failed/4 passed) and passes after interval compounding and interval-key alignment. Relevant prior implementation from PR #8 was independently checked and reused for this file only; no PR was merged, and its proposed numerical q mapping change was not adopted. Historical ROE alias remains earnings_yield, with clarified study-specific q-style labeling. Final AP1 empirical implications and acceptance remain under investigation.


## Phase 2 evaluated signoff — 1 November 2026

`PHASE2_CORRECTIONS_REQUIRED`. All AP1-AP10 investigated. Six research limitations documented (AP3/AP4/AP6/AP7/AP8/AP9); AP1/AP2/AP5 NEEDS_REVIEW, AP10 SOURCE_EVIDENCE_BLOCKED. Checked boxes mean completed bounded investigation/disclosure, not approval of the original study. Source checkpoint `62343e686475552a0b629d63b5445a6203ea90f7`; final evidence is the Git commit containing `outputs/audit/phase2/PHASE2_ASSET_PRICING_VALIDATION.md`. The original archive was newly located outside the Phase1 checkout and authenticated; archived615 regressions and11545 quantile returns reproduce, but the daily/holding-period pricing mismatch was confirmed and corrected. All new interval/common-sample results remain supplementary because265 original quantile groups have incomplete holdings. Historical ROE mapping retained and qualified. Full tests343 passed with90.58% branch-aware coverage;35 targeted passed. H1/H3 remain inconclusive with missing original approval/decision evidence. Main, Phase1 branch, pre-existing correction branches, manuscripts and old results remain preserved. Independent review pending; do not start Phase3 or edit paper/README.

## Phase 2B baseline and predeclared policy — 1 November 2026

New branch `research/institutional-phase2b-empirical-correction` starts at exact accepted Phase2 SHA `0745139d20d8de0789eada3e13ca327beff28805`. The working tree was clean. Live main and Phase1/2 remote heads match the recorded immutable baselines; accepted NAV, D8 fail-closed and market/cash interval corrections are present. No older PR or branch was merged.

All76 source artifacts used in Phase2 were rehashed unchanged. The historical factor and pricing publications, parent hash relationship and both finalized market/fundamental dataset authorities reauthenticated. The supplied common market dates cover all2128 XNYS sessions in their observed study window, with no missing or non-session dates. Source-cache pre-existing API/frontend changes remain outside this audit checkout and will be preserved.

Before corrected performance is calculated, `config/research_phase2b.yaml` freezes the full-XNYS delayed-close policy: month-end UTC information cutoff; execution at the following XNYS close; common exit at the next monthly execution close; no incomplete terminal cycle; memberships fixed before inspecting holding returns; whole-quantile exclusion for unsupported paths; no zero/cash/stale fill or survivor re-ranking. Recoveries require original same-vintage security-specific evidence. Frozen factor definitions, thresholds and historical q mapping remain unchanged. Primary pricing uses per-asset common model dates, with model-specific samples supplementary. All source/PIT/return-basis limitations remain explicit until investigated. This phase will produce new immutable publications or precise affected blockers, not overwrite historical ones.

### Phase 2B policy amendment before corrected model calculation

Independent endpoint checks found that the Phase2 count of265 groups was a missing-session diagnostic, not265 proven wrong holding returns. For195 groups, interior quote gaps are bridged by the next genuine stored return and the complete holding-period return agrees with observed endpoint prices (individual-case errors at numerical roundoff). Seventy original groups, involving BDTX and CRSP, genuinely lack the scheduled endpoint and were split onto earlier realization dates. This distinction preserves the original evidence while correcting its interpretation.

Before calculating new model performance, methodology `full-xnys-delayed-close-endpoint-v2` replaces the excessively strict interior-daily-quote requirement. For fixed formation weights, an authenticated observed-quote return chain may span an interior gap if every stored link matches its source quote ratio, it covers the complete execution-to-exit interval, and the compounded return matches the genuine endpoint ratio. No unobserved daily prices, zero returns, stale valuations or cash substitutions are inserted, and no intraperiod NAV is asserted. Execution/end quotes, date-effective security identity, complete common benchmark/cash calendar, endpoint consistency and terminal evidence remain mandatory. The same rule applies to positive and negative returns and all quantiles. The earlier strict policy remains in Git history; no new corrected model result was examined before this amendment.

## Phase2B evaluated signoff — 1 November2026

`PHASE2B_READY_WITH_LIMITATIONS`. Exact base `0745139d20d8de0789eada3e13ca327beff28805`; branch `research/institutional-phase2b-empirical-correction`; empirical source `291447199fe603f0168d972ee77b88c4d949f205`. All50original IDs retained;16 dependency records updated (14focus plus AP4/AP10). New factor `factor-4ddee9ac6fb45cedfd62a2cc68676b58`, primary matched pricing `asset-pricing-d60bee7310b34976c80372a0f0f29e21`, supplementary pricing `asset-pricing-8c2396179c4b509796b2cab043ec31d2` generated/authenticated at configured data roots; manifest hashes recorded in `outputs/audit/phase2b/PHASE2B_SOURCE_MANIFEST.json`. Private publications are preserved locally and not committed.

265groups/277occurrences individually reconciled:195 valid interior-gap chains,70 unavailable old endpoints; none represented as recovered. All shifted new intervals pass genuine endpoints. Original11545 rows become11352:70split-end consolidations plus123terminal partial-cycle exclusions. New fixed membership has1,138,880occurrences. All123 assets remain;615primary fits useN67-77 identical per-asset model dates with no month gaps. Every corrected holding return, spread, market/cash interval and1230total fits independently reproduces. Full358tests pass at90.68%;37targeted, type/lint/format/lock/delivery checks and hashes pass.

D3tiny samples,D4complete PIT,D5exhaustive class attribution,V1exact return basis remain open/qualified;AP10source-blocked. No unqualified total-return/performance claim follows. Original papers/results/main/Phase1/Phase2/olderbranches unchanged. Phase3not started; stop for independent review.

## Phase2C independent verification signoff — 1 November2026

`PHASE2C_VERIFIED_WITH_ECONOMIC_LIMITATIONS`. Branch `research/institutional-phase2c-regression-verification` starts at exact94f347476c86962d2d7479a74b8fa915a5849668. All615primary and615supplementary regressions independently reproduced from complete reconstructed matrices; all11352returns and1,138,880formation memberships agree. Negative mean alphas and .76-.82mean adjustedR2 are verified; no Phase2B defect, numerical change or new official publication required. Full366tests pass at90.68%;45targeted and static/lock/hash checks pass. One frozen self-inclusion diagnostic retains109assets and excludes14empty-leg cases, without establishing external independence. OnlyAP3/AP5/AP6/AP7/AP8/AP9 interpretation records updated; all50IDs and prior statuses/checkboxes retained. Main, earlierbranches, historical publications/manuscripts/README and frozen inputs unchanged. Stop here; noPhase3 or paper rewrite.

## Phase3 complete signoff — 1 November2026

`PHASE3_VERIFIED_WITH_LIMITATIONS`. Branch `research/institutional-phase3-validation`, exact base277c95bd4ba7279e6863bc3acc026d406a8ad482. AllP1-P12/ML1-ML10 investigated:7verified,4fixed issues covering5distinct defects,8disclosed limitations,3source-blocked. All50IDs retained. Historical maximum-diversification MDD-5.43%is verified; initial-NAV effect0 for all8historical maxima.24new portfolio publications preserve8methods and3fee scenarios;32old cycles become31full cycles. CVaR83.17%/Sharpe1.667 becomes73.68%/1.252; cash-only repair on old path gives1.379. Corrected ML has27632rows/89true monthly dates/15folds,not27640/91distinct dates/17folds. Eight existing families retrained only for confirmed calendar/label changes; later metric-only republishing does not refit models. Positive nominal IC intervals do not establish stable economic value; economic checks remain isolated1-session resets,not21-session investments. Final372tests pass/90.62%;91targeted pass. Preliminary broad run interrupted58%after an actual-data constant-IC defect; one complete final run after the final core correction. Accepted1230regressions and11352factor-return experiment were not repeated. P8/ML4/ML5source-blocked;D4/V1unchanged. Main,previousbranches,originalpapers/README/data/publications preserved. NoPhase4editing orPhase5cleanup.

- **Phase4 manuscript reconciliation (1 November2026):** previous `UNASSESSED`; current `VERIFIED_CORRECT`. All27 materially used reference identities checked against DOI registry/publisher/provider metadata. Corrected dataset title/explicitURLs and current access dates; historical consultation not retroactively attested. Evidence: `../../outputs/audit/phase4/PHASE4_MANUSCRIPT_VALIDATION.md`, `References; PHASE4_PUBLICATION_SOURCE_MANIFEST.json reference_verification` and source/checksum manifest. Source baseline `f22f5cbe365e98c8d5fef6b5308ff765703df173`; new manuscript `IMFP-P4-2026-11-01`; exact review checkpoint is the containing Phase4 commit. Tests:27rendered pages/26tables/6figures/26equations;843cells and all corrected table/interval values pass;27reference identities; author preservation PASS. Remaining limitation and paper consequence: Current HF documentation/Zenodo record describes October2026 restructuring; not a replacement for frozen historical-vintage evidence. Bibliographic checks do not attest author consultation. Independent human review `PENDING`.


## Phase4 manuscript signoff — 1 November2026

`PHASE4_READY_WITH_AUTHOR_CONFIRMATIONS`. Branch `research/institutional-phase4-manuscript-revision`, exact base `f22f5cbe365e98c8d5fef6b5308ff765703df173`. AllR1-R8 investigated;4verified-correct,3disclosed limitations,1source-blocked. R5(deferredREADME) andR6(author attestation) remain unchecked. All50stable IDs retained; upstream source/timing/hypothesis blockers unchanged. New27page revision has26tables,6figures and26editable equations;843cells checked and allpages rendered/inspected.954traceability records include359original digit-containing passages. Author-designated14page SSRN text governs; author details and4declaration blocks preserved verbatim. Manuscript hash/delivery boundaries and source identities are in the Phase4manifest. No financial-code/model/main/README/historical-manuscript change or new research experiment. Human review pending; stop beforePhase5.
