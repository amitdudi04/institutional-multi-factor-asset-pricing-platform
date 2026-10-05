"""Machine-learning dataset, training, evaluation, and publication service."""

import hashlib
import io
import json
import subprocess
from importlib.metadata import version
from pathlib import Path
from typing import cast

import joblib
import numpy as np
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
from numpy.typing import NDArray

from institutional_factor_platform.backtest.costs import TransactionCostModel
from institutional_factor_platform.data.access import ResearchDatasetRepository
from institutional_factor_platform.data.evidence import resolve_project_path
from institutional_factor_platform.exceptions import DataQualityError, EvidenceIntegrityError
from institutional_factor_platform.factors.storage import FactorRepository
from institutional_factor_platform.ml.config import MachineLearningConfig
from institutional_factor_platform.ml.contracts import ModelCard, TargetSpecification
from institutional_factor_platform.ml.economic import evaluate_ranked_signal
from institutional_factor_platform.ml.evaluation import (
    block_bootstrap_ic,
    classification_metrics,
    ranking_metrics,
    regression_metrics,
)
from institutional_factor_platform.ml.features import (
    add_interactions,
    assemble_factor_features,
    monthly_decision_features,
)
from institutional_factor_platform.ml.models import ResearchModel, Task, create_model
from institutional_factor_platform.ml.preprocessing import SafePreprocessor
from institutional_factor_platform.ml.publication import MLManifest, publish_bundle
from institutional_factor_platform.ml.splits import assign_and_purge, temporal_folds
from institutional_factor_platform.ml.targets import build_targets
from institutional_factor_platform.ml.validation import (
    bounded_grid_search,
    calibrate_classifier,
    drift_report,
    linear_explanation,
    tree_explanations,
)
from institutional_factor_platform.research_outputs.portfolio_storage import PortfolioRepository
from institutional_factor_platform.research_outputs.storage import AssetPricingRepository

ArtifactContent = tuple[bytes, str, tuple[str, ...]]


