# Phase 3 Model Methodology

## Return and timing conventions

All returns are decimal simple returns at monthly frequency. For test asset (i), the dependent return is (R_{i,t}-R_{f,t}), using the authenticated same-date Phase 2 risk-free value. Market excess is the Phase 2 `excess_return` characteristic. Other factors are configured high-minus-low realized returns across the extreme Phase 2 quantiles. Formation precedes realization under the Phase 2 contract, and Phase 3 additionally requires observation availability no later than its permitted date. Exact dates are joined; interpolation, forward fill, and nearest-date matching are prohibited.

The project spreads are research constructions and are not official Fama-French or q-factor provider series. Model names describe equations and mapped economic concepts, not identity with an external provider implementation.

## Model equations

Each time-series model estimates (R_{i,t}-R_{f,t}=\alpha_i+\beta_i'F_t+\epsilon_{i,t}).

| Model | Factors |
|---|---|
| CAPM | market excess |
| Fama-French 3 | market excess, SMB, HML |
| Carhart 4 | market excess, SMB, HML, MOM |
| Fama-French 5 | market excess, SMB, HML, RMW, CMA |
| Hou-Xue-Zhang q | market excess, ME, IA, ROE |
| Custom | explicit unique caller-defined factor tuple, outside the approved default registry |

The default mappings are versioned in `config/asset_pricing.yaml`: size uses `log_market_cap`, value uses `book_to_market`, momentum uses `momentum_12_1`, profitability uses `gross_profitability`, investment uses `asset_growth`, and q profitability uses `earnings_yield`. Direction-adjusted Phase 2 scores determine the high-minus-low orientation.

## Estimation and inference

OLS is the publication estimator. WLS is supported when finite, positive, index-aligned weights are explicitly supplied. Covariance choices are classical, HC0–HC3, and Newey-West HAC; publications use finite-sample-corrected HAC with configured lags. Outputs contain coefficients including alpha, standard errors, t-statistics, p-values, confidence intervals, observations, residual degrees of freedom, R-squared, adjusted R-squared, AIC, BIC, and residual standard error.

Rolling windows contain only observations at or before each window end. Expanding windows hold the first date fixed and add only past observations. Panel estimation supports pooled regressions and explicit entity/time dummy effects. Fama-MacBeth first estimates valid date-level cross-sections, then reports time-series mean premia with HAC inference. Prediction-interval utilities exist for forecast contexts; retrospective publication does not label in-sample fitted-value uncertainty as a forecast interval.

## Diagnostics and validation

Validation rejects missing columns, insufficient complete observations, non-finite values, constant dependent or factor series, rank-deficient design matrices, and invalid covariance matrices. Diagnostics report Jarque-Bera, Breusch-Pagan, White where identified, Durbin-Watson, Ljung-Box, ADF, VIF, covariance rank and condition number, leverage, Cook's distance, and studentized residuals. Statistical significance is not treated as economic importance, causality, model validity, or investment evidence.

## Limitations

No live or issuer-scale data was used in Phase 3 validation. Synthetic fixtures test software correctness only. Free-data and Phase 2 coverage limitations carry forward. Characteristic-spread mappings are configurable project baselines, factor definitions can differ from published academic construction details, multiple-testing controls are not automatically imposed, and rolling estimates remain sensitive to sample length and regimes. Empirical use requires authenticated data, documented model selection, economic-magnitude review, and independent assurance.
