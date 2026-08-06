# Phase 5 Model Validation

## Validation policy

An acceptable model must preserve source authentication, temporal separation, feature/preprocessor/model identity, held-out evaluation, reproducible seeds, immutable predictions, and explanation identity. Model status is restricted to `EXPERIMENTAL`, `VALIDATED_RESEARCH`, `CHALLENGER`, `REJECTED`, or `DEPRECATED`; Phase 5 never labels a model production or deployable.

## Adversarial matrix

Tests reject target/future features, late evidence, duplicate identity, random splitting, insufficient folds, overlapping target windows, future-fitted preprocessors, reordered features, one-class classification, invalid probabilities, unbounded tuning, test-period calibration ordering, future SHAP backgrounds, explanation shape changes, unauthenticated economic signals, incomplete publications, model/prediction mutation, supplied-artifact substitution, and disconnected Phase 2/3 lineage.

XGBoost and Random Forest reproducibility are checked with fixed seeds and bounded threads. SHAP shape and training-background identity are checked. Publication restart authenticates the complete bundle and trusted-local model loads authenticate bytes before Joblib deserialization.

## Interpretation boundary

Predictive accuracy, rank correlation, feature importance, SHAP values, and synthetic economic fixtures do not establish a factor premium, causal relationship, investable alpha, capacity, or live suitability. `LIVE EMPIRICAL ML VALIDATION PENDING` remains the correct research status.

## Recorded software gate

The complete Phase 1–5 suite passed 209 tests with 90.00% branch-aware coverage. Ruff lint and formatting, strict Mypy across 87 source files, lock verification, all 34 CLI help paths, alternate hash-seed Phase 5 tests, Markdown links, import-cycle analysis, dependency-license review, security scans, and tracked-artifact scans passed.