class MLResearchService:
    def __init__(
        self,
        config: MachineLearningConfig,
        root: Path,
        factors: FactorRepository,
        pricing: AssetPricingRepository,
        phase1: ResearchDatasetRepository,
        portfolios: PortfolioRepository | None = None,
    ) -> None:
        self.config = config
        self.root = root.resolve()
        self.factors = factors
        self.pricing = pricing
        self.phase1 = phase1
        self.portfolios = portfolios

    def build_authenticated_dataset(
        self, phase3_publication_id: str
    ) -> tuple[pd.DataFrame, dict[str, object]]:
        phase3 = self.pricing.authenticate(phase3_publication_id)
        phase2 = self.factors.authenticate(phase3.phase2_publication_id)
        if phase3.phase2_manifest_hash != phase2.content_hash():
            raise EvidenceIntegrityError("Phase 2 and Phase 3 lineage do not connect")
        kind, horizon = self.config.target.require_explicit()
        selected = self.config.features.families
        if not selected:
            raise DataQualityError("Feature families must be explicit for a research run")
        factor_table = self.factors.read_table(phase2.publication_id).to_pandas()
        features, schema, report = assemble_factor_features(
            factor_table,
            selected,
            self.config.features.value_column,
            source_publication_id=phase2.publication_id,
            minimum_coverage=self.config.features.minimum_coverage,
        )
        features = add_interactions(features, self.config.features.interactions)
        features = monthly_decision_features(features)
        report["monthly_rows"] = len(features)
        market_ids = tuple(phase2.market_source_dataset_ids)
        if len(market_ids) != 1:
            raise EvidenceIntegrityError(
                "ML target construction requires exactly one authenticated Phase 1 market parent"
            )
        market_id = market_ids[0]
        parent = next((item for item in phase2.parents if item.dataset_id == market_id), None)
        if parent is None:
            raise EvidenceIntegrityError("Phase 2 market parent is absent from bound lineage")
        market = self.phase1.get(market_id)
        if market.checksum != parent.artifact_checksum:
            raise EvidenceIntegrityError("Phase 1 market artifact differs from Phase 2 lineage")
        return_unit = market.unit_metadata.get("return", market.unit_metadata.get("request.return"))
        if return_unit != "decimal_return":
            raise EvidenceIntegrityError("ML targets require authenticated decimal-return units")
        source = self.phase1.read_table(market_id).to_pandas()
        targets, spec = build_targets(
            source,
            kind=kind,
            horizon=horizon,
            benchmark_id=self.config.target.benchmark_id,
            threshold=self.config.target.threshold or 0,
            quantiles=self.config.target.quantiles,
            annualization_periods=self.config.target.annualization_periods,
            minimum_acceptable_return=self.config.target.minimum_acceptable_return,
            risk_quantile_alpha=self.config.target.risk_quantile_alpha,
            source_publication_id=market.dataset_id,
            source_artifact_checksum=market.checksum,
            source_unit=return_unit,
        )
        dataset = features.merge(
            targets, on=["security_id", "formation_date"], validate="one_to_one"
        )
        if (
            pd.to_datetime(dataset["feature_available_at"], utc=True)
            > pd.to_datetime(dataset["decision_time"], utc=True)
        ).any():
            raise EvidenceIntegrityError("Merged dataset violates feature availability")
        metadata: dict[str, object] = {
            "phase2_publication_id": phase2.publication_id,
            "phase2_manifest_hash": phase2.content_hash(),
            "phase3_publication_id": phase3.publication_id,
            "phase3_manifest_hash": phase3.content_hash(),
            "feature_schema_hash": schema.content_hash(),
            "target_hash": spec.content_hash(),
            "target_specification": spec,
            "target_source_dataset_id": market.dataset_id,
            "target_source_artifact_checksum": market.checksum,
            "target_source_unit": return_unit,
            "feature_report": report,
            "git_commit": _git_commit(self.root),
        }
        return dataset, metadata

    def train_evaluate_publish(self, phase3_publication_id: str, family: str) -> MLManifest:
        if family not in self.config.models.enabled:
            raise DataQualityError("Requested model family is not enabled by configuration")
        dataset, metadata = self.build_authenticated_dataset(phase3_publication_id)
        feature_names = tuple(
            sorted(
                [*self.config.features.families]
                + [f"{left}__x__{right}" for left, right in self.config.features.interactions]
            )
        )
        folds = temporal_folds(
            dataset,
            method=self.config.split.method,
            train_periods=self.config.split.train_periods,
            validation_periods=self.config.split.validation_periods,
            test_periods=self.config.split.test_periods,
            rolling_periods=self.config.split.rolling_periods,
            embargo_periods=self.config.split.embargo_periods,
        )
        kind, _horizon = self.config.target.require_explicit()
        task: Task = (
            "classification"
            if kind == "outperformance"
            else "ranking"
            if "rank" in kind or "quantile" in kind
            else "regression"
        )
        assignments: list[pd.DataFrame] = []
        predictions: list[pd.DataFrame] = []
        evaluations: list[dict[str, object]] = []
        trials: list[dict[str, object]] = []
        calibrations: list[dict[str, object]] = []
        explanation_frames: list[pd.DataFrame] = []
        drift_frames: list[pd.DataFrame] = []
        comparisons: list[dict[str, object]] = []
        processor: SafePreprocessor | None = None
        model: ResearchModel | None = None
        fitted_train: pd.DataFrame | None = None
        for fold_index, fold in enumerate(folds):
            assigned = assign_and_purge(dataset, fold, purge=self.config.split.purge_overlaps)
            assignments.append(assigned)
            train = assigned.loc[assigned["partition"].eq("train")]
            validation = assigned.loc[assigned["partition"].eq("validation")]
            test = assigned.loc[assigned["partition"].eq("test")]
            retrain = model is None or fold_index % self.config.split.retrain_every == 0
            if retrain:
                processor = SafePreprocessor(
                    feature_names,
                    self.config.missing.policy,
                    self.config.preprocessing.scaling,
                    self.config.preprocessing.winsor_lower,
                    self.config.preprocessing.winsor_upper,
                ).fit(
                    train,
                    train["formation_date"],
                    allowed_training_end=pd.to_datetime(train["formation_date"], utc=True).max(),
                )
                train_x = processor.transform(train).to_numpy(float)
                validation_x = processor.transform(validation).to_numpy(float)
                train_y = train["target"].to_numpy(float)
                validation_y = validation["target"].to_numpy(float)
                search_space = self.config.search.spaces.get(family, {})
                if search_space:
                    model, fold_trials = bounded_grid_search(
                        family,
                        task,
                        feature_names,
                        processor.identity(),
                        cast(str, metadata["target_hash"]),
                        train_x,
                        train_y,
                        validation_x,
                        validation_y,
                        search_space,
                        maximum_trials=self.config.search.maximum_trials,
                        seed=self.config.models.random_seed,
                        threads=self.config.models.thread_limit,
                    )
                    trials.extend(
                        {
                            "fold": fold.fold,
                            "parameters": item.parameters,
                            "metric": item.metric,
                            "status": item.status,
                            "failure_reason": item.failure_reason,
                            "duration_seconds": int(item.duration_seconds),
                            "selected_model_id": model.model_id,
                        }
                        for item in fold_trials
                    )
                else:
                    model = create_model(
                        family,
                        task,
                        feature_names,
                        processor.identity(),
                        cast(str, metadata["target_hash"]),
                        seed=self.config.models.random_seed,
                        threads=self.config.models.thread_limit,
                    ).fit(train_x, train_y)
                    trials.append(
                        {
                            "fold": fold.fold,
                            "parameters": {},
                            "metric": None,
                            "status": "NOT_APPLICABLE",
                            "failure_reason": None,
                            "duration_seconds": 0.0,
                            "selected_model_id": model.model_id,
                        }
                    )
                fitted_train = train
            else:
                assert model is not None
                trials.append(
                    {
                        "fold": fold.fold,
                        "parameters": {},
                        "metric": None,
                        "status": "REUSED_BY_RETRAINING_CADENCE",
                        "failure_reason": None,
                        "duration_seconds": 0.0,
                        "selected_model_id": model.model_id,
                    }
                )
            assert processor is not None and model is not None and fitted_train is not None
            validation_x = processor.transform(validation).to_numpy(float)
            test_x = processor.transform(test).to_numpy(float)
            test_y = test["target"].to_numpy(float)
            prediction = model.predict(test_x, feature_names)
            prediction_frame = test[
                ["security_id", "formation_date", "decision_time", "feature_coverage"]
            ].copy()
            prediction_frame["target"] = test_y
            prediction_frame["prediction"] = prediction
            prediction_frame["rank"] = prediction_frame.groupby("formation_date")[
                "prediction"
            ].rank(method="first", pct=True)
            prediction_frame["model_id"] = model.model_id
            prediction_frame["fold"] = fold.fold
            prediction_frame["retrained"] = retrain
            prediction_frame["authentication_status"] = "PASS"
            if task == "classification":
                probability = model.predict_probability(test_x, feature_names)
                calibration_status = "NOT_REQUESTED"
                calibrator_id: str | None = None
                if self.config.calibration.method != "none":
                    if len(validation) < self.config.calibration.minimum_samples:
                        raise DataQualityError("Calibration validation population is below minimum")
                    calibrator = calibrate_classifier(
                        model,
                        validation_x,
                        validation["target"].to_numpy(float),
                        method=self.config.calibration.method,
                        validation_end=pd.to_datetime(validation["formation_date"], utc=True).max(),
                        test_start=pd.to_datetime(test["formation_date"], utc=True).min(),
                    )
                    probability = np.asarray(calibrator.predict_proba(test_x))[:, 1]
                    calibrator_buffer = io.BytesIO()
                    joblib.dump(calibrator, calibrator_buffer)
                    calibrator_id = hashlib.sha256(calibrator_buffer.getvalue()).hexdigest()
                    calibration_status = "PASS"
                prediction_frame["probability"] = probability
                fold_metrics: dict[str, object] = classification_metrics(test_y, probability)
                calibrations.append(
                    {
                        "fold": fold.fold,
                        "method": self.config.calibration.method,
                        "status": calibration_status,
                        "calibrator_id": calibrator_id,
                        "validation_start": str(validation["formation_date"].min()),
                        "validation_end": str(validation["formation_date"].max()),
                        "test_start": str(test["formation_date"].min()),
                        "validation_rows": len(validation),
                    }
                )
            else:
                fold_metrics = dict(regression_metrics(test_y, prediction))
                fold_metrics.update(ranking_metrics(prediction_frame))
                calibrations.append(
                    {
                        "fold": fold.fold,
                        "method": "none",
                        "status": "NOT_APPLICABLE_NON_CLASSIFICATION",
                        "calibrator_id": None,
                        "validation_rows": len(validation),
                    }
                )
            predictions.append(prediction_frame)
            evaluations.append(
                {
                    "fold": fold.fold,
                    "model_id": model.model_id,
                    "retrained": retrain,
                    "available_train_period": [
                        str(train["formation_date"].min()),
                        str(train["formation_date"].max()),
                    ],
                    "model_training_period": [
                        str(fitted_train["formation_date"].min()),
                        str(fitted_train["formation_date"].max()),
                    ],
                    "validation_period": [
                        str(validation["formation_date"].min()),
                        str(validation["formation_date"].max()),
                    ],
                    "test_period": [
                        str(test["formation_date"].min()),
                        str(test["formation_date"].max()),
                    ],
                    "metrics": fold_metrics,
                }
            )
            comparisons.extend(
                self._challenger_comparison(
                    family,
                    task,
                    feature_names,
                    processor,
                    fitted_train,
                    test,
                    test_x,
                    fold.fold,
                    cast(str, metadata["target_hash"]),
                    fold_metrics,
                )
            )
            if self.config.explainability.enabled:
                if family in {"zero", "historical_mean"}:
                    explanation = pd.DataFrame(
                        {
                            "feature": feature_names,
                            "value": np.zeros(len(feature_names), dtype=float),
                            "method": "not_applicable_baseline",
                            "background_hash": hashlib.sha256(b"not-applicable").hexdigest(),
                        }
                    )
                elif family in {
                    "factor_composite",
                    "linear",
                    "ridge",
                    "lasso",
                    "elastic_net",
                    "logistic",
                }:
                    explanation = linear_explanation(model).rename(columns={"coefficient": "value"})
                    explanation["method"] = "coefficient"
                    explanation["background_hash"] = hashlib.sha256(b"not-applicable").hexdigest()
                else:
                    background = processor.transform(fitted_train).to_numpy(float)[
                        : self.config.explainability.background_size
                    ]
                    sample = test_x[: self.config.explainability.sample_size]
                    permutation, shap_values, background_hash = tree_explanations(
                        model,
                        background,
                        sample,
                        validation["target"].to_numpy(float),
                        validation_x,
                        background_dates=fitted_train["formation_date"].iloc[: len(background)],
                        training_end=pd.to_datetime(fitted_train["formation_date"], utc=True).max(),
                        seed=self.config.explainability.random_seed,
                    )
                    explanation = permutation.rename(columns={"permutation_importance": "value"})
                    explanation["method"] = "permutation"
                    explanation["background_hash"] = background_hash
                    local = shap_values.stack().rename("value").reset_index()
                    local = local.rename(columns={"level_1": "feature", "level_0": "sample"})
                    local["method"] = "shap"
                    local["background_hash"] = background_hash
                    explanation = pd.concat([explanation, local], ignore_index=True, sort=False)
                explanation["fold"] = fold.fold
                explanation["model_id"] = model.model_id
                explanation["preprocessor_hash"] = processor.identity()
                explanation_frames.append(explanation)
            fold_drift = drift_report(
                fitted_train, test, feature_names, bins=self.config.drift.psi_bins
            )
            fold_drift["fold"] = fold.fold
            drift_frames.append(fold_drift)
        assert processor is not None and model is not None
        assigned = pd.concat(assignments, ignore_index=True)
        prediction_frame = pd.concat(predictions, ignore_index=True)
        explanations = (
            pd.concat(explanation_frames, ignore_index=True, sort=False)
            if explanation_frames
            else pd.DataFrame({"status": ["NOT_REQUESTED"]})
        )
        drift = pd.concat(drift_frames, ignore_index=True)
        prediction_checksum = hashlib.sha256(_parquet(prediction_frame)[0]).hexdigest()
        feature_checksum = hashlib.sha256(
            _parquet(assigned[[*feature_names, "security_id", "formation_date", "fold"]])[0]
        ).hexdigest()
        model_checksum = hashlib.sha256(model.trusted_bytes()).hexdigest()
        explanations["model_checksum"] = model_checksum
        explanations["prediction_artifact_checksum"] = prediction_checksum
        explanations["feature_matrix_artifact_checksum"] = feature_checksum
        explanations["feature_schema_hash"] = metadata["feature_schema_hash"]
        explanations["configuration_hash"] = self.config.canonical_hash()
        explanations["git_commit"] = metadata["git_commit"]
        comparison_evidence: dict[str, object] = {
            "status": "PASS",
            "folds": comparisons,
            "selected_model_bootstrap_ic": block_bootstrap_ic(
                prediction_frame,
                block_length=max(1, min(3, prediction_frame["formation_date"].nunique())),
                resamples=100,
                seed=self.config.models.random_seed,
            ),
            "fold_metric_stability": _metric_stability(evaluations),
        }
        economic_evaluation = self._economic_evaluation(prediction_frame, metadata)
        final_metrics = evaluations[-1]["metrics"]
        spec = cast(TargetSpecification, metadata["target_specification"])
        card = ModelCard(
            schema_version="1.0.0",
            model_id=model.model_id,
            family=family,
            task=task,
            target=spec,
            intended_use="Point-in-time empirical equity research",
            prohibited_use="Live trading, causal inference, or unreviewed investment decisions",
            universe="Point-in-time screened U.S. equity research universe",
            training_period=_period(assigned, "train"),
            validation_period=_period(assigned, "validation"),
            test_period=_period(assigned, "test"),
            folds=tuple(evaluations),
            features=feature_names,
            preprocessing_hash=processor.identity(),
            hyperparameters={"search_method": self.config.search.method, "trials": len(trials)},
            seed=self.config.models.random_seed,
            metrics={
                k: v
                for k, v in cast(dict[str, object], final_metrics).items()
                if isinstance(v, (int, float)) or v is None
            },
            economic_evaluation=economic_evaluation,
            explanations={"enabled": self.config.explainability.enabled, "rows": len(explanations)},
            drift={"maximum_psi": float(drift["psi"].max())},
            limitations=("Research evidence only", "Explanations are associational, not causal"),
            known_failure_modes=("Regime shift", "Sparse or stale factor inputs"),
            data_dependencies=(
                cast(str, metadata["target_source_dataset_id"]),
                cast(str, metadata["phase2_publication_id"]),
                cast(str, metadata["phase3_publication_id"]),
            ),
            artifact_checksums={
                "target_source": cast(str, metadata["target_source_artifact_checksum"]),
                "model": model_checksum,
                "predictions": prediction_checksum,
                "feature_matrix": feature_checksum,
            },
            dependency_versions={
                name: version(name) for name in ("numpy", "scikit-learn", "shap", "xgboost")
            },
            selection_rationale=(
                f"Selected {family} by bounded {self.config.search.method} search using "
                f"{self.config.search.selection_metric}; compared against configured baselines, "
                "challengers, and feature-family ablations on every temporal test fold."
            ),
            configuration_hash=self.config.canonical_hash(),
            git_commit=cast(str, metadata["git_commit"]),
            status="EXPERIMENTAL",
        )
        contents = self._bundle_contents(
            assigned,
            processor,
            model,
            prediction_frame,
            {"folds": evaluations, "fold_count": len(evaluations)},
            explanations,
            drift,
            trials,
            calibrations,
            comparison_evidence,
            card,
            metadata,
            economic_evaluation,
        )
        return publish_bundle(
            self.root,
            self.config.publication.output_root,
            self.config.publication.manifest_root,
            {
                "phase2_publication_id": metadata["phase2_publication_id"],
                "phase2_manifest_hash": metadata["phase2_manifest_hash"],
                "phase3_publication_id": metadata["phase3_publication_id"],
                "phase3_manifest_hash": metadata["phase3_manifest_hash"],
                "phase4_publication_id": economic_evaluation.get("phase4_publication_id"),
                "phase4_manifest_hash": economic_evaluation.get("phase4_manifest_hash"),
                "configuration_hash": self.config.canonical_hash(),
                "git_commit": metadata["git_commit"],
                "model_id": model.model_id,
                "feature_schema_hash": metadata["feature_schema_hash"],
                "target_hash": metadata["target_hash"],
                "preprocessor_hash": processor.identity(),
                "random_seed": self.config.models.random_seed,
                "dependency_versions": {
                    name: version(name) for name in ("numpy", "scikit-learn", "shap", "xgboost")
                },
                "validation_status": "PASS",
            },
            contents,
        )

    def _economic_evaluation(
        self, predictions: pd.DataFrame, metadata: dict[str, object]
    ) -> dict[str, object]:
        if not self.config.economic_evaluation.enabled:
            return {"enabled": False, "status": "NOT_REQUESTED"}
        phase4_id = self.config.inputs.phase4_publication_id
        selection = self.config.economic_evaluation.selection_quantile
        if self.portfolios is None or phase4_id is None or selection is None:
            raise DataQualityError(
                "Economic evaluation requires an authenticated Phase 4 parent "
                "and explicit selection quantile"
            )
        phase4 = self.portfolios.authenticate(phase4_id)
        if (
            phase4.phase2_publication_id != metadata["phase2_publication_id"]
            or phase4.phase2_manifest_hash != metadata["phase2_manifest_hash"]
            or phase4.phase3_publication_id != metadata["phase3_publication_id"]
            or phase4.phase3_manifest_hash != metadata["phase3_manifest_hash"]
        ):
            raise EvidenceIntegrityError("Phase 4 economic parent does not connect to ML lineage")
        config_artifact = next(
            (item for item in phase4.artifacts if item.name == "configuration"), None
        )
        if config_artifact is None:
            raise EvidenceIntegrityError("Phase 4 economic parent lacks configuration evidence")
        phase4_config = json.loads(
            resolve_project_path(config_artifact.path, self.root).read_text("utf-8")
        )["configuration"]
        costs = TransactionCostModel(
            phase4_config["costs"]["commission_bps"],
            phase4_config["costs"]["spread_bps"],
            phase4_config["costs"]["slippage_bps"],
            phase4_config["costs"]["market_impact_coefficient"],
        )
        source = self.phase1.read_table(cast(str, metadata["target_source_dataset_id"])).to_pandas()
        source["date"] = pd.to_datetime(source["date"], utc=True)
        return_matrix = source.pivot(index="date", columns="security_id", values="return").dropna()
        benchmark_group = source.groupby("date")["benchmark_return"]
        if (benchmark_group.nunique(dropna=False) > 1).any():
            raise EvidenceIntegrityError("Authenticated benchmark conflicts across securities")
        benchmark = benchmark_group.first().reindex(return_matrix.index)
        dates = list(return_matrix.index)
        results: list[dict[str, object]] = []
        for fold, fold_predictions in predictions.groupby("fold", sort=True):
            formation_dates = sorted(
                pd.to_datetime(fold_predictions["formation_date"], utc=True).unique()
            )
            first = return_matrix.index.get_loc(formation_dates[0])
            last = return_matrix.index.get_loc(formation_dates[-1])
            if (
                not isinstance(first, (int, np.integer))
                or not isinstance(last, (int, np.integer))
                or first < 1
                or last + 1 >= len(dates)
            ):
                raise DataQualityError("Economic test fold lacks preceding or subsequent returns")
            evaluation_dates = dates[first - 1 : last + 2]
            expected_formations = set(evaluation_dates[1:-1])
            if set(formation_dates) != expected_formations:
                raise DataQualityError(
                    "Economic test fold predictions are not temporally contiguous"
                )
            backtest = evaluate_ranked_signal(
                fold_predictions,
                return_matrix.loc[evaluation_dates],
                benchmark.loc[evaluation_dates],
                costs,
                selection_fraction=selection,
                window=2,
            )
            reconciliation = np.allclose(
                backtest.returns["gross_return"] - backtest.returns["transaction_cost"],
                backtest.returns["net_return"],
                atol=1e-12,
            )
            if not reconciliation:
                raise EvidenceIntegrityError("Economic return and cost reconciliation failed")
            results.append(
                {
                    "fold": int(fold),
                    "return_rows": len(backtest.returns),
                    "allocation_rows": len(backtest.allocations),
                    "transaction_rows": len(backtest.transactions),
                    "gross_cumulative_return": float(
                        np.prod(1 + backtest.returns["gross_return"].to_numpy(float)) - 1
                    ),
                    "net_cumulative_return": float(
                        np.prod(1 + backtest.returns["net_return"].to_numpy(float)) - 1
                    ),
                    "transaction_cost": float(backtest.returns["transaction_cost"].sum()),
                    "long_only": bool((backtest.allocations["weight"] >= 0).all()),
                    "fully_invested": bool(
                        np.allclose(backtest.allocations.groupby("date")["weight"].sum(), 1.0)
                    ),
                    "reconciliation_status": "PASS",
                }
            )
        return {
            "enabled": True,
            "status": "PASS",
            "phase4_publication_id": phase4.publication_id,
            "phase4_manifest_hash": phase4.content_hash(),
            "phase4_configuration_hash": phase4.configuration_hash,
            "costs": phase4_config["costs"],
            "selection_fraction": selection,
            "folds": results,
        }

    def _challenger_comparison(
        self,
        selected_family: str,
        task: Task,
        feature_names: tuple[str, ...],
        processor: SafePreprocessor,
        train: pd.DataFrame,
        test: pd.DataFrame,
        test_x: NDArray[np.float64],
        fold: int,
        target_hash: str,
        selected_metrics: dict[str, object],
    ) -> list[dict[str, object]]:
        rows = [
            {
                "fold": fold,
                "family": selected_family,
                "role": "selected",
                "metrics": selected_metrics,
            }
        ]
        if task == "classification":
            challengers = [
                name
                for name in ("logistic",)
                if name in self.config.models.enabled and name != selected_family
            ]
        else:
            challengers = [
                name
                for name in ("zero", "historical_mean", "linear", "ridge")
                if name in self.config.models.enabled and name != selected_family
            ]
        train_x = processor.transform(train).to_numpy(float)
        train_y = train["target"].to_numpy(float)
        test_y = test["target"].to_numpy(float)
        for challenger in challengers:
            candidate = create_model(
                challenger,
                task,
                feature_names,
                processor.identity(),
                target_hash,
                seed=self.config.models.random_seed,
                threads=self.config.models.thread_limit,
            ).fit(train_x, train_y)
            prediction = candidate.predict(test_x, feature_names)
            if task == "classification":
                metrics = classification_metrics(
                    test_y, candidate.predict_probability(test_x, feature_names)
                )
            else:
                metrics = dict(regression_metrics(test_y, prediction))
                metrics.update(ranking_metrics(test.assign(prediction=prediction)))
            rows.append(
                {
                    "fold": fold,
                    "family": challenger,
                    "role": "challenger",
                    "model_id": candidate.model_id,
                    "metrics": metrics,
                }
            )
        if len(feature_names) > 1 and selected_family not in {"zero", "historical_mean"}:
            full_train_x = processor.transform(train).to_numpy(float)
            for excluded_index, excluded in enumerate(feature_names):
                retained = tuple(name for name in feature_names if name != excluded)
                keep = [index for index in range(len(feature_names)) if index != excluded_index]
                candidate = create_model(
                    selected_family,
                    task,
                    retained,
                    processor.identity(),
                    target_hash,
                    seed=self.config.models.random_seed,
                    threads=self.config.models.thread_limit,
                ).fit(full_train_x[:, keep], train_y)
                prediction = candidate.predict(test_x[:, keep], retained)
                if task == "classification":
                    metrics = classification_metrics(
                        test_y, candidate.predict_probability(test_x[:, keep], retained)
                    )
                else:
                    metrics = dict(regression_metrics(test_y, prediction))
                    metrics.update(ranking_metrics(test.assign(prediction=prediction)))
                rows.append(
                    {
                        "fold": fold,
                        "family": selected_family,
                        "role": "feature_family_ablation",
                        "excluded_family": excluded,
                        "model_id": candidate.model_id,
                        "metrics": metrics,
                    }
                )
        return rows

    def _bundle_contents(
        self,
        assigned: pd.DataFrame,
        processor: SafePreprocessor,
        model: ResearchModel,
        predictions: pd.DataFrame,
        metrics: dict[str, object],
        explanations: pd.DataFrame,
        drift: pd.DataFrame,
        trials: list[dict[str, object]],
        calibrations: list[dict[str, object]],
        comparisons: dict[str, object],
        model_card: ModelCard,
        metadata: dict[str, object],
        economic_evaluation: dict[str, object],
    ) -> dict[str, ArtifactContent]:
        processor_buffer = io.BytesIO()
        joblib.dump(processor, processor_buffer)
        feature_columns = [*processor.feature_names, "security_id", "formation_date", "fold"]
        return {
            "feature_matrix": _parquet(assigned[feature_columns]),
            "targets": _parquet(
                assigned[
                    [
                        "security_id",
                        "formation_date",
                        "target",
                        "target_start",
                        "target_end",
                        "target_available_at",
                        "fold",
                    ]
                ]
            ),
            "splits": _parquet(
                assigned[
                    [
                        "security_id",
                        "formation_date",
                        "target_start",
                        "target_end",
                        "fold",
                        "partition",
                    ]
                ]
            ),
            "preprocessor": (processor_buffer.getvalue(), "application/x-joblib", ()),
            "model": (model.trusted_bytes(), "application/x-joblib", ()),
            "hyperparameter_trials": _document(
                {"trials": trials, "selection": self.config.search.selection_metric}
            ),
            "predictions": _parquet(predictions),
            "evaluation": _document(metrics),
            "calibration": _document({"folds": calibrations}),
            "explanations": _parquet(explanations),
            "drift": _parquet(drift),
            "comparison": _document(comparisons),
            "economic_evaluation": _document(economic_evaluation),
            "model_card": _document(model_card.model_dump(mode="json")),
            "configuration": _document(self.config.model_dump(mode="json")),
            "lineage": _document(
                {
                    "source": "authenticated Phase 1/2/3/4 publications",
                    "target_source_dataset_id": metadata["target_source_dataset_id"],
                    "target_source_artifact_checksum": metadata["target_source_artifact_checksum"],
                    "phase4_publication_id": economic_evaluation.get("phase4_publication_id"),
                    "phase4_manifest_hash": economic_evaluation.get("phase4_manifest_hash"),
                }
            ),
            "validation": _document(
                {"status": "PASS", "fold_count": len(calibrations), "all_folds_evaluated": True}
            ),
        }


