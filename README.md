# Multi-Factor Asset Pricing and Portfolio Research

This project asks three questions about U.S. equities. How much do characteristics-based factors improve in-sample fit over CAPM? How do eight long-only portfolio methods compare after modeled trading costs? Do two simple characteristics add useful information in a walk-forward forecast?

The multifactor regressions fit the study portfolios better than CAPM. The portfolio methods show different risk and return trade-offs over 31 monthly cycles. The machine-learning results give some evidence of rank predictability for linear models, while stable after-cost value remains unestablished.

[Results](docs/RESULTS.md) · [Methodology](docs/METHODOLOGY.md) · [Data and sources](docs/DATA_AND_SOURCES.md) · [Reproducibility](docs/REPRODUCIBILITY.md) · [Working-paper candidate](outputs/audit/final_correction/FINAL_CANDIDATE_MANUSCRIPT.pdf)

## Data and research design

The study screened **822 candidate securities**, retained **487** and excluded **335**. The retained data include **715,447 daily market observations** and **37,273 SEC-derived fundamental observations**. The sample depends on source availability and screening rules. Public sources include the HF Data Library, SEC EDGAR, Alpha Vantage and FRED. The Kenneth French Data Library provides a reference for factor definitions, and SPY serves as a broad U.S. equity benchmark.

The factor engine defines **48 characteristics and return series**, of which **47** have usable raw observations. The available SEC evidence could not support a consistent equity-issuance measure, so it remains missing. The corrected quantile-return sample contains **11,352 complete portfolio-cycle observations** across 41 sorting characteristics and 123 portfolio series. Availability controls use recorded data dates, with incomplete evidence for the original timing of every filing capture.

The regressions and allocation tests use quantile returns. The forecasting experiment uses security-level features and forward returns. Each analysis has its own sample and timing rules. [Data and sources](docs/DATA_AND_SOURCES.md) · [Research design](docs/METHODOLOGY.md)

## Asset-pricing results

All five models use the same 67–77 monthly trading cycles per test portfolio. The study estimates 615 OLS regressions across 123 portfolios using three-lag Newey–West standard errors.

| Model | Mean adjusted R² | Mean alpha per cycle | Nominal HAC p < 0.05 |
| --- | ---: | ---: | ---: |
| CAPM | 0.760818 | −0.001658 | 8/123 |
| Fama–French 3-factor specification | 0.802438 | −0.001967 | 12/123 |
| Carhart 4-factor specification | 0.811021 | −0.001879 | 14/123 |
| Fama–French 5-factor specification | 0.817658 | −0.002008 | 8/123 |
| Study-specific q-style specification | 0.814361 | −0.002227 | 9/123 |

Alpha is a decimal return per cycle. The specifications use factors constructed for this study. The q-style specification uses earnings yield as one of its inputs. The portfolios share constituents and include six pairs with identical return series. No primary intercept survives the supplementary Holm adjustment. The R² comparison describes in-sample fit on these portfolios. [Regression results](docs/RESULTS.md#3-asset-pricing-results)

## Portfolio results

Eight methods allocate across 123 long-only quantile sleeves over **31 complete monthly cycles**. Costs are 5, 10 or 20 basis points per unit of absolute traded weight (L1). In the 10-bp case, the initial investment costs 10 bps and a full switch between portfolios costs 20 bps. Trades within the sleeves, capacity and market impact are outside this cost estimate.

| Strategy | Selected result at 10 bps |
| --- | --- |
| Minimum Variance | Annualized volatility of 9.9505% |
| Maximum Diversification | Maximum drawdown of −4.8279% |
| Maximum Sharpe | Realized Sharpe ratio of 1.346360 |
| CVaR | Cumulative net return of 73.6842% and Sharpe ratio of 1.252327 |

These results describe the observed sample from February 2024 to August 2026. The short evaluation window limits conclusions about which method will perform better in other periods. [Portfolio results](docs/RESULTS.md#4-portfolio-cost-and-risk-results)

## Walk-forward forecast

Book-to-market and 12-minus-1 momentum are used to forecast the next 21 trading sessions of security returns relative to SPY. The study covers **27,632 rows, 89 month ends and 15 test folds**, with 7,286 held-out observations per model. The design uses expanding training, label purging and a one-month embargo. Five pairs of adjacent test folds have overlapping return windows.

Elastic Net has a mean rank IC of **0.044609**, compared with **−0.002641** for Random Forest and **−0.023285** for XGBoost. The linear and factor-composite rows produce identical predictions. Constant forecasts have undefined IC. The bootstrap intervals are exploratory given the number of folds, their dependence and the number of models compared. The investment check resets to cash each month and evaluates the next session after fees. This design leaves the economic value of holding a 21-session forecast unresolved. [Forecast and economic results](docs/RESULTS.md#5-walk-forward-machine-learning)

## Reproduce the public checks

Use Python 3.11 or newer and `uv`.

```shell
uv sync --frozen --all-groups
uv run pytest
uv run coverage report --fail-under=90
uv run institutional-factor-platform validate-config
uv run institutional-factor-platform verify-delivery-platform
```

The public checkout includes the software, tests, published summaries and reconciliation records. Exact empirical reproduction requires access to the frozen vendor inputs and local research artifacts. The historical software tags and the sources for the corrected study are listed in the [reproducibility guide](docs/REPRODUCIBILITY.md). The API and dashboard display stored research outputs. See [software usage](docs/SOFTWARE_USAGE.md).

| Repository path | Contents |
| --- | --- |
| `src/`, `config/`, `tests/` | Analysis, delivery code, settings and tests |
| `docs/` | Research design, results, limitations and reproduction instructions |
| [Research evidence](docs/research_audit/INDEX.md) | Validation reports, underlying tables and output provenance |
| [CITATION.cff](CITATION.cff) | Citation metadata for the historical software release |

The [working-paper candidate](outputs/audit/final_correction/FINAL_CANDIDATE_MANUSCRIPT.pdf) is under [author review](outputs/audit/final_correction/DEFERRED_AUTHOR_REVIEW.md). Code and documentation are provided under the [MIT License](LICENSE). Third-party data are subject to their providers’ terms.
