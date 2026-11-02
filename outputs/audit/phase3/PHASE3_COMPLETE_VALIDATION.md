# Phase3 complete portfolio and machine-learning validation

**Status: `PHASE3_VERIFIED_WITH_LIMITATIONS`.** All22target issues were investigated:7 VERIFIED_CORRECT,4 CONFIRMED_ERROR_FIXED issues covering5distinct implementation defects,8 RESEARCH_LIMITATION_DISCLOSED and3 SOURCE_EVIDENCE_BLOCKED. These are verified,qualified research calculations and simulation records, not proof of live investability or complete historical point-in-time availability.

## Baseline and source authority

Branch `research/institutional-phase3-validation` starts from exact accepted Phase2C SHA `277c95bd4ba7279e6863bc3acc026d406a8ad482`. Main remains `4e7fbdc380b8042db72e9c628260f60077a205ef`. The commit containing this report is the final Phase3 evidence commit, avoiding a self-referential hash. Portfolio/ML fitting source is `0fe382f`; constant-forecast metric-only source is `9df5455`. Previous phase/older branches and original data,publications,release tags,papers and README remain unchanged. The G: archive's pre-existing API/frontend changes were untouched; audit code ran from this checkout.

The one-pass gate authenticated25historical portfolio publications (8methods×LOW/BASE/HIGH plus a duplicate BASE-EW contextual publication),8final monthly-design ML publications,and540distinct artifacts. Sixteen earlier daily-design ML manifests were inventoried and excluded from the paper's17-fold design. Both original/corrected factor and pricing authorities, including the three required accepted corrected IDs, connect to finalized normalized market/fundamental parents. Five cached canonical upstream authorities match accepted Git-tracked hashes. Source paths,sizes,schemas,row counts,configuration hashes,IDs,parents and artifact checksums are in `PHASE3_SOURCE_MANIFEST.json`.

Large files were authenticated once; final unchanged-size/mtime guards reuse that cache. New publication authorities are separately authenticated. No accepted1230asset-pricing regressions,11352factor-return reconciliation or full SEC pipeline was repeated. No replacement market data was downloaded. Existing raw/frozen inputs remain private and immutable.

## Demonstrated defects and minimal corrections

Five financial/ML failures were demonstrated before correction:

1. **Cash horizon:** `portfolio/service.py::_risk_free_series` supplied a single daily cash return to monthly performance. It now compounds cash over each exact authenticated (formation,exit] interval. Fees,objectives and constraints were not changed.
2. **Monthly sampling:** `ml/features.py::monthly_decision_features` used each security's last available observation, creating two extra earlier dates (BDTX2023-04-27 and CRSP2023-10-30). These were counted as separate periods. It now requires a common month end and omits a security lacking that date.
3. **Target horizon:** `ml/targets.py::build_targets` counted21available security observations, extending incomplete windows beyond21common sessions. Eight archived label ends violated the declared horizon. Two earlier-date feature rows and six incomplete common-calendar labels are excluded; nothing is recovered,filled,extended or made cash.
4. **IC estimand:** `ml/evaluation.py::block_bootstrap_ic` pooled cross-date ranks and reported a mean bootstrap estimate while the stated object was mean per-date/fold IC. It now bootstraps date IC and reports the actual observed mean, retaining block3,100replicates and seed17.
5. **Undefined correlation:** `_correlation` tested computed standard deviation==0, which can miss an exactly constant nonzero floating array. It now checks zero range and rejects nonfinite correlations. Undefined IC stays unavailable rather than zero or NaN.

Initial focused tests yielded4failed/1passed. A later authentic-output check exposed the constant-forecast failure (1failed/5passed); all6new regression cases now pass. No financial hyperparameter,model family,feature definition,confidence threshold or investment objective was changed to improve results.

### Actual dependency tracing

The portfolio optimizer consumes quantile returns from the old factor publication, not pricing coefficients. Its training/holding population contains the earlier incomplete-endpoint construction and terminal partial cycle. This demonstrated dependency requires propagation from the accepted corrected factor publication. The correction preserves all8methods,123sleeves,36-cycle trailing window,Ledoit-Wolf covariance,long-only fully-invested mandate and5/10/20bps assumptions.

