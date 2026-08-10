# Phase 5 Model Card Guide

Every accepted research model card records model/family/task, explicit target and horizon, authenticated target-source dataset/checksum/unit, intended and prohibited use, universe, the complete fold inventory and train/validation/test intervals, ordered features, preprocessor identity, search and selection rationale, seed, predictive/ranking/calibration metrics, challenger/ablation/stability evidence, economic evaluation status, explanations, drift, limitations, failure modes, data and dependency versions, artifact checksums, configuration, Git commit, and status.

Cards must state that explanations are not causal, results are configuration-dependent, live serving is absent, production deployment is absent, and empirical validation is pending unless an authenticated study actually exists. A card is part of the checksum-bound publication. Substitution or stale identity invalidates the complete supported read.

Joblib model/preprocessor artifacts are trusted-local-only. Authentication must precede deserialization; downloaded or arbitrary Pickle/Joblib files are prohibited.
