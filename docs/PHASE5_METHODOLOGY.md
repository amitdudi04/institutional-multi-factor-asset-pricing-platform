# Phase 5 Methodology

## Research question

The software supports testing whether a temporally safe model adds stable incremental information beyond zero, historical-mean, factor-composite, linear, and regularized challengers. It does not assume the answer is positive. No live empirical study was run and no alpha conclusion exists.

## Features and targets

Feature rows require canonical security identity, formation/decision time, maximum availability time, source publication identity, unit metadata, deterministic order, and coverage. Future-named and target-derived fields are rejected. Supported explicit targets are future return, benchmark-relative return, cross-sectional ranks/buckets, outperformance, and future-risk variants. Horizon and benchmark are configuration identities; the repository baseline intentionally leaves the owner-dependent target and horizon unset.

## Temporal validation

Holdout, expanding, rolling, and walk-forward folds operate on ordered formation dates. Training target windows overlapping validation and validation windows overlapping test are purged. Configured embargo periods separate partitions. Random financial splitting is rejected. Imputation, winsorization, and scaling fit only through the training cutoff; feature order and fitted-state identity are checked at transform and prediction time.

## Models and selection

Implemented families are zero/historical-mean baselines, factor-composite and ordinary linear models, logistic regression, Ridge, Lasso, Elastic Net, Random Forest regression/classification, and XGBoost regression/classification. Grid search is bounded, records success/failure and duration, and receives training/validation arrays only. Test data is not accepted by the tuning interface. Threads and seeds are explicit; GPU execution is absent.

## Evaluation and uncertainty

Regression metrics include MAE, RMSE, median absolute error, cautious R², Pearson/Spearman/IC, direction, bias, and dispersion. Classification includes accuracy, balanced accuracy, precision/recall/F1, ROC/PR AUC, log loss, Brier score, calibration error, and confusion matrix with undefined metrics retained as unavailable. Ranking includes date-level IC, dispersion, top-minus-bottom target spread, top-k precision, and turnover. Date-block bootstrap provides IC uncertainty. Ablations preserve the same split assignments.

## Explainability and drift

Linear explanations expose coefficients and signs. Tree explanations expose native and permutation importance plus bounded SHAP values using training-period backgrounds only. SHAP and importance are not causal; correlated features can redistribute attribution. Drift diagnostics report missingness, mean/variance shift, PSI, KS, and Wasserstein distance. Phase 5 reports drift and does not automatically retrain.

## Economic evaluation

Authenticated predictions are converted to long-only selections and passed to the existing Phase 4 backtest engine. That engine owns next-period execution, self-financing weight drift, turnover, transaction costs, benchmark alignment, and performance reconciliation. Open concentration, cost, liquidity, and capital choices remain explicit. Synthetic fixtures test mechanics only and are not empirical performance.