BASE optimization was performed once per method. LOW/HIGH use the identical BASE weight path only after confirming that no fee-dependent objective/constraint is active and drift is gross-return based. Actual scenario-weight invariance and monotonic fee outcomes are verified, avoiding three redundant optimizer runs.

ML consumes unchanged raw book-to-market and12-1momentum scores,normalized market returns for targets,and the original EW parent **only for its fee configuration**. It does not consume the faulty quantile-return table or asset-pricing coefficients. Its raw-score/market/cost-context parent identities are therefore retained rather than automatically substituted. Byte-identical score values are reused; no factor/SEC system is rebuilt.

The confirmed calendar/label defects invalidate the fitting population, so the existing8families were retrained under unchanged grids,seeds,thread limits and procedures. The subsequent constant-IC correction republishes metrics with identical fitted-model and prediction bytes, without refitting. Superseded intermediate records are preserved and distinguished from final publications.

## Portfolio reconciliation

All returns use frozen provider-vintage adjusted quotes, net of the specified modeled fees where applicable. Complete dividend-total-return treatment is not independently established.

Every original/corrected trade,drifted pretrade weight,target allocation,L1,commission,half-spread,slippage and modeled NAV deduction reconciles independently. Trade=w_target−w_pretrade; cost=Σ|trade|×(commission+half-spread+slippage rates), nonlinear impact0. Net return=gross−cost; NAV_next=NAV_prev×(1+gross)−NAV_prev×cost. This preserves the existing modeled end-of-period cost convention rather than silently switching cash timing.

Initial deployment hasL1=1 and fees.0005/.001/.002 forLOW/BASE/HIGH. A full invested switch hasL1=2, so BASE costs20bps with a10bps per-traded-side rate; that is not an inconsistency. LOW uses quoted spread4bps (half-charge2)+slippage3; BASE quoted10 (half5)+slippage5; HIGH quoted20 (half10)+slippage10. BASE slippage5 bundles2slippage+3fixed allowance. Half-L1 is self-financing one-way rebalance turnover, not initial deployment notional. No fee was arbitrarily halved.

All8methods share the same123asset IDs and32original or31corrected evaluated cycles. All long-only/fully-invested constraints,positive covariance estimates,expected-return/volatility records and objective identities reconcile. CVaR objectives agree with36past scenarios. No future return row is included in history. Global optimality is not independently asserted for every nonconvex solver. Maximum-Sharpe's existing default optimizationRF0 is distinct from performance's now-correct compounded cash convention.

| Method | Cumulative net old→new | Volatility old→new | Sharpe old→new | MDD old→new |
|---|---|---|---|---|
| equal_weight | 48.8933% → 46.3133% | 11.1409% → 10.7432% | 1.383444 → 1.023067 | -8.5667% → -8.2915% |
| minimum_variance | 41.6442% → 45.0930% | 10.0003% → 9.9505% | 1.341007 → 1.065607 | -6.6935% → -6.4993% |
| mean_variance | 37.6026% → 29.2761% | 16.0427% → 14.6465% | 0.817996 → 0.455591 | -17.8068% → -16.1138% |
| maximum_sharpe | 64.6091% → 66.5591% | 12.2966% → 12.0472% | 1.574543 → 1.346360 | -7.5093% → -6.1601% |
| maximum_diversification | 53.0784% → 58.9082% | 10.9726% → 10.6378% | 1.498689 → 1.334355 | -5.4323% → -4.8279% |
| risk_parity | 47.7242% → 45.4247% | 10.7921% → 10.4332% | 1.397148 → 1.027799 | -8.3301% → -7.9894% |
| hrp | 46.7927% → 43.8413% | 10.5590% → 10.1920% | 1.403084 → 1.008019 | -8.1335% → -7.7200% |
| cvar | 83.1737% → 73.6842% | 14.2090% → 14.4950% | 1.666657 → 1.252327 | -8.5489% → -7.0821% |

The CSV includes annualized geometric returns under12cycles/year,wealth,fee sums/wealth effects and all24scenario results. Changes combine corrected holding inputs,optimization histories,delayed interval convention,terminal-cycle exclusion and cash repair; they are **not an initial-NAV-only experiment**.

