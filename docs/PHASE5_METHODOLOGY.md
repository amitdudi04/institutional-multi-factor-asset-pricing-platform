# Phase 5 Methodology

## Research question

The software supports testing whether a temporally safe model adds stable incremental information beyond zero, historical-mean, factor-composite, linear, and regularized challengers. It does not assume the answer is positive. No live empirical study was run and no alpha conclusion exists.

## Features and targets

Feature rows require canonical security identity, formation/decision time, maximum availability time, source publication identity, unit metadata, deterministic order, and coverage. Future-named and target-derived fields are rejected. Targets use the authenticated Phase 1 security-return artifact bound in Phase 2 lineage, never market-wide factor observations. Supported explicit targets are compounded future return, compounded security-minus-benchmark return, cross-sectional ranks/buckets, benchmark outperformance, annualized sample volatility, annualized downside deviation, cumulative-wealth maximum drawdown, and historical risk quantile under a positive-loss convention. Horizon, benchmark, annualization, minimum acceptable return, and quantile probability are configuration identities; the repository baseline intentionally leaves the owner-dependent target and horizon unset.

## Temporal validation

Holdout, expanding, rolling, and walk-forward folds operate on ordered formation dates. Every returned test fold is evaluated. `retrain_every` either fits a new training-only preprocessor/model or reuses the prior authenticated model according to the recorded cadence; the actual model-training interval remains distinct from the available fold-training interval. Training target windows overlapping validation and validation windows overlapping test are purged. Configured embargo periods separate partitions. Random financial splitting is rejected. Imputation, winsorization, scaling, search, calibration, and explanation backgrounds remain pre-test.

## Models and selection

Implemented families are zero/historical-mean baselines, factor-composite and ordinary linear models, logistic regression, Ridge, Lasso, Elastic Net, Random Forest regression/classification, and XGBoost regression/classification. Configured grid search is bounded, records parameters, success/failure, duration bucket, selection metric, and selected model identity, and receives training/validation arrays only. Sigmoid or isotonic calibration fits only on the validation interval and records calibrator and period identity. Test data is not accepted by either interface. Threads and seeds are explicit; GPU execution is absent.

## Evaluation and uncertainty

Regression metrics include MAE, RMSE, median absolute error, cautious R², Pearson/Spearman/IC, direction, bias, and dispersion. Classification includes accuracy, balanced accuracy, precision/recall/F1, ROC/PR AUC, log loss, Brier score, calibration error, and confusion matrix with undefined metrics retained as unavailable. Ranking includes date-level IC, dispersion, top-minus-bottom target spread, top-k precision, and turnover. Date-block bootstrap provides IC uncertainty. Ablations preserve the same split assignments.

## Explainability and drift

Linear explanations expose coefficients and signs. Tree explanations expose permutation importance plus bounded local SHAP values using training-period backgrounds only. Explanation rows bind fold, model checksum, preprocessing identity, feature schema, feature/prediction artifact checksums, background hash, configuration, seed, dependency version, and Git identity. SHAP and importance are not causal; correlated features can redistribute attribution. Drift diagnostics report missingness, mean/variance shift, PSI, KS, and Wasserstein distance. Phase 5 reports drift and follows only the configured retraining cadence.

## Economic evaluation

When enabled, the service requires an authenticated Phase 4 publication whose Phase 2/3 hashes match the ML lineage. Authenticated predictions are converted to long-only selections and passed to the existing Phase 4 backtest engine using the bound Phase 4 cost configuration. That engine owns next-period execution, self-financing weight drift, turnover, transaction costs, benchmark alignment, and performance reconciliation. Fold-level evidence records gross/net returns, costs, long-only/full-investment checks, and reconciliation. Disabled evaluation is reported as `NOT_REQUESTED`; it is never represented by a success placeholder. Synthetic fixtures test mechanics only and are not empirical performance.
