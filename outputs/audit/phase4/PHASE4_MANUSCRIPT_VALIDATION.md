# Phase 4 manuscript validation

**PHASE4_READY_WITH_AUTHOR_CONFIRMATIONS**. The qualified revised paper is ready for final human review, not final publication clearance. R1-R8 are investigated; author-dependent attestations and deferred cross-document README consistency remain open. No Phase5 work was started.

## Verified baseline and manuscript authority

Repository: https://github.com/amitdudi04/institutional-multi-factor-asset-pricing-platform. Branch `research/institutional-phase4-manuscript-revision` starts at exact accepted `f22f5cbe365e98c8d5fef6b5308ff765703df173`. Main remains `4e7fbdc380b8042db72e9c628260f60077a205ef`. The containing Phase4 commit identifies this evidence without a self-referential hash. Remote Phase1-3 lineage/heads were verified; the checkout was clean at branch creation. No original paper is tracked in the accepted audit checkout's current `paper/` tree; historical Git authority is in the preserved archive.

The author explicitly designated `C:/Users/amitk/Downloads/ssrn-7528419 (1).pdf` as authority:14pages,SHA256 `8616305ba1043c7641a4388aad0d677cd2bd7d35e6d4c5ae2ca401ec120c2608`. Its displayed title is An Auditable Public-Data U.S. Equity Research Pipeline: Point-in-Time Factors, Asset Pricing, Portfolio Construction, and Walk-Forward Machine Learning, by Amit Kumar Dudi. Stale PDF metadata identifies IEEE/PaperTitle; visible author text governs. The original30page archived paper SHA256 `ab9bbbbdd5ddef1b84c46667fd4f02f5ee717ac5178761f79e7c95a4cdad4251` is historical,not the latest authority; archive Git commit `c778a12404596a1a936ec58ddba7750b8795a8c4` contains blob `8417463c920ddb629fef3abba15d5840229ed30d`. The alternative30page copy has SHA256 `2ea1a0767030e8693a91695940795996329302e898ac47163b3b395672e70a64`. Related older editable DOCX sources and ledgers were inspected without modification; this revision is a new editable reconstruction of the supplied PDF,not the original editable document.

No new venue was selected. Original title,author line,SRM/contact,supervision,funding,conflicts and AI declaration are preserved exactly. Four declaration blocks/headings match after PDF whitespace normalization. Preservation is not independent verification: all are flagged `AUTHOR_CONFIRMATION_REQUIRED` in the claim ledger and author-confirmation file. In particular,the retained AI wording must be assessed against the actual audit/revision assistance and final human review. No new supervisor,institutional endorsement,funding or personal attestation was invented.

## Numerical reconciliation and evidence reuse

Pricing: all5matched primary rows reproduce accepted source precision: mean adjustedR² CAPM0.760818,FF30.802438,Carhart40.811021,FF50.817658,q-style0.814361; mean cycle alpha -0.001658,-0.001967,-0.001879,-0.002008,-0.002227; nominal HAC intercept counts8,12,14,8,9 of123. Matched67-77observations/asset,9441asset-cycles/model. No supplementary-model-specific cells replace primary values. No intercept survives supplementary Holm adjustment; that is not proof of zero true alpha. Six duplicate pairs,shared exposures and109asset self-inclusion sensitivity remain disclosed.

Portfolios: all8BASE rows and24scenario identities match Phase3reconciliation.31complete cycles replace32historical cycles;123long-only quantile sleeves are distinct from487equities. Corrected CVaR73.68%/Sharpe1.252; historical83.17%/1.667 remains archived. Cash-only old-path Sharpe1.379 is distinguished from changed inputs/sample. Historical maximum-diversification MDD-5.43% is verified,corrected path-4.83%; initial-NAV adjustment changes no historical minimum. Trading fees preserve5/10/20bps per L1 units,not changed assumptions.

ML: all8families and six finite block intervals match accepted final publications; constant baselines remain undefined.27632rows,89common months,15dependent folds,7286held-out rows/model. Corrected means: composite/linear0.034430,Ridge0.034434,ElasticNet0.044609,RF-0.002641,XGB-0.023285. Exploratory intervals are positive for linear families,cross zero forRF and negative forXGB. Block3/100resamples/seed17 replaces the old1000resample description. Economic means are one-session reset-to-cash checks,not a21-session wealth backtest. Stable incremental after-cost value remains unestablished. Higher aggregate linear IC is not isolated improvement: matched old predictions give0.037238 versus corrected0.034430.

The final gate reused Phase3's7bound evidence hashes and540unchanged-size/mtime guards,checked32pointer/manifest pairs and264small correctedJSON artifacts,and retained all accepted factor/pricing authority identities. No1230regressions,11352return reconciliation,24portfolio publications,8model fits,SEC ingestion or factor pipeline was rerun. A minimal descriptive column read was justified to authenticate old TableIV/AppendixC and breadth claims not otherwise tied to accepted corrected summary cells. Six original descriptive rows and9annual breadth rows reproduce; this is not a new investment experiment. Current HF/Zenodo metadata describes a restructured IEX-only release; this does not replace frozen vintage or closeV1.