**P1:** the original maximum-diversification MDD−5.432343856% is correct on its actual archived path. Including initialNAV1 changes none of the8historical maximum drawdowns, although the general Phase1 formula correction remains necessary. New MDD−4.827860559% belongs to the changed corrected path; the old−5.43%was not disproved.

**P6:** original CVaR83.173655874%/Sharpe1.666656947 reproduces. On the same old path,cash repair alone gives Sharpe1.378572122. After input propagation the result is73.684195642%/1.252326967. A loss-minimizing strategy can have high realized return without a return-maximizing objective or future leakage; observed ranking is not persistence evidence.

VaR95/ES95 are positive-loss,unannualized monthly-cycle quantities. The historical estimator uses the interpolated5%quantile and inclusive below-threshold mean; only two realized observations enter each31/32-cycle tail estimate. This differs from the fractional36-scenario tail used by the CVaR training LP. No claim of precise tail calibration follows.

The single predeclared paired CVaR−EW mean net-cycle difference is.00689120060 originally,with leave-one-out means.00508077666–.00980775974; corrected.00598371896,range.00408710902–.00875998275. These are descriptive sensitivities,not confidence intervals or superiority tests. No large bootstrap grid or sample extension was added.

Investments here are constructed long-only quantile sleeves,not directly executed equities or long-short spreads. Shared constituents and omitted inner-sleeve execution,liquidity and capacity costs limit investability. Equal weight and optimized methods have identical outer accounting; external SPY remains an uncosted proxy. Flat impact allowance is not measured order-book impact.

## ML calendar,purging and features

The original27640rows contain91distinct dates but **89calendar months**. Two earlier security dates made the original first training slice60date labels but only58months. Corrected sampling/targets yield **27632rows,89common monthly dates,15complete folds**. No historical observation was invented to retain17folds.

The corrected first fold has60calendar-month training2019-02-28–2024-01-31,one unused monthly date,12-month validation2024-03-28–2025-02-28,one unused monthly date,and test2025-04-30. Monthly tests continue through2026-06-30. Walk-forward training expands from60to74months; it is not always a fixed60-month rolling window. Original17folds/8253test observations remain archived; corrected15folds contain7286test observations/model.

All original17and corrected15partition checks pass: retained training labels mature before validation formation,and validation labels before test formation. The existing one-month embargo is preserved on both boundaries. Every retained corrected target uses21complete common sessions. Adjacent OOS target windows overlap6/16original and5/14corrected pairs,so fold independence is not established by purging alone.

Only the two original features and reject-missing/training-only standardization are used. Raw values match the frozen source. Final saved scaler means/std match permitted training rows. Independent baseline,OLS and Ridge equations reproduce every original/corrected fold forecast and linear coefficient to within3.13e-17; selected parameters are recovered from authenticated trial/model identities. Every final saved model,including RF/XGBoost,reproduces its last-fold predictions. Earlier fitted tree states are not independently retained; authenticated earlier predictions and controlled retraining are not misrepresented as independent reloads of every old tree.

UTC-day feature availability passes,but complete actual filing/share capture and pre-execution intraday timing remain D4/V1-qualified. Forecast files are retrospective research outputs,not proof of historical live forecasts. Latest training marks can coincide with holding starts,allocation rows label exits,and a UTC-day-end cutoff does not prove pre-close execution. **P8,ML4 andML5 remain source-blocked.** No fictitious timestamp or new execution-lag parameter was added to hide this limitation.

## ML prediction,uncertainty and economic results

