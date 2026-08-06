"""Authenticated Phase 5 dataset, training, evaluation, and publication service."""

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

from institutional_factor_platform.exceptions import DataQualityError, EvidenceIntegrityError
from institutional_factor_platform.factors.storage import FactorRepository
from institutional_factor_platform.ml.config import MachineLearningConfig
from institutional_factor_platform.ml.evaluation import (
    classification_metrics,
    ranking_metrics,
    regression_metrics,
)
from institutional_factor_platform.ml.features import add_interactions, assemble_factor_features
from institutional_factor_platform.ml.models import ResearchModel, Task, create_model
from institutional_factor_platform.ml.preprocessing import SafePreprocessor
from institutional_factor_platform.ml.publication import MLManifest, publish_bundle
from institutional_factor_platform.ml.splits import assign_and_purge, temporal_folds
from institutional_factor_platform.ml.targets import build_targets
from institutional_factor_platform.ml.validation import drift_report, linear_explanation
from institutional_factor_platform.research_outputs.storage import AssetPricingRepository

ArtifactContent = tuple[bytes, str, tuple[str, ...]]


class MLResearchService:
    def __init__(
        self,
        config: MachineLearningConfig,
        root: Path,
        factors: FactorRepository,
        pricing: AssetPricingRepository,
    ) -> None:
        self.config = config
        self.root = root.resolve()
        self.factors = factors
        self.pricing = pricing

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
        target_factor = (
            "rolling_volatility"
            if kind.startswith("future_") and "volatility" in kind
            else "excess_return"
        )
        source = factor_table.loc[
            factor_table["factor_id"].eq(target_factor),
            ["security_id", "date", "raw_value", "available_at"],
        ].rename(columns={"raw_value": "return"})
        target_kind = (
            "future_return" if kind in {"future_excess_return", "outperformance"} else kind
        )
        targets, spec = build_targets(
            source,
            kind=target_kind,
            horizon=horizon,
            threshold=self.config.target.threshold or 0,
            quantiles=self.config.target.quantiles,
        )
        if kind == "outperformance":
            targets["target"] = (targets["target"] > (self.config.target.threshold or 0)).astype(
                int
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
        assigned = assign_and_purge(dataset, folds[-1], purge=self.config.split.purge_overlaps)
        train = assigned.loc[assigned["partition"].eq("train")]
        validation = assigned.loc[assigned["partition"].eq("validation")]
        test = assigned.loc[assigned["partition"].eq("test")]
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
        test_x = processor.transform(test).to_numpy(float)
        train_y = train["target"].to_numpy(float)
        test_y = test["target"].to_numpy(float)
        kind, horizon = self.config.target.require_explicit()
        task: Task = (
            "classification"
            if kind in {"outperformance", "future_drawdown"}
            else "ranking"
            if "rank" in kind or "quantile" in kind
            else "regression"
        )
        parameters: dict[str, object] = (
            {"n_estimators": 100, "max_depth": 3} if family in {"random_forest", "xgboost"} else {}
        )
        model = create_model(
            family,
            task,
            feature_names,
            processor.identity(),
            cast(str, metadata["target_hash"]),
            seed=self.config.models.random_seed,
            threads=self.config.models.thread_limit,
            parameters=parameters,
        ).fit(train_x, train_y)
        prediction = model.predict(test_x, feature_names)
        prediction_frame = test[
            ["security_id", "formation_date", "decision_time", "feature_coverage"]
        ].copy()
        prediction_frame["prediction"] = prediction
        prediction_frame["model_id"] = model.model_id
        prediction_frame["authentication_status"] = "PASS"
        if task == "classification":
            probability = model.predict_probability(test_x, feature_names)
            prediction_frame["probability"] = probability
            metrics: dict[str, object] = classification_metrics(test_y, probability)
        else:
            metrics = dict(regression_metrics(test_y, prediction))
            metrics.update(
                ranking_metrics(
                    prediction_frame.assign(target=test_y),
                    target="target",
                    prediction="prediction",
                )
            )
        if family in {"linear", "ridge", "lasso", "elastic_net", "logistic"}:
            explanations = linear_explanation(model)
        else:
            native = getattr(model.estimator, "feature_importances_", np.zeros(len(feature_names)))
            explanations = pd.DataFrame(
                {"feature": feature_names, "native_importance": np.asarray(native, dtype=float)}
            )
        drift = drift_report(train, test, feature_names, bins=self.config.drift.psi_bins)
        contents = self._bundle_contents(
            assigned,
            processor,
            model,
            prediction_frame,
            metrics,
            explanations,
            drift,
            len(validation_x),
            horizon,
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

    def _bundle_contents(
        self,
        assigned: pd.DataFrame,
        processor: SafePreprocessor,
        model: ResearchModel,
        predictions: pd.DataFrame,
        metrics: dict[str, object],
        explanations: pd.DataFrame,
        drift: pd.DataFrame,
        validation_rows: int,
        horizon: int,
    ) -> dict[str, ArtifactContent]:
        processor_buffer = io.BytesIO()
        joblib.dump(processor, processor_buffer)
        feature_columns = [*processor.feature_names, "security_id", "formation_date"]
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
                {"trials": [], "selection": "explicit bounded specification"}
            ),
            "predictions": _parquet(predictions),
            "evaluation": _document({"metrics": metrics}),
            "calibration": _document(
                {"method": self.config.calibration.method, "validation_rows": validation_rows}
            ),
            "explanations": _parquet(explanations),
            "drift": _parquet(drift),
            "comparison": _document({"status": "challenger comparison required per empirical run"}),
            "economic_evaluation": _document(
                {
                    "enabled": self.config.economic_evaluation.enabled,
                    "status": "delegated to Phase 4; explicit costs required",
                }
            ),
            "model_card": _document(
                {
                    "status": "EXPERIMENTAL",
                    "horizon": horizon,
                    "limitations": [
                        "No empirical validation",
                        "Explanations are not causal",
                        "Not for live trading",
                    ],
                }
            ),
            "configuration": _document(self.config.model_dump(mode="json")),
            "lineage": _document({"source": "authenticated Phase 2/3 publications"}),
            "validation": _document({"status": "PASS"}),
        }


def _parquet(frame: pd.DataFrame) -> ArtifactContent:
    table = pa.Table.from_pandas(frame, preserve_index=False)
    buffer = io.BytesIO()
    pq.write_table(table, buffer, compression="zstd")
    return buffer.getvalue(), "application/vnd.apache.parquet", tuple(table.column_names)


def _document(value: dict[str, object]) -> ArtifactContent:
    return json.dumps(value, sort_keys=True, default=str).encode(), "application/json", ()


def _git_commit(root: Path) -> str:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=root, text=True, stderr=subprocess.DEVNULL
        ).strip()
    except (OSError, subprocess.CalledProcessError) as exc:
        raise EvidenceIntegrityError("ML research requires an available Git commit") from exc