## Claim and hypothesis coverage

The matrix contains **954records**:359original digit-containing PDF passages,249legacy ledger metrics,222revised table rows,81revised numerical paragraphs,26equations,7hypotheses and10author records. Counts include repeated,structural,configuration and bibliographic numbers; they are not independent empirical claims or new tests. Original passages retain exact PDF page/line context; revised rows record units,sample,publication IDs,evidence,status and reviewer notes. Legacy field-level records retain old values and explicit replacements/omissions. Every main table I-XV and appendices are covered. No historical verification label is accepted solely because an older ledger says VERIFIED.

All7hypotheses retain supplied wording,intended evidence,historical conclusion,revised interpretation,citation and limitation in AppendixI. H1/H3 remain inconclusive. H2/H5 historical shorter-versus-extended wording and earlierH3direction uncertainty are explicit; no approval or new confirmatory rule is fabricated. Old scenario impact cells and legacy-only risk statistics are not propagated to a different corrected experiment. Their removal is recorded,not silently treated as zero.

## Publication issue outcomes

| ID | Status | Acceptance |
|---|---|---|
| R1 | `RESEARCH_LIMITATION_DISCLOSED` | Completed bounded investigation |
| R2 | `RESEARCH_LIMITATION_DISCLOSED` | Completed bounded investigation |
| R3 | `VERIFIED_CORRECT` | Completed bounded investigation |
| R4 | `VERIFIED_CORRECT` | Completed bounded investigation |
| R5 | `RESEARCH_LIMITATION_DISCLOSED` | Open |
| R6 | `SOURCE_EVIDENCE_BLOCKED` | Open |
| R7 | `VERIFIED_CORRECT` | Completed bounded investigation |
| R8 | `VERIFIED_CORRECT` | Completed bounded investigation |

**R1:** All359 digit-containing original PDF passages inventoried;249 legacy field records inspected;222 revised table rows,81 numerical narrative paragraphs and26equations mapped. Unsupported scenario/legacy-only risk cells omitted explicitly. Original hypotheses preserved; author statements pending. Evidence: `PHASE4_CLAIM_TRACEABILITY.csv; manuscript Tables I-XV and Appendices A-L`. Remaining limitation: Every material claim is reproducible within stated evidence or explicitly qualified/pending; missing H1/H3 approval is not repaired.

**R2:** Public code/configuration/audit evidence separated from private frozen Parquet and model bundles. Lawful original-input access is required; current vendor downloads do not reproduce source vintage. Evidence: `Manuscript Data and code availability; PHASE4_PUBLICATION_SOURCE_MANIFEST.json`. Remaining limitation: Original vendor retrieval/adjustment and redistribution permissions remain bounded; no private raw data published.

**R3:** 372tests/90.62%coverage are attributed to accepted Phase3,not new Phase4 execution or proof of causality/PIT/investability. Document checks independently verify843table cells and corrected values. Evidence: `Manuscript Section X/Appendix J; PHASE4_TEST_AND_FORMAT_QA.txt`. Remaining limitation: Software assurance is distinct from empirical provenance and economic generalizability.

**R4:** 32final accepted corrected portfolio/ML authority pairs and264smallJSON artifacts authenticate against stored hashes. Corrected factor/pricing parents retained; ML actual historical raw-score/cost dependencies distinguished from quantile returns. Evidence: `Manuscript Appendix H; PHASE4_PUBLICATION_SOURCE_MANIFEST.json`. Remaining limitation: No result IDs regenerated; final ML IDs exclude superseded intermediates. Large source hashes reused through540stat guards.

**R5:** Revised manuscript consistently uses matched cycle alphas,31portfolio cycles,89common monthly dates/15folds,internal q-style mapping and L1 fees. README lines17,19-22 retain historical/conflicting wording; deferred to Phase5 by instruction. Evidence: `Manuscript Tables VI-XIV; Phase4 validation report README conflict register`. Remaining limitation: Cross-document acceptance remains open because README must remain unchanged; this checkbox stays unchecked.

**R6:** User explicitly authorizes supplied14pageSSRN source and instructs verbatim preservation of author name,SRM/contact,funding,conflicts,supervision and other declarations. Native-text comparison confirms all4declaration blocks/headings unchanged after whitespace normalization. Evidence: `PHASE4_AUTHOR_CONFIRMATIONS.md; PHASE4_CLAIM_TRACEABILITY.csv author records`. Remaining limitation: Preservation instruction is not independent verification or final author attestation. AI wording is retained verbatim; actual audit/revision assistance and human review require author assessment. No venue selected.