| Model | Mean IC old→new | Old IC on new matched sample | Corrected IC interval | Mean one-session net old→new | Positive new folds |
|---|---|---|---|---|---|
| zero | unavailable → unavailable | unavailable | unavailable | -0.14148% → -0.06043% | 7/15 |
| historical_mean | unavailable → unavailable | unavailable | unavailable | -0.14148% → -0.06043% | 7/15 |
| factor_composite | 0.017412 → 0.034430 | 0.037238 | [0.010731,0.084270] | -0.09729% → 0.05591% | 7/15 |
| linear | 0.017412 → 0.034430 | 0.037238 | [0.010731,0.084270] | -0.09729% → 0.05591% | 7/15 |
| ridge | 0.017414 → 0.034434 | 0.037239 | [0.010735,0.084272] | -0.09729% → 0.05591% | 7/15 |
| elastic_net | 0.027535 → 0.044609 | 0.048753 | [0.016324,0.096766] | -0.10394% → 0.05509% | 7/15 |
| random_forest | 0.009558 → -0.002641 | 0.008806 | [-0.017721,0.015985] | 0.00743% → 0.14095% | 8/15 |
| xgboost | -0.009069 → -0.023285 | -0.010175 | [-0.038821,-0.005015] | -0.00441% → 0.15537% | 10/15 |

Mean/median IC,forecast metrics,uncertainty bounds and cost effects are in the reconciliation CSV. Constant forecasts have undefined IC. Corrected intervals target mean date IC using the original block3/100replicates/seed17. Four configured labels have nominal positive intervals excluding zero (two are exactly the same estimator),and XGBoost has a negative interval excluding zero; RF's includes zero. The old statement that every interval includes zero cannot be carried forward unchanged. Fifteen dependent folds,overlapping labels,small resampling budget and multiple model comparisons do not justify robust discovery or guaranteed coverage.

The linear meanIC increase.017412→.034430 is not an improvement in skill attributable to correction. On the **same corrected security/date sample**,the old linear predictions have meanIC.037238 versus corrected.034430. Equivalent controls for every model are in the CSV. Changed valid folds remove two old test dates; test-window and training-population effects must not be marketed as superior forecasting.

The factor-composite and linear branches both instantiate LinearRegression. All17original+15corrected fold vectors/rankings are exactly identical; this is intentional aliasing,not accidental file reuse. Ridge retains its.1/1/10grid and final selected alpha.1,weak relative to its standardized training Gram matrix. Its actual maximum forecast difference from linear is7.66e-6,with some changed rankings. No penalty was increased to manufacture a difference.

The economic routine uses20%equal-weight selected equities,unit capital,cash reset and10bps initialL1 fee for every model. It evaluates **one subsequent common session**,not the21-session target. No exit liquidation charge or continuous capital chain is modeled. Constant-forecast ties select an arbitrary deterministic security-ID subset,not cash or a new all-universe benchmark. Selection,returns and modeled costs reconcile independently for every fold.

Positive mean one-session outcomes—even XGBoost's despite negative21-sessionIC—do not establish continuous,stable incremental after-cost value. The prior conclusion that stable incremental economic value is unestablished is retained. These are isolated research checks,not a21-session trading backtest.

Permutation importance measures validation prediction-loss degradation; SHAP explains test predictions against historical training background. Highest-feature disagreements are RF7/17→7/15 andXGBoost10/17→6/15; training feature correlation is about−.1875. Different estimands/samples,moderate feature dependence and small samples do not imply a calculation error or identify a causal explanation. No new attribution algorithm was added. Existing per-fold IDs/outputs are retained; final model-file checksum binding does not supply every earlier fitted tree state.

## All22target issue outcomes