def _parquet(frame: pd.DataFrame) -> ArtifactContent:
    table = pa.Table.from_pandas(frame, preserve_index=False)
    buffer = io.BytesIO()
    pq.write_table(table, buffer, compression="zstd")
    return buffer.getvalue(), "application/vnd.apache.parquet", tuple(table.column_names)


def _document(value: dict[str, object]) -> ArtifactContent:
    return json.dumps(value, sort_keys=True, default=str).encode(), "application/json", ()


def _period(frame: pd.DataFrame, partition: str) -> tuple[str, str]:
    selected = pd.to_datetime(
        frame.loc[frame["partition"].eq(partition), "formation_date"], utc=True
    )
    if selected.empty:
        raise DataQualityError(f"No {partition} observations exist for model-card identity")
    return str(selected.min()), str(selected.max())


def _metric_stability(evaluations: list[dict[str, object]]) -> dict[str, dict[str, float]]:
    values: dict[str, list[float]] = {}
    for evaluation in evaluations:
        metrics = cast(dict[str, object], evaluation["metrics"])
        for name, value in metrics.items():
            if isinstance(value, (int, float)) and np.isfinite(value):
                values.setdefault(name, []).append(float(value))
    return {
        name: {
            "mean": float(np.mean(observations)),
            "standard_deviation": (
                float(np.std(observations, ddof=1)) if len(observations) > 1 else 0.0
            ),
            "minimum": float(np.min(observations)),
            "maximum": float(np.max(observations)),
        }
        for name, observations in sorted(values.items())
    }


def _git_commit(root: Path) -> str:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=root, text=True, stderr=subprocess.DEVNULL
        ).strip()
    except (OSError, subprocess.CalledProcessError) as exc:
        raise EvidenceIntegrityError("ML research requires an available Git commit") from exc