**R7:** Final27pages rendered via native Word PDF export and bundled Poppler;allpages visually inspected. Final pages1-26are pixel-byte-identical to inspected pages;final27reinspected.26tables/6figures/26editableOMML equations;no clipped or missing content. Evidence: `FINAL_REVISED_MANUSCRIPT.pdf; PHASE4_TEST_AND_FORMAT_QA.txt`. Remaining limitation: Packaged render_docx failed because LibreOffice unavailable; native Word fallback and PNG review are recorded. Neutral academic review format,no invented journal template.

**R8:** All27 materially used reference identities checked against DOI registry/publisher/provider metadata. Corrected dataset title/explicitURLs and current access dates; historical consultation not retroactively attested. Evidence: `References; PHASE4_PUBLICATION_SOURCE_MANIFEST.json reference_verification`. Remaining limitation: Current HF documentation/Zenodo record describes October2026 restructuring; not a replacement for frozen historical-vintage evidence. Bibliographic checks do not attest author consultation.

## README conflicts deferred to Phase5

| Existing location | Conflict | Correct manuscript treatment |
|---|---|---|
| README line17 | Unqualified point-in-time label | Recorded availability controls; exhaustive capture chronology unresolved |
| README line19 | Historical0.063/0.259/0.277/0.301/0.296fit | Corrected matched-sample0.760818/0.802438/0.811021/0.817658/0.814361 |
| README line20 | One-way fee label without L1 qualification | Per-side5/10/20bps applied to absolute L1; half-L1 separately defined |
| README line21 |27640rows/91months/17folds |27632rows/89common dates/15folds; historical91dates covered89months |
| README line22 | All IC intervals include zero | Some positive nominal intervals; negativeXGB; stable economic value unestablished |

README and related historical methodology/results docs are intentionally unchanged. R5's cross-document gate therefore stays open; this is not authorization to perform Phase5 cleanup.

## Document and formatting QA

Final **27pages,26tables,6figures,26nativeeditable equations**. Fifteen main tables retain historical numbering; eleven appendix tables preserve technical detail. All843native table cells match the controlled manuscript source; corrected pricing/portfolio/ML numerical anchors and interval endpoints appear in the PDF. Every nonempty native DOCX paragraph appears in the PDF after removing only page-number footers and layout whitespace. Bibliographic identities for all27materially used references were checked against primary publisher/provider or DOI registry metadata; no author consultation is attested.

The packaged `render_docx.py` was attempted and failed because LibreOffice was unavailable. A separate native Microsoft Word automation instance exported the exact DOCX to PDF without modifying other documents; bundled Poppler rendered all pages. Every page was visually inspected at100dpi. The final edit shortened only the ending provenance paragraph: pages1-26are byte-identical PNGs to the inspected revision; finalpage27was re-rendered and inspected. No clipped tables,missing glyphs,overlap,unreadable figure labels or nearly empty trailing page remains. All PDF characters pass safe-page bounding checks. This is actual rendered QA,not text-only layout certification.

No financial source code/configuration changed,so the software suite was not rerun. Accepted Phase3 results remain372passing tests/90.62%coverage and91targeted tests. Phase4 checks are document,source-integrity,numerical-display and formatting checks; their results are separate in `PHASE4_TEST_AND_FORMAT_QA.txt`.

## Delivery and remaining limits

Single authoritative revision: `IMFP-P4-2026-11-01`. Local author delivery is `outputs/audit/phase4/` under this task workspace,containing the8requested files. Editable DOCX is controlled local delivery and is **not committed**; PDF plus6supporting evidence files are committed under repository `outputs/audit/phase4/`. Both manuscript byte hashes are in the public checksum manifest. No claim that uncommitted DOCX bytes exist on GitHub is made. Rendering images,scratch builds and private source/model bundles are excluded.

Final human review remains necessary for preserved author statements,original hypothesis authority and submission policy. Economic limits remain sparse/selected universe,SEC capture/share-class mapping,provider vintage/dividends,modeled execution/timing,dependent portfolios,short horizon,outer-only costs,retrospective forecasts,dependent folds and one-session economics. Upstream D4/V1,AP10,P8,ML4/ML5are not closed by manuscript reproduction. R5 andR6checkboxes remain unchecked. No stronger alpha,causality,portfolio superiority or ML-profit claim is added.

Main,earlier branches,README,financial source code,model configuration,original manuscripts and all original/corrected immutable research publications remain unchanged. The narrow Phase4text LF policy protects committed evidence bytes only. Final independent human review is pending; the phase stops here without merge or Phase5work.

## Explicit hypothesis evidence table

The7 `HYPOTHESIS` records in the claim CSV contain original wording,intended statistical test,historical conclusion,corrected available evidence,revised interpretation,evidence citation and remaining limitation in named columns. They form the complete machine-readable hypothesis-evidence table; manuscript TableV/TableXV and AppendixI provide its readable presentation without an overflowing seven-column document table. Original H2/H5 wording variations remain explicitly flagged.