| ID | Final status | Finding |
|---|---|---|
| P1 | VERIFIED_CORRECT | All8actual BASE paths reconcile from NAV1; initial-NAV effect0 for all historical minima. Original maximum-diversification MDD-.05432343856 is correct on its historical path. |
| P2 | VERIFIED_CORRECT | Actual old/new trade,fee,drift and NAV identities reconcile for all5/10/20bps scenarios. InitialL1=1,BASEfee=.001; full switchL1=2 costs20bps. |
| P3 | VERIFIED_CORRECT | Eight methods share123sleeves,36-cycle history and identical32original/31corrected test cycles; objectives legitimately differ. |
| P4 | RESEARCH_LIMITATION_DISCLOSED | Optimizer invests in123constructed long-only quantiles, not direct487equities or long-short spreads. |
| P5 | VERIFIED_CORRECT | EW and optimized methods start from cash/NAV1, charge initial deployment and use identical drift/fees. All16old/new method scenario comparisons have identical weights and monotonic fee effects. |
| P6 | RESEARCH_LIMITATION_DISCLOSED | Original CVaR.83173655874/Sharpe1.666656947 reproduces; cash-only repair on old path1.378572122; corrected inputs.73684195642/1.252326967. Scenario objectives and feasible weights reconcile. |
| P7 | RESEARCH_LIMITATION_DISCLOSED | Original32cycles become31full corrected cycles after terminal partial exclusion. |
| P8 | SOURCE_EVIDENCE_BLOCKED | Every optimizer uses36observations before evaluated return; training_end<=holding_start and no future array row. |
| P9 | VERIFIED_CORRECT | Feasible long-only fully-invested weights,positive Ledoit-Wolf covariances and all expected-return/volatility/objective identities reconcile. |
| P10 | RESEARCH_LIMITATION_DISCLOSED | BASE half-spread5bps plus modeled5bps slippage(2slippage+3fixed allowance),commission0,nonlinear impact0. |
| P11 | CONFIRMED_ERROR_FIXED | Confirmed daily-cash/monthly-return mismatch fixed by exact interval compounding. Independent Sharpe,volatility,NAV,VaR95/ES95 reconcile. |
| P12 | RESEARCH_LIMITATION_DISCLOSED | One predeclared paired CVaR-EW mean:original.00689120060,LOO.00508077666-.00980775974; corrected.00598371896,LOO.00408710902-.00875998275. |
| ML1 | CONFIRMED_ERROR_FIXED | 91original distinct dates=89months+2earlier security dates. Corrected27632rows/89common dates/15complete folds rather than27640/91/17. |
| ML2 | CONFIRMED_ERROR_FIXED | 8original ends violate common21-session horizon. Remove2off-month-end features and exclude6incomplete labels; every retained corrected window is21complete sessions. Partition interval checks pass. |
| ML3 | VERIFIED_CORRECT | All17original/15corrected folds preserve1-month embargo at both boundaries; train/validation label ends precede later formation. |
| ML4 | SOURCE_EVIDENCE_BLOCKED | Only frozen book-to-market and12-1momentum reused. UTC-day gate passes; final scalers match permitted training data; independent linear/Ridge/baseline forecasts and coefficients match all folds. |
| ML5 | SOURCE_EVIDENCE_BLOCKED | Held-out predictions map to next common session without realized return entering ranking. |
| ML6 | RESEARCH_LIMITATION_DISCLOSED | factor_composite and linear both use LinearRegression; vectors/ranks exactly identical in all32original+corrected folds. |
| ML7 | VERIFIED_CORRECT | Ridge grid.1/1/10 and training-only scaling preserved; finalalpha.1. Penalized normal equations reproduce fold forecasts/coefficients; max linear-Ridge gap7.66e-6. |
| ML8 | CONFIRMED_ERROR_FIXED | Bootstrap now targets observed mean date IC instead of pooled ranks/bootstrap mean. Constant nonzero forecasts now yield unavailable IC rather thanNaN. Same block3/100resamples/seed17. |
| ML9 | RESEARCH_LIMITATION_DISCLOSED | Every family uses20%equal-weight selected equities,cash reset,one next session and10bps initialL1fee; all economic identities reconcile. |
| ML10 | RESEARCH_LIMITATION_DISCLOSED | Permutation uses validation prediction loss; SHAP explains test predictions with historical background. Top disagreement RF7/17→7/15;XGB10/17→6/15; feature correlation≈-.1875. |

The issue CSV records previous/final status,exact functions,input/hash references,original/corrected numerical evidence,tests,paper consequences and limitations. The same master tracker retains all50IDs. Source-blockedP8/ML4/ML5stay unchecked; upstreamD4/V1remain unchanged. A limitation checkbox records a completed bounded investigation/disclosure,not elimination of the limitation.

## Final immutable publication IDs

Portfolio publications bind the accepted corrected factor and primary-pricing context. ML publications retain their actual raw-score,market-label and historical fee-context dependencies,with fitting versus metric-only source commits distinguished. Full content/output hashes,parent identities,configurations and original counterpart IDs are in the source manifest. Private Parquet/model bundles and restricted sources are not committed.

