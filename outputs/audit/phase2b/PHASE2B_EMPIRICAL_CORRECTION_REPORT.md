# Phase2B empirical correction report

**Status: `PHASE2B_READY_WITH_LIMITATIONS`.** New factor and two pricing publications were actually generated and independently reconciled. Complete point-in-time and total-return source validation remains qualified. Stop for independent review; no Phase3 or manuscript work was performed.

## Baseline and authentication

Repository: [institutional-multi-factor-asset-pricing-platform](https://github.com/amitdudi04/institutional-multi-factor-asset-pricing-platform). Branch `research/institutional-phase2b-empirical-correction`, exact base `0745139d20d8de0789eada3e13ca327beff28805`. Empirical source checkpoint `291447199fe603f0168d972ee77b88c4d949f205`. The Git commit containing this report is the final phase-evidence commit, avoiding a self-referential commit hash inside its own file.

Live main remains `4e7fbdc380b8042db72e9c628260f60077a205ef`, Phase1 `10b3dc353f604ef332f55c153b093d1628a4ff7f`, Phase2 the exact base. PR7/8 were not merged; relevant alignment evidence was already reviewed in Phase2. README, original manuscripts and historical results are unchanged. The G: archive retains its pre-existing two API modifications and untracked frontend; audit code executes from this checkout.

All76 accepted Phase2 source artifacts rehashed unchanged. Original factor `factor-5a73616f131fca2102fa2ca4141ad64f`, manifest hash `9fc526c05fb1c63e1d04a4322f7779c40b877674a82d056ed0d3390afc78567f`, and pricing `asset-pricing-c0a72fae5349f1048e18557250da1927`, hash `995e2f8870de9717b0f205cb6693157f02285efeeb332b729a2fe8726e7c8b06`, authenticate including their parent link. Both input datasets authenticate as FINALIZED: market715447rows / SHA256 `19e7c9bc3cad776bde6de94de6322045c92e5673421c35bd5573c9e411d3e410`; fundamentals37273rows / `497fe518ba1b3044bda1381cbee0c367c89b24abb8472b7311a014a79a6f229a`. Full paths, schemas, dates, retrieval metadata, IDs and hashes are in `PHASE2B_SOURCE_MANIFEST.json`. This authenticates bytes/authority, not every historical vendor assertion.

## Frozen policy and individual holding audit

Policy commits `0a2583f` and `a982dd6` precede corrected model performance. Method `full-xnys-delayed-close-endpoint-v2` uses genuine month-end UTC-day signal cutoff, modeled next-XNYS-session close execution, and exit at the following monthly execution close. Membership/positive normalized cap weights are fixed before future inspection. Three eligible names/all three quantiles are required. Unsupported endpoints reject a whole quantile; no survivor ranking/weighting, zero/cash/stale fill or invented terminal payout is permitted. This is a full monthly trading cycle, not a calendar-month or daily NAV claim.

Common market/cash has exactly2128 XNYS sessions,2018-02-14–2026-08-04, with no missing/duplicate/non-session dates; exchange_calendars 4.13.2 supplies actual sessions/early closes. Provider date-only quotes do not certify complete intraday bars, closing auctions or executable fills. Every retained window contains19–23 return sessions, strictly after execution and through its common exit. The terminal unobserved full cycle is excluded entirely.

`PHASE2B_FACTOR_HOLDING_AUDIT.csv` individually records **265groups/277affected occurrences**, all formation IDs/weights, expected/observed sessions, actual/intended endpoints, original inclusion/subset weights, source/event evidence and new admissibility. Memberships were re-formed from frozen scores and matched to the validated historical reconstruction.

- **195 COMPLETE_VALID original groups:** interior quote gaps bridge through the next genuine observed return. Each link reconciles to consecutive archived quotes, spans genuine endpoints and compounds to their ratio. Missing daily quotes do not inherently omit terminal buy-and-hold PnL. Phase1's strict daily-observation guard is too restrictive for this declared endpoint experiment; legacy behavior remains preserved.
- **70 INCOMPLETE_UNRECOVERABLE original groups:** BDTX/CRSP lack intended old endpoint quotes and historical groups were split onto earlier actual ends. No unavailable old endpoint or payout is invented.
- **Zero** VALID_TERMINAL_EVENT, RECOVERABLE_AUTHENTICATED, AMBIGUOUS_TIMING or SOURCE_EVIDENCE_BLOCKED classifications in this bounded endpoint accounting. Unexplained gap causes remain disclosed, not presumed corrupt or treated as terminal events.

Original raw files for all seven affected names—JKHY,PCAR,BIIB,BDTX,CRSP,GH,CHRW—also lack the target dates; no same-vintage recovery exists. [Biogen June2023](https://investors.biogen.com/node/26871) and [OCC November2020](https://infomemo.theocc.com/infomemos?number=47809) establish two genuine interior trading halts. Other causes are not guessed.

All new shifted intervals have genuine endpoints, including the265cases. This is a changed predeclared horizon, not recovery of old observations. **11352 new portfolio rows =3784 complete triples;101signal dates;41characteristics;123series;1,138,880member occurrences.** Zero formed groups fail the new endpoint policy; zero recovered/synthetic terminal groups. Original11545 becomes11352 through **70 split-end consolidations plus123 terminal partial-cycle exclusions**; minimum breadth causes no additional attrition. Nevertheless956singleton quantile observations remain; D3 statistical adequacy is open. Earliest valid exits per factor range2018-04-02–2021-02-01; all41are listed in independent-validation JSON.

Reconciliation has11422 matched comparison rows because70 new groups map to both historical split-end rows; this is not the new physical row count. Different-horizon mean signed difference is .001124462066, mean absolute .013298314803, maximum absolute .226379043257. Neither the execution shift nor exit shift can be attributed solely to a defect correction. No corrected old missing-endpoint value is claimed.

## Point-in-time, identity and provider vintage

`PHASE2B_SOURCE_CASE_EVIDENCE.json` traces AAPL at2023-11-30/2024-11-29 and AAP at2024-05-31 through raw SEC accession/acceptance, normalized book equity/net income, price×shares, raw ratio, frozen score, quantile/weight and subsequent execution/exit return. Apple accession `0000320193-23-000106` accepted2023-11-02T22:08:27Z after US close, filedNov3; normalized date-end availability is conservative for the later decision. Apple2024 `0000320193-24-000123` accepted2024-11-01T10:01:36Z. AAP amended10-K/A `0001158449-24-000128` accepted2024-05-30T01:01:16Z retains its own chronology, not fiscal-end availability. Share values match actual SEC facts in these cases. Every used score meets cutoff. All1,138,880formed intervals lie within dated listing mappings; none of15provider-documented reused tickers is retained.

These representative matches do not prove every share accession, cache capture chronology, restatement, issuer/share class or intraday timing. Cache hashes fixed now are not independent proof of historical capture. D4 remains SOURCE_EVIDENCE_BLOCKED; D5 remains qualified and open for reviewer acceptance. No intraday timestamp is fabricated. Historical universe-selection limitations also persist.

AAPL split-case frozen quotes123.59→127.68 (2020-08-28→31), return+.0330932923, are consistent with split continuity rather than an unadjusted75% fall; the [issuer announcement](https://www.apple.com/newsroom/2020/07/apple-reports-third-quarter-results/) establishes the event. Around the [August2024 dividend](https://www.apple.com/newsroom/2024/08/apple-reports-third-quarter-results/),214.514748→216.193926 alone cannot prove reinvestment. PiTrading/IEX transition163.22→156.163286 is recorded. Normalized overlapping AAPL prices equal frozen raw Close exactly. Raw OHLCV/source has no distribution ledger or complete adjustment factors.

The [provider errata](https://hfdatalibrary.com/pages/issues) describes mixed adjustment treatment in older files and an October2026 basis rebuild, plus shortened sessions/ticker-reuse risks. These facts do not authorize replacement of the old vintage. Exact complete dividend-total returns remain unestablished. Use **frozen provider-vintage adjusted-quote returns**, not independently validated total returns or execution fills. V1 stays source-blocked. No newer prices were downloaded.

## Immutable publications and five-model results

Factor `factor-4ddee9ac6fb45cedfd62a2cc68676b58` is preserved under `data/factors/factor-4ddee9ac6fb45cedfd62a2cc68676b58/` with authority `data/factor_manifests/factor-4ddee9ac6fb45cedfd62a2cc68676b58/`. It reuses34341456score rows byte-for-byte, SHA256 `ca2b67cb9f4586af19840c1f0e0540de5124b5ec040376e6db2a120a8862f60a`; this is authenticated reuse, not fresh exhaustive PIT verification. New portfolios/memberships/admissibility bind to method, composite config hash, source commit and original parents.

Primary matched pricing `asset-pricing-d60bee7310b34976c80372a0f0f29e21` and supplementary model-specific `asset-pricing-8c2396179c4b509796b2cab043ec31d2` are preserved under configured `data/asset_pricing/<id>/` and `data/asset_pricing_manifests/<id>/`. All manifests/content hashes are reproduced in the committed source manifest. Actual private Parquet/authority files remain local, excluded from Git. A fresh clone requires the authenticated archive and preserved private outputs. Optional bound supplementary evidence is enforced by both repository authenticators. Immutable output locations cannot be overwritten. Typed empty rolling artifacts explicitly mean no rolling estimates were computed in this bounded correction.

Primary:123assets/615fits,9441observations/model,N67–77, identical per-asset five-model dates with no month gaps; overall exits2020-04-01–2026-08-03. Alpha/SE are decimal returns per full monthly trading cycle, not annualized.

| Model | Assets | N | Mean adj.R² | Mean alpha | Mean abs.alpha | RMS alpha | Mean alpha SE | Nominal p<.05 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| capm | 123 | 67–77 | 0.760818 | -0.00165816 | 0.00218422 | 0.00270226 | 0.00314693 | 8/123 (6.50%) |
| fama_french_3 | 123 | 67–77 | 0.802438 | -0.00196725 | 0.00239349 | 0.00286833 | 0.00277895 | 12/123 (9.76%) |
| carhart_4 | 123 | 67–77 | 0.811021 | -0.00187946 | 0.00238247 | 0.00283528 | 0.00271976 | 14/123 (11.38%) |
| fama_french_5 | 123 | 67–77 | 0.817658 | -0.00200828 | 0.00240154 | 0.00281467 | 0.00280882 | 8/123 (6.50%) |
| hou_xue_zhang_q | 123 | 67–77 | 0.814361 | -0.00222658 | 0.00261656 | 0.00302639 | 0.00299608 | 9/123 (7.32%) |

Supplementary model-specific estimates are separate from the primary fair comparison:

| Model | Assets | N | Mean adj.R² | Mean alpha | Mean abs.alpha | RMS alpha | Mean alpha SE | Nominal p<.05 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| capm | 123 | 67–101 | 0.678143 | -0.00012129 | 0.00185312 | 0.00243522 | 0.00340451 | 3/123 (2.44%) |
| fama_french_3 | 123 | 67–89 | 0.737566 | -0.00140370 | 0.00232229 | 0.00292528 | 0.00302131 | 9/123 (7.32%) |
| carhart_4 | 123 | 67–89 | 0.747744 | -0.00140406 | 0.00229991 | 0.00291038 | 0.00298280 | 9/123 (7.32%) |
| fama_french_5 | 123 | 67–77 | 0.817658 | -0.00200828 | 0.00240154 | 0.00281467 | 0.00280882 | 8/123 (6.50%) |
| hou_xue_zhang_q | 123 | 67–89 | 0.761624 | -0.00152499 | 0.00246061 | 0.00298080 | 0.00307500 | 9/123 (7.32%) |

Historical/conditional/corrected families remain distinct. Cells below show mean adjustedR²/nominal significant intercepts, denominator123. First two families reuse validated Phase2 reference evidence.

| Model | Historical adj.R²/rejections | Phase2 conditional | New supplementary | New primary matched |
|---|---:|---:|---:|---:|
| capm | 0.063440/105 | 0.661500/1 | 0.678143/3 | 0.760818/8 |
| fama_french_3 | 0.258505/72 | 0.730559/9 | 0.737566/9 | 0.802438/12 |
| carhart_4 | 0.276585/65 | 0.747366/9 | 0.747744/9 | 0.811021/14 |
| fama_french_5 | 0.300791/114 | 0.812728/10 | 0.817658/8 | 0.817658/8 |
| hou_xue_zhang_q | 0.295732/72 | 0.759606/10 | 0.761624/9 | 0.814361/9 |

All signed/absolute/RMS alpha, samples, SE/t/p, dates and differences are in CSVs and actual publications. The prior compact conditional CSV lacks alpha-SE, so that summary field remains unavailable, not zero. New SE values are complete. Original CAPM/FF5 shares85.37%/92.68% become primary6.50%/6.50%; authentic supplementary2.44%/6.50% and Phase2conditional.81%/8.13% remain separately labeled. Fewer significant alphas do not prove better pricing.

## Inference, overlap and independent validation

OLS intercept/regressor order are preserved. For (execution,exit], market/cash gross returns compound separately; excess is terminal market minus terminal cash, never compounded daily excess. Dependent excess uses the identical cash interval. GenuineQ1/Q3 are required: the baseline accepted240synthetic rows substitutingQ2 for absentQ1; the correction rejects them. Genuine new outputs have all extreme legs, so this edge-case correction creates no separate empirical delta here.

BartlettHAC3,n/(n-k),two-sided Student-t p-values and95%CI remain unchanged. Lags0/3/6/12 independently agree. Primary rejections by those lags: CAPM7/8/10/15;FF3 9/12/18/21;Carhart10/14/20/21;FF5 6/8/16/22;q-style5/9/13/20. These are nominal dependent tests, not FDR-certified discoveries.

Overlap recomputed: mean constituent fractions shared withQ1/Q3factor legs SMB/ME.681716,HML.577757,MOM.574423,RMW.250764,CMA/IA.557992,ROE.571497; ranges0–1. Weight overlap is separate. Return-correlation mean.776274,median.792259,51/7503pairs>.95. Six exact pairs persist: market_cap/log_market_capQ1–3 and rolling_beta/rolling_market_betaQ1–3. Residual dependence is separately recorded. No percentage of artificially inflatedR² is inferred and123portfolios are not independent experiments.

Registry:48names,47with nonmissing raw values;equity_issuance absent.28550589nonmissing raw observations and24255559scores,41portfolio characteristics. Names are not independent signals. Historical q mapping remainsROE=earnings_yield,ME=SMB underlying log_market_cap,IA=CMA underlying asset_growth; study-specific q-style, not exactHXZ. AP10 originalH1/H3 approval/decision evidence remains absent.

Independent NumPy least-squares/Bartlett reference is in `scripts/research_phase2b.py::reference_fit`. Every11352published holding return is independently reconstructed as fixed weights×endpoint ratios, max error8.33e-17. Spread/market/cash/dependent-excess max errors0. All1230fits reproduce: coefficient2.34e-15,SE6.56e-15,p6.48e-14,residual1.00e-15,adjustedR²4.45e-16. Additionalt/CI/R²/RSE checks are exact at represented precision;AIC/BICmax1.71e-13. Tolerances1e-12returns and1e-8regressions; no mismatch suppressed. Summaries aggregate verified values; HAC sensitivity independently agrees.

37targeted tests pass. Full suite executed once: **358passed,115warnings,90.68%coverage,461.28seconds**. Warnings concern dependency deprecation, constant-correlation fixtures and small classification folds. Publication run also emitted a pandasPeriod metadata overflow warning; independently checked month ordinals/date hashes confirm zero gaps in all615primary fits, with numerical artifacts unaffected. Mypy115source files,Ruff lint/format156files,lock96packages and delivery config/platform checks pass. All76historical hashes, original authorities/parents, new publications and supplementary hashes revalidate. Exact log/commands are in `PHASE2B_TEST_RESULTS.txt`.

## Tracker and Phase3 gate

The same master tracker retains exactly50original IDs;16records (14focused plusAP4/AP10) are updated with prior/current status, sources/hashes, numerical effect, tests and paper consequence. D3/D4/D5/V1/AP10 remain open/qualified; warning text alone does not close their boxes. Other portfolio/ML issues are not declared solved.

Phase3 is **not safe for unqualified investment-performance or ML conclusions**. Independent review must accept the new publications and address or explicitly accept PIT/return-basis/breadth limits before downstream claims. Later authorized work can reuse qualified upstream evidence without implying total-return validation. No Phase3empirical computation, paper/README edit, PR merge or main change occurred. Both historical manuscript hashes and old empirical bytes remain preserved.

## Publication authority hashes

- `factor-4ddee9ac6fb45cedfd62a2cc68676b58` manifest content hash: `a96f20a0be44bb982a37b48a79bb8421d69269b3ec60058078a79d1d0a713a0b`; configuration hash: `de1bd2ba60ecd19e656228a1ce350b1cb163342eee582be62153d51ffb3424d8`.
- `asset-pricing-d60bee7310b34976c80372a0f0f29e21` manifest content hash: `02b18634e629360afdeafd25c65188549210647f214109629206eabda1b65fe5`; configuration hash: `734e675a123eddae5cc25ff3008e5b453f66f5696c42ea3af847bc3c4b321268`.
- `asset-pricing-8c2396179c4b509796b2cab043ec31d2` manifest content hash: `7d9f3a20c107f2fecdf59f71c2183c0a87ee3a3809a835c03e195a469f07f77b`; configuration hash: `734e675a123eddae5cc25ff3008e5b453f66f5696c42ea3af847bc3c4b321268`.
