# Phase 2C — Independent quantitative-finance verification

**Result: `PHASE2C_VERIFIED_WITH_ECONOMIC_LIMITATIONS`.** All 615 primary matched regressions and all 615 supplementary regressions independently reproduce. The high adjusted R² and negative mean intercepts are mathematically compatible and are correct for these authenticated frozen return objects, samples and specifications. No Phase 2B implementation defect was found; no published numerical change or new official publication is required. Economic validity is narrower than numerical reproducibility.

## Baseline, source authority and scope

Repository: [institutional-multi-factor-asset-pricing-platform](https://github.com/amitdudi04/institutional-multi-factor-asset-pricing-platform). Branch `research/institutional-phase2c-regression-verification`, created from exact Phase 2B SHA `94f347476c86962d2d7479a74b8fa915a5849668` with a clean worktree. Main remains `4e7fbdc380b8042db72e9c628260f60077a205ef`. Prior phase/older branch heads are unchanged. The commit containing this report is the final Phase 2C evidence commit; calculation source is `ac478bb59027e27212c7f5da28846dd1107434cb`. Policy/tolerances and the sole sensitivity were committed before results in `569779a`.

Reauthenticated publications:

- Factor `factor-4ddee9ac6fb45cedfd62a2cc68676b58`, manifest content hash `a96f20a0be44bb982a37b48a79bb8421d69269b3ec60058078a79d1d0a713a0b`.
- Primary `asset-pricing-d60bee7310b34976c80372a0f0f29e21`, hash `02b18634e629360afdeafd25c65188549210647f214109629206eabda1b65fe5`.
- Supplementary `asset-pricing-8c2396179c4b509796b2cab043ec31d2`, hash `7d9f3a20c107f2fecdf59f71c2183c0a87ee3a3809a835c03e195a469f07f77b`.

Both pricing manifests bind the new factor's exact authority. Its inherited score bytes and normalized parents match the authenticated original factor/pricing lineage; both parents reauthenticate as FINALIZED. All 76 historical source entries plus 16 additional source/case entries (including repeated case references) rehash unchanged. Full paths, hashes, configurations, source inventories and preserved authority records are in `PHASE2C_SOURCE_MANIFEST.json`. Actual matrices, residuals, coefficients, memberships and raw parent data were read, not inferred from aggregate CSVs. No prices were downloaded or vintage replaced. Original G: archive and private Phase 2B output locations are read-only inputs.

## Independent construction and numerical method

`scripts/research_phase2c.py` uses no production formation, pricing-input or regression-fitting helper. It independently rebuilds membership/rank order and positive normalized cap weights from the authenticated frozen scores, observed eligibility and price×shares; all **1,138,880** membership occurrences agree, weight error0. Genuine execution/exit quote ratios times fixed weights reproduce all **11,352** portfolio returns, max error8.33e-17. Unchanged Phase 2B quote-chain evidence is reused after reauthentication rather than rerunning that earlier investigation.

Every characteristic explanatory leg is rebuilt from those returns as genuine Q3 minus Q1, retaining historical score directions and alias definitions. Market and cash are independently compounded separately over exactly `(execution,exit]`; dependent excess is portfolio return minus that same terminal cash return. Market/cash errors0; maximum matrix difference8.33e-17. Complete-case intersections are independently reconstructed before fitting and match the full authenticated primary matrix.

Each regression uses pivoted Householder QR and triangular solves, distinct from production statsmodels OLS and the previous NumPy least-squares verifier. X includes the intercept; k counts all estimated coefficients. SSE=Σe², SST=Σ(y−mean(y))², R²=1−SSE/SST and adjusted R²=1−[SSE/(n−k)]/[SST/(n−1)]. Every design is full rank. Fitted values, residuals, residual means, scaled normal equations and `alpha=mean(y)−beta' mean(factors)` are checked.

The reference independently accumulates every score outer product and Bartlett lagged cross-product. HAC covariance is `n/(n−k) * bread * meat * bread`, with bread obtained through QR triangular solves. Lag3, two-sided Student-t(n−k) p-values and 95% intervals reproduce the bound specification. These are correctly calculated nominal HAC conventions, not exact finite-sample guarantees. [Newey and West's original method](https://www.nber.org/papers/t0055) supplies the covariance-estimator context.

Tolerances: return/matrix absolute1e-12, regression absolute1e-8, scaled normal equations1e-10. Actual maxima: coefficient6.60e-15; fitted/residual6.65e-15; SE1.27e-14; p1.64e-12; t4.87e-12; CI2.54e-14; R²3.34e-16; adjusted R²4.45e-16. HAC sensitivity maximum2.81e-12. Model-summary discrepancies are below4e-15; separate NumPy checks of all20 model-family summary rows agree within9.89e-17. No failed comparison was suppressed. Scaled normal equations are below3.30e-16, residual means below1.97e-17, and alpha mean-identity errors below2.37e-17 across official and diagnostic fits. Per-case differences are recorded, not rounded to zero.

## Primary alpha distribution and significance

All primary models have123 assets, 9,441 observations per model and67–77 observations per asset. Summaries are equal-weight arithmetic means across the123 portfolio fits, not pooled regressions or weights by sample size. Distribution SD uses ddof=1; quartiles use linear interpolation. Alpha/SE units are **decimal returns per monthly trading cycle**. Mean alphas correspond to approximately−16.58,−19.67,−18.79,−20.08 and−22.27basis points per cycle; they are not annualized or compounded investment returns.

| Model | Mean α | Median | Min | Max | SD | Mean abs. α | RMS α |
|---|---|---|---|---|---|---|---|
| CAPM | -0.00165816 | -0.00171445 | -0.00573934 | 0.00777728 | 0.00214243 | 0.00218422 | 0.00270226 |
| FF3 | -0.00196725 | -0.00207082 | -0.00674843 | 0.00603446 | 0.00209593 | 0.00239349 | 0.00286833 |
| Carhart 4 | -0.00187946 | -0.00197849 | -0.00652072 | 0.00706662 | 0.00213152 | 0.00238247 | 0.00283528 |
| FF5 | -0.00200828 | -0.00212325 | -0.00641299 | 0.00686241 | 0.00198017 | 0.00240154 | 0.00281467 |
| q-style | -0.00222658 | -0.00243746 | -0.00723375 | 0.00509097 | 0.00205810 | 0.00261656 | 0.00302639 |

| Model | Positive | Negative | Sig.positive | Sig.negative | Not significant | 95%CI includes0 |
|---|---|---|---|---|---|---|
| CAPM | 24 | 99 | 0 | 8 | 115 | 115 |
| FF3 | 20 | 103 | 0 | 12 | 111 | 111 |
| Carhart 4 | 21 | 102 | 0 | 14 | 109 | 109 |
| FF5 | 15 | 108 | 0 | 8 | 115 | 115 |
| q-style | 16 | 107 | 0 | 9 | 114 | 114 |

There are zero exactly zero point estimates. The confidence intervals and nominal rejection counts agree. Negative point estimates are much more numerous than statistically significant negative estimates. No significant positive intercept appears. A negative arithmetic mean of dependent estimates is not itself a test of a negative population mean; no iid-123 standard error or mean-alpha significance is claimed. Nonsignificance does not establish exactly zero alpha.

| Model | Mean SE(α) | Median SE(α) | df range |
|---|---|---|---|
| CAPM | 0.00314693 | 0.00292504 | 65–75 |
| FF3 | 0.00277895 | 0.00259087 | 63–73 |
| Carhart 4 | 0.00271976 | 0.00255934 | 62–72 |
| FF5 | 0.00280882 | 0.00262499 | 61–71 |
| q-style | 0.00299608 | 0.00277448 | 62–72 |

The actual sample-mean identity explains the signs without an error:

| Model | Mean dependent excess | Mean β×factor contribution | Mean intercept |
|---|---|---|---|
| CAPM | 0.00900576 | 0.01066393 | -0.00165816 |
| FF3 | 0.00900576 | 0.01097302 | -0.00196725 |
| Carhart 4 | 0.00900576 | 0.01088522 | -0.00187946 |
| FF5 | 0.00900576 | 0.01101404 | -0.00200828 |
| q-style | 0.00900576 | 0.01123234 | -0.00222658 |

Mean dependent excess is positive, but mean fitted factor-exposure contribution is larger. Centered fit measures variation about the mean; intercept sign measures this different mean-return discrepancy. High R² places no positivity restriction on alpha.

## Adjusted R² distribution, model differences and conditioning

| Model | Mean adj.R² | Median | Min | Max | IQR | SD | Negative | Mean R²−adj.R² |
|---|---|---|---|---|---|---|---|---|
| CAPM | 0.760818 | 0.787564 | 0.098605 | 0.939118 | 0.113932 | 0.124351 | 0 | 0.003183 |
| FF3 | 0.802438 | 0.822721 | 0.092871 | 0.974767 | 0.093869 | 0.116048 | 0 | 0.007898 |
| Carhart 4 | 0.811021 | 0.830492 | 0.131160 | 0.974438 | 0.096790 | 0.113697 | 0 | 0.010075 |
| FF5 | 0.817658 | 0.835738 | 0.107751 | 0.974364 | 0.090225 | 0.110549 | 0 | 0.012160 |
| q-style | 0.814361 | 0.828120 | 0.124938 | 0.975233 | 0.085884 | 0.110922 | 0 | 0.009908 |

The .76–.82 values are means, not uniformly high fits: individual minima are approximately.09–.13. Adjusted R² penalizes added parameters and can fall for individual assets even when an added-factor model is nested. All ten matched-portfolio comparisons are preserved; the direction below is second model minus first on identical per-asset dates.

| Second−first model | Mean Δadj.R² | Median | Min | Max |
|---|---|---|---|---|
| Carhart 4−CAPM | 0.050203 | 0.023977 | -0.009903 | 0.295452 |
| FF3−CAPM | 0.041620 | 0.015541 | -0.011358 | 0.297409 |
| FF5−CAPM | 0.056840 | 0.031054 | -0.011402 | 0.295350 |
| q-style−CAPM | 0.053543 | 0.032444 | -0.007459 | 0.256127 |
| FF5−Carhart 4 | 0.006637 | 0.001774 | -0.156717 | 0.262407 |
| q-style−Carhart 4 | 0.003340 | 0.000795 | -0.159457 | 0.118868 |
| Carhart 4−FF3 | 0.008583 | 0.000543 | -0.009577 | 0.161885 |
| FF5−FF3 | 0.015220 | 0.004803 | -0.012780 | 0.289070 |
| q-style−FF3 | 0.011923 | 0.003891 | -0.089734 | 0.115657 |
| q-style−FF5 | -0.003298 | -0.002351 | -0.192580 | 0.092972 |

| Model | Raw cond.max | Standardized cond.max | VIF max | Full-rank fits |
|---|---|---|---|---|
| CAPM | 24.4652 | 1.0000 | 1.0000 | 123 |
| FF3 | 53.2254 | 2.9203 | 2.6373 | 123 |
| Carhart 4 | 53.6729 | 3.2958 | 2.6921 | 123 |
| FF5 | 60.1698 | 3.3907 | 3.1047 | 123 |
| q-style | 47.2101 | 2.1872 | 1.7190 | 123 |

Condition numbers are 2-norm values; standardized versions center and scale each nonconstant regressor within its actual sample, retaining an intercept. The prespecified standardized flag30 is never exceeded. Maximum within-model regressor correlation is .693212 (q-style .486596). Numerical instability, rank failure or severe regressor redundancy does not explain these results. SMB=ME and CMA=IA are exact aliases **across** model families; neither duplicate pair is simultaneously entered into one fitted model. High correlation and numerical collinearity are distinct from dependent/test-portfolio overlap.

Sample choice matters: supplementary CAPM has mean adjusted R².678143 and mean alpha−.00012129, whereas matched primary CAPM has.760818 and−.00165816. Model-specific samples are supplementary, not a fair same-calendar model ranking. This demonstrates sample dependence; it is not a causal decomposition or evidence of result-driven sample tuning. The primary rule was frozen before Phase 2B performance.

## Dependence and the one predetermined sensitivity

All123 test portfolios and every relevant factor leg were inspected. Six exact repeated-return pairs persist: log_market_cap/market_cap Q1–3, rolling_beta/rolling_market_beta Q1–3. Return correlation mean.776274, median.792259, with51/7503 pairs above.95. Shared constituent fractions and dependent-weight fractions are recorded per asset/alias in the dependence CSV, including complete self-inclusion in corresponding original factor legs. No overlap statistic is described as a percentage of mechanically generated R².

| Model | Mean residual correlation | Median | Pairs>.95 |
|---|---|---|---|
| CAPM | 0.293014 | 0.302328 | 18 |
| FF3 | 0.303718 | 0.326725 | 25 |
| Carhart 4 | 0.321449 | 0.346231 | 27 |
| FF5 | 0.332289 | 0.349834 | 26 |
| q-style | 0.329434 | 0.336210 | 24 |

For every model, the all-asset common residual matrix has67 dates,123 columns and centered rank66: sample covariance is singular. A naive inverse-covariance joint-alpha test would be unsupported. No such test, GRS claim or independent-123-trial inference is manufactured.

The frozen sensitivity `dependent-constituent-excluded-legs-v1` removes **every** dependent-portfolio constituent from each characteristic factor leg at the original signal date, renormalizes the remaining original positive cap weights within that leg and never reranks. No future performance criterion selects membership. Empty legs stay unavailable; no zero/cash/fallback is inserted. The SPY market proxy remains unchanged because its constituent exclusions cannot be authenticated here. All five diagnostic models and the unchanged baseline use identical retained dates/assets, minimum24 and full rank.

**109 assets** remain (67–77 dates);14 have empty required legs on every primary date: Q1/Q3 of asset_growth, book_to_market, earnings_yield, gross_profitability, log_market_cap, momentum_12_1m, plus duplicate market_cap Q1/Q3. These exclusions are explicitly reported. Among the109 retained assets,57 lose some original dates:163 asset-cycle observations per model are excluded, reducing8363 to8200 on this asset subset;52 assets lose no dates. Forty-four retained assets have internal month gaps (up to3 gap jumps), and the maximum loss is9 cycles for an asset. Both diagnostic and refitted baseline use exactly the same retained dates. HAC lag3 in this diagnostic counts retained observations rather than necessarily3 calendar months; this is an additional inferential qualification, not a new official result. CAPM is unchanged on the matched sensitivity sample because its market regressor was not changed.

| Model | Matched baseline adj.R² | Excluded-constituent adj.R² | Δadj.R² | Baseline α | Diagnostic α |
|---|---|---|---|---|---|
| CAPM | 0.746522 | 0.746522 | 0.000000 | -0.00137048 | -0.00137048 |
| FF3 | 0.784963 | 0.782692 | -0.002271 | -0.00173965 | -0.00146281 |
| Carhart 4 | 0.792998 | 0.784799 | -0.008199 | -0.00166372 | -0.00136253 |
| FF5 | 0.797998 | 0.790472 | -0.007527 | -0.00176722 | -0.00171062 |
| q-style | 0.798270 | 0.790752 | -0.007519 | -0.00194833 | -0.00189749 |

High fit persists for those109 assets and average changes in richer-model fit are modest. This cannot be generalized to the14 most directly self-included assets that become unestimable, nor translated into an overlap-generated R² percentage. Remaining security overlap between different test assets, common universe selection and SPY exposure survive. This diagnostic reduces direct characteristic-leg self-inclusion; it is **not** an independent external-factor validation or a replacement publication.

## HAC lag and multiplicity checks

All counts use the original .05 threshold. The lag sensitivity was prespecified, not optimized:

| Model | Lag0 | Lag3 | Lag6 | Lag12 | Holm within123 | Holm across615 |
|---|---|---|---|---|---|---|
| CAPM | 7 | 8 | 10 | 15 | 0 | 0 |
| FF3 | 9 | 12 | 18 | 21 | 0 | 0 |
| Carhart 4 | 10 | 14 | 20 | 21 | 0 | 0 |
| FF5 | 6 | 8 | 16 | 22 | 0 | 0 |
| q-style | 5 | 9 | 13 | 20 | 0 | 0 |

Holm adjustments are supplementary within each model's123 intercepts and across all615 primary intercepts. They control familywise error under arbitrary dependence **conditional on valid marginal p-values**; they do not repair approximate small-sample HAC inference, generated regressors or source errors. None survives either adjustment. This is not FDR certification and does not prove zero pricing errors. Method reference: [Holm (1979)](https://doi.org/10.2307/4615733).

## Ten-question referee assessment for each model

For **each** of CAPM, FF3, Carhart4, FF5 and q-style:

1. Adjusted R²: verified against every actual fit, with distributions above.
2. Mean alpha: verified from actual intercepts; negative means are retained.
3. SE, p-values and intervals: verified for the declared HAC/t convention; finite-sample inferential validity remains conditional.
4. Periods: valid matched modeled intervals, with source/PIT qualifications below.
5. Numerical stability: full rank and stable to declared tolerances; conditioning table gives individual model maxima.
6. Sufficient independence: **no** for interpretation as independent factor/test-asset evidence.
7. Negative alpha without implementation error: **yes**, the verified mean identity above explains it.
8. Demonstration: within-sample linear association of these frozen adjusted-quote portfolio returns with the specified proxy/spread returns, plus descriptive nominal pricing-error estimates.
9. Not established: an exactly zero alpha model, causal factor premiums, independent cross-sectional pricing success, out-of-sample predictability, investable net performance or genuine dividend-total-return/PIT certification.
10. Paper readiness: numerical tables are ready for a **qualified descriptive revision**, not unqualified asset-pricing or investment-performance claims. No paper edit is made here.

Model-specific economic qualifications:

- **CAPM:** the market factor is inherited SPY, not an independently reconstructed US equity market. Market exposure alone explains much of the high variation fit; its intercept still measures a nonzero sample-mean discrepancy.
- **FF3:** internally formed size/book spreads improve average fit by .041620 versus CAPM on common samples, with individual gains and losses. This does not validate official Fama–French pricing factors or independent test assets.
- **Carhart4:** adding the internal momentum spread improves average adjusted fit by .008583 versus FF3, but the individual differences vary. Shared formation data and exposures remain.
- **FF5:** the highest primary mean fit among these five is descriptive, not proof of superior economic pricing. Negative mean alpha and eight nominal negative intercepts remain; factor/asset dependence persists.
- **q-style:** historical ROE=earnings_yield, ME=log_market_cap and IA=asset_growth mappings remain unchanged. This is a study-specific q-style proxy, not exact HXZ profitability replication, despite correct arithmetic and stable design.

## Timing, source limits and validation gate

Every signal is a genuine XNYS month end; modeled execution is its next session close and exit is the following monthly execution close. All2128 observed market/cash sessions match the XNYS calendar. Return windows exclude execution-date returns and match dependent, explanatory and cash endpoints. All used formation score timestamps meet the declared UTC-day cutoff and dated listing bounds. Frozen raw-score preprocessing is authenticated reuse, not a fresh reconstruction of every SEC field's historical capture. Full strict PIT, share-class/capture chronology, historical universe selection, early single-name groups and provider adjustment-vintage risks remain. The return object remains **frozen provider-vintage adjusted-quote returns**, not certified complete total returns or executable closing fills.

The19-session and23-session cycles are **not identical elapsed trading horizons**. They are distinct full monthly trading cycles, treated as one observation each by the retained monthly specification; there is no duration normalization or guaranteed compounding interpretation. The unobserved terminal full cycle is excluded, and neither official publication has duplicate dates or gaps in retained monthly cycles; diagnostic gaps are explicitly disclosed above. Source authenticity establishes recorded bytes, not all underlying vendor/economic assertions.

Targeted mathematical/regression tests:45 passed. Full suite executed once:366 passed,115 warnings,90.68% branch-aware coverage,460.04seconds. Existing warnings concern dependency deprecation, constant-correlation fixtures and small classification folds. Type checks115 source files, Ruff lint/format159 files and dependency lock96 packages pass. Final hash reauthentication covers original and all three Phase 2B publications, parents and bound supplementary evidence. See exact commands/log in `PHASE2C_TEST_RESULTS.txt`.

One audit-helper display issue was corrected: uncomputed supplementary/diagnostic Holm counts initially appeared as zero; they are now unavailable. A targeted summary check confirms this, and the primary verified zero counts are unchanged. Joint-covariance support, aggregate conditioning and sensitivity-attrition metadata were added after the main verification run. A check of the initial no-attrition diagnostic assumption failed; the observed date losses and gaps are now explicitly recorded. This did not affect the already matched diagnostic/baseline calculations or any primary result. No Phase 2B function, value, configuration or publication changed; no new official publication IDs exist. Original manuscripts, README, main, previous branches and all frozen inputs/results remain unchanged.

The same50-ID tracker is updated only for new AP3/AP5/AP6/AP7/AP8/AP9 interpretations, without changing their prior statuses or checkboxes. D3/D4/D5/V1 and AP10 limitations remain open/qualified. **Stop after Phase 2C.** Phase3 and manuscript rewriting are not started.

New audit-file integrity: Git Windows automatic line-ending conversion would have changed staged evidence byte hashes. Narrow Phase2C-only `.gitattributes` rules preserve the exact new evidence bytes and LF verifier sources; staged Git blobs are checked against the recorded hashes. No historical file is normalized or rewritten. The prior Phase2B source-document captured-worktree and canonical Git-blob hashes are both recorded to distinguish line-ending representation from publication content authority.