| Method | BASE | LOW | HIGH |
|---|---|---|---|
| equal_weight | portfolio-56ff12e1590325ab00bdd65e67bdc83e | portfolio-11709b3a14018e43df2bf8e1d2718c91 | portfolio-46f99762b2a9b628e2646a277a409df0 |
| minimum_variance | portfolio-da8cd6b77d46e57138a924a8c9d106eb | portfolio-db82d1daea8b14a78d8ca1ad62fc4f10 | portfolio-0f33c5f2bdfc6c53bd3fdcfc37443e31 |
| mean_variance | portfolio-99d63f9cb5aecc834329df585ebc2577 | portfolio-f9af93e679dc89edcf678e1152c76966 | portfolio-679edfb80b2d261518cddabc748e87a8 |
| maximum_sharpe | portfolio-bb374ca488687ec7e964587f30e3bd15 | portfolio-9a62cedf9b5baa43a9da6007ed619a49 | portfolio-97707e729b6f181beb475c101d84c6e5 |
| maximum_diversification | portfolio-af2465790ec1d893a2f71af83b3cfc4d | portfolio-82915787237332d51851eac12ae03fc5 | portfolio-dbc423d7ffbb7e16cb206b235ba8fa46 |
| risk_parity | portfolio-102f3597c9fdfe7e17e7e910ec1173cd | portfolio-e56cddb97819bad16b4ef99a6be46184 | portfolio-9a112be955a1bfe41b0afaedd1918588 |
| hrp | portfolio-66f902bdd7cf1bfb2b8c250de9717e8f | portfolio-76342a886b06a0812512cb13cb4a372f | portfolio-8f21debde1810a36b38ccbb8fee59d27 |
| cvar | portfolio-87fa6e8666cac548ba3c936ef55cb733 | portfolio-2d158887153105a965bebd1478ac735b | portfolio-732b4e4da91d4adfa23ea3c69720421b |

| Family | Corrected publication |
|---|---|
| zero | ml-6731aae58077b43bafcb27e2ede9b879 |
| historical_mean | ml-8465c40774367a85a0d73163324ba5c6 |
| factor_composite | ml-7d6d0a56ed4aef365ee6510c4bd28b81 |
| linear | ml-b7855cf2b3ddbe94b38d20a544743469 |
| ridge | ml-0dce7f82c4a92e971bb4740a7d0d3632 |
| elastic_net | ml-d35e503f6a33010aa0346e2eda1b8678 |
| random_forest | ml-b2185fbf1e37089aeb1c0b122e757890 |
| xgboost | ml-74e283ab3be2bba30aa7d6d21281951f |

Twenty-four portfolio and8ML publications are the final accepted corrected outputs. Eight metric-only predecessors and one interrupted-run EW trial are preserved as unselected forensic records,not competing final studies. Original historical publications and all parent bytes remain unchanged.

## Validation and Phase4 handoff

Six new targeted regressions pass;91targeted tests pass. The final full suite ran once to completion after the last core correction: **372passed,105warnings,90.62%coverage,443.10seconds**. An earlier broad pass was interrupted at58%when actual frozen outputs exposed the additional degenerate-IC bug; this is documented rather than counted as a completed final run. Warnings concern existing dependency deprecation,constant-rank fixtures and small classification folds. Type checks115source files,Rufflint/format164files and dependency lock96packages pass.

Independent tolerances are1e-9accounting,1e-7optimizer objectives,1e-10forecast/coefficient checks and1e-12IC/economic identities. Failures stop the verifier. Earlier tree-reference fields remain unavailable instead of fabricated zeros. Source-cache guards,accepted canonical anchors,new manifest authority and staged evidence-byte checks preserve traceability; exact commands/logs are in `PHASE3_TEST_RESULTS.txt`.

For Phase4,reconcile portfolio tables/cash units,31-cycle horizon,89-month/15-fold population,date-IC intervals and one-session economic claims. Retain frozen provider-vintage adjusted-quote wording,universe selection,PIT/close-time limits and estimator aliases. Independent review is needed before stronger financial claims. **No paper/README edit,Phase4execution,Phase5cleanup,PRmerge or main change occurred.**
