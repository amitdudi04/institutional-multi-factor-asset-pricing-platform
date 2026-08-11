"""Phase 5 deterministic software and adversarial integrity tests."""

import hashlib
import io
import json
from datetime import UTC, date, datetime, timedelta
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
import pytest
from pydantic import ValidationError

from institutional_factor_platform.backtest.costs import TransactionCostModel
from institutional_factor_platform.exceptions import (
    ConfigurationError,
    DataQualityError,
    EvidenceIntegrityError,
    PublicationConflictError,
    TemporalIntegrityError,
)
from institutional_factor_platform.ml.config import MachineLearningConfig, load_ml_config
from institutional_factor_platform.ml.contracts import (
    ExplanationRecord,
    FeatureDefinition,
    FeatureSchema,
    ModelCard,
    PredictionRecord,
    TargetSpecification,
)
from institutional_factor_platform.ml.economic import evaluate_ranked_signal
from institutional_factor_platform.ml.evaluation import (
    block_bootstrap_ic,
    calibration_error,
    classification_metrics,
    ranking_metrics,
    regression_metrics,
)
from institutional_factor_platform.ml.features import add_interactions, assemble_factor_features
from institutional_factor_platform.ml.models import ResearchModel, create_model
from institutional_factor_platform.ml.preprocessing import SafePreprocessor, cross_sectional_median
from institutional_factor_platform.ml.publication import (
    REQUIRED_ARTIFACTS,
    MLRepository,
    publish_bundle,
)
from institutional_factor_platform.ml.service import MLResearchService
from institutional_factor_platform.ml.splits import (
    assign_and_purge,
    reject_random_financial_split,
    temporal_folds,
)
from institutional_factor_platform.ml.targets import build_targets
from institutional_factor_platform.ml.validation import (
    bounded_grid_search,
    calibrate_classifier,
    drift_report,
    feature_family_ablations,
    linear_explanation,
    tree_explanations,
)


def _factor_frame(periods: int = 30, securities: int = 8) -> pd.DataFrame:
    rows = []
    start = date(2020, 1, 1)
    for period in range(periods):
        current = start + timedelta(days=period)
        available = datetime.combine(current, datetime.min.time(), tzinfo=UTC) + timedelta(hours=12)
        for number in range(securities):
            security = f"sec_{number:032d}"
            values = {
                "value_score": number / 10 + period / 100,
                "momentum_score": np.sin((number + period) / 5),
                "excess_return": 0.001 * (number - 3) + 0.0001 * period,
                "rolling_volatility": 0.01 + number / 1000,
            }
            for factor_id, raw in values.items():
                rows.append(
                    {
                        "security_id": security,
                        "date": current,
                        "factor_id": factor_id,
                        "raw_value": raw,
                        "winsorized_value": raw,
                        "normalized_value": raw,
                        "score_value": raw,
                        "normalization_method": "fixture",
                        "available_at": available,
                        "factor_version": "fixture-v1",
                    }
                )
    return pd.DataFrame(rows)


def _returns(periods: int = 30, securities: int = 8) -> pd.DataFrame:
    factors = _factor_frame(periods, securities)
    return factors.loc[
        factors["factor_id"].eq("excess_return"),
        ["security_id", "date", "raw_value", "available_at"],
    ].rename(columns={"raw_value": "return"})


def _explicit_config(tmp_path: Path | None = None) -> MachineLearningConfig:
    base = load_ml_config()
    publication = base.publication
    if tmp_path is not None:
        publication = publication.model_copy(
            update={"output_root": Path("outputs"), "manifest_root": Path("manifests")}
        )
    return base.model_copy(
        update={
            "features": base.features.model_copy(
                update={"families": ("value_score", "momentum_score"), "minimum_coverage": 1.0}
            ),
            "target": base.target.model_copy(update={"kind": "future_return", "horizon": 1}),
            "split": base.split.model_copy(
                update={
                    "method": "expanding",
                    "train_periods": 10,
                    "validation_periods": 4,
                    "test_periods": 3,
                    "embargo_periods": 0,
                }
            ),
            "publication": publication,
        }
    )


def test_configuration_keeps_owner_decisions_open_and_strict(tmp_path: Path) -> None:
    base = load_ml_config()
    assert base.schema_version == "1.0.0"
    assert len(base.canonical_hash()) == 64
    with pytest.raises(ConfigurationError, match="open owner decisions"):
        base.target.require_explicit()
    assert _explicit_config().target.require_explicit() == ("future_return", 1)
    with pytest.raises(ValidationError):
        base.model_copy(update={"unknown": True}).__class__.model_validate(
            {**base.model_dump(), "unknown": True}
        )
    invalid = tmp_path / "ml.yaml"
    invalid.write_text("schema_version: nope", encoding="utf-8")
    with pytest.raises(ConfigurationError):
        load_ml_config(invalid)
    with pytest.raises(ValidationError):
        base.preprocessing.model_copy(
            update={"winsor_lower": 0.4, "winsor_upper": 0.2}
        ).__class__.model_validate(
            {**base.preprocessing.model_dump(), "winsor_lower": 0.4, "winsor_upper": 0.2}
        )


def test_feature_contract_order_availability_and_interactions() -> None:
    frame = _factor_frame()
    features, schema, report = assemble_factor_features(
        frame,
        ("value_score", "momentum_score"),
        "score_value",
        source_publication_id="phase2",
        minimum_coverage=1.0,
    )
    assert schema.features[0].name == "momentum_score"
    assert report["excluded_rows"] == 0
    interacted = add_interactions(features, (("value_score", "momentum_score"),))
    assert "value_score__x__momentum_score" in interacted
    with pytest.raises(DataQualityError):
        add_interactions(features, (("future_return", "value_score"),))
    with pytest.raises(DataQualityError):
        assemble_factor_features(
            frame, (), "score_value", source_publication_id="p", minimum_coverage=0
        )
    leaked = frame.copy()
    leaked.loc[0, "available_at"] = pd.Timestamp("2030-01-01", tz="UTC")
    with pytest.raises(TemporalIntegrityError):
        assemble_factor_features(
            leaked, ("value_score",), "raw_value", source_publication_id="p", minimum_coverage=0
        )
    duplicated = pd.concat([frame, frame.iloc[[0]]])
    with pytest.raises(DataQualityError, match="duplicate"):
        assemble_factor_features(
            duplicated, ("value_score",), "raw_value", source_publication_id="p", minimum_coverage=0
        )


def test_feature_schema_rejects_duplicate_and_reordered() -> None:
    definition = FeatureDefinition(
        name="b",
        family="value",
        definition="x",
        rationale="x",
        source="p",
        unit="score",
        direction=0,
        availability_policy="past",
        transformation_chain=("raw",),
        missingness_policy="reject",
        fitted_state_scope="none",
        version="1",
    )
    with pytest.raises(ValidationError, match="deterministic"):
        FeatureSchema(
            schema_version="1.0.0",
            feature_set_version="1",
            features=(definition, definition.model_copy(update={"name": "a"})),
        )
    with pytest.raises(ValidationError, match="duplicate"):
        FeatureSchema(
            schema_version="1.0.0", feature_set_version="1", features=(definition, definition)
        )


@pytest.mark.parametrize(
    "kind,unit",
    [
        ("future_return", "decimal_return"),
        ("percentile_rank", "rank"),
        ("ordinal_rank", "rank"),
        ("quantile_bucket", "rank"),
        ("outperformance", "binary"),
    ],
)
def test_target_construction_is_explicit_and_separate(kind: str, unit: str) -> None:
    frame = _returns()
    if kind == "outperformance":
        frame["benchmark_return"] = 0.0
    targets, spec = build_targets(
        frame, kind=kind, horizon=2, benchmark_id="SP500-TR" if kind == "outperformance" else None
    )
    assert not targets.empty and spec.unit == unit
    assert (targets["formation_date"] < targets["target_start"]).all()
    assert (targets["target_start"] <= targets["target_end"]).all()
    if kind == "outperformance":
        assert set(targets["target"]).issubset({0, 1})


def test_target_rejects_bad_identity_and_benchmark() -> None:
    frame = _returns()
    with pytest.raises(DataQualityError, match="benchmark"):
        build_targets(frame, kind="future_excess_return", horizon=1, benchmark_id="SP500-TR")
    with pytest.raises(DataQualityError, match="duplicate"):
        build_targets(pd.concat([frame, frame.iloc[[0]]]), kind="future_return", horizon=1)
    invalid = frame.copy()
    invalid.loc[invalid.index[0], "available_at"] = pd.Timestamp("2019-01-01", tz="UTC")
    with pytest.raises(TemporalIntegrityError):
        build_targets(invalid, kind="future_return", horizon=1)


def test_risk_targets_match_hand_calculations_and_preserve_source_identity() -> None:
    dates = pd.date_range("2024-01-01", periods=4, tz="UTC")
    frame = pd.DataFrame(
        {
            "security_id": ["security"] * 4,
            "date": dates,
            "return": [0.01, -0.02, 0.03, -0.01],
            "available_at": dates + pd.Timedelta(hours=12),
        }
    )
    checksum = "c" * 64
    volatility, vol_spec = build_targets(
        frame,
        kind="future_volatility",
        horizon=3,
        annualization_periods=252,
        source_publication_id="market-source",
        source_artifact_checksum=checksum,
    )
    window = np.array([-0.02, 0.03, -0.01])
    assert volatility.loc[0, "target"] == pytest.approx(window.std(ddof=1) * np.sqrt(252))
    assert vol_spec.source_publication_id == "market-source"
    assert vol_spec.source_artifact_checksum == checksum

    downside, _ = build_targets(
        frame, kind="future_downside_volatility", horizon=3, annualization_periods=252
    )
    assert downside.loc[0, "target"] == pytest.approx(
        np.sqrt(np.mean(np.minimum(window, 0.0) ** 2)) * np.sqrt(252)
    )
    drawdown, _ = build_targets(frame, kind="future_drawdown", horizon=3)
    wealth = np.cumprod(1 + window)
    prior_peaks = np.maximum.accumulate(np.r_[1.0, wealth])[:-1]
    assert drawdown.loc[0, "target"] == pytest.approx(np.min(wealth / prior_peaks - 1))
    risk_quantile, _ = build_targets(
        frame, kind="future_risk_quantile", horizon=3, risk_quantile_alpha=0.05
    )
    assert risk_quantile.loc[0, "target"] == pytest.approx(max(0.0, -np.quantile(window, 0.05)))


def _dataset() -> pd.DataFrame:
    features, _, _ = assemble_factor_features(
        _factor_frame(),
        ("value_score", "momentum_score"),
        "score_value",
        source_publication_id="phase2",
        minimum_coverage=1,
    )
    targets, _ = build_targets(_returns(), kind="future_return", horizon=1)
    return features.merge(targets, on=["security_id", "formation_date"])


def test_temporal_splits_purge_embargo_and_reject_random() -> None:
    data = _dataset()
    folds = temporal_folds(
        data,
        method="expanding",
        train_periods=10,
        validation_periods=4,
        test_periods=3,
        embargo_periods=0,
    )
    assigned = assign_and_purge(data, folds[0])
    assert {"train", "validation", "test", "purged"}.issubset(set(assigned["partition"]))
    rolling = temporal_folds(
        data,
        method="rolling",
        train_periods=10,
        validation_periods=4,
        test_periods=3,
        rolling_periods=8,
    )
    assert len(rolling[0].train_dates) == 8
    assert temporal_folds(
        data, method="holdout", train_periods=10, validation_periods=4, test_periods=3
    )
    with pytest.raises(TemporalIntegrityError, match="Random"):
        reject_random_financial_split("shuffle")
    with pytest.raises(DataQualityError, match="Insufficient"):
        temporal_folds(
            data.head(8), method="holdout", train_periods=10, validation_periods=4, test_periods=3
        )


def test_training_only_preprocessing_and_schema_identity() -> None:
    data = _dataset()
    names = ("momentum_score", "value_score")
    train = data.iloc[:80].copy()
    train.loc[train.index[0], "value_score"] = np.nan
    end = pd.to_datetime(train["formation_date"], utc=True).max()
    processor = SafePreprocessor(names, "training_median", "standard", 0.05, 0.95).fit(
        train, pd.to_datetime(train["formation_date"], utc=True), allowed_training_end=end
    )
    transformed = processor.transform(train)
    assert transformed.shape == (len(train), 2) and len(processor.identity()) == 64
    with pytest.raises(TemporalIntegrityError):
        SafePreprocessor(names, "reject", "none").fit(
            train.fillna(0), train["formation_date"], allowed_training_end=end - timedelta(days=1)
        )
    with pytest.raises(DataQualityError, match="order"):
        processor.transform(train[["value_score", "momentum_score"]])
    cross = train.copy()
    cross.loc[cross.index[0], "value_score"] = np.nan
    assert (
        not cross_sectional_median(cross, names, cross["formation_date"])["value_score"]
        .isna()
        .any()
    )


def _arrays() -> tuple[np.ndarray, np.ndarray, tuple[str, ...]]:
    rng = np.random.default_rng(7)
    x = rng.normal(size=(120, 3))
    y = 0.5 * x[:, 0] - 0.2 * x[:, 1] + rng.normal(scale=0.05, size=120)
    return x, y, ("a", "b", "c")


@pytest.mark.parametrize(
    "family",
    [
        "zero",
        "historical_mean",
        "factor_composite",
        "linear",
        "ridge",
        "lasso",
        "elastic_net",
        "random_forest",
        "xgboost",
    ],
)
def test_regression_model_families_reproducible(family: str) -> None:
    x, y, names = _arrays()
    params = (
        {"n_estimators": 10, "max_depth": 2}
        if family in {"random_forest", "xgboost"}
        else (
            {"alpha": 0.1}
            if family in {"ridge", "lasso"}
            else ({"alpha": 0.1, "l1_ratio": 0.5} if family == "elastic_net" else {})
        )
    )
    first = create_model(
        family, "regression", names, "a" * 64, "b" * 64, seed=3, parameters=params
    ).fit(x, y)
    second = create_model(
        family, "regression", names, "a" * 64, "b" * 64, seed=3, parameters=params
    ).fit(x, y)
    np.testing.assert_allclose(first.predict(x, names), second.predict(x, names))
    with pytest.raises(EvidenceIntegrityError):
        first.predict(x, tuple(reversed(names)))


@pytest.mark.parametrize("family", ["logistic", "random_forest", "xgboost"])
def test_classification_models_produce_probabilities(family: str) -> None:
    x, y, names = _arrays()
    binary = (y > np.median(y)).astype(float)
    params = {"n_estimators": 10, "max_depth": 2} if family != "logistic" else {}
    model = create_model(
        family, "classification", names, "a" * 64, "b" * 64, seed=4, parameters=params
    ).fit(x, binary)
    probability = model.predict_probability(x, names)
    assert ((probability >= 0) & (probability <= 1)).all()
    assert classification_metrics(binary, probability)["roc_auc"] is not None
    with pytest.raises(DataQualityError, match="two"):
        create_model(
            family, "classification", names, "a" * 64, "b" * 64, seed=4, parameters=params
        ).fit(x, np.ones(len(x)))


def test_model_serialization_authenticates_before_load() -> None:
    x, y, names = _arrays()
    model = create_model("ridge", "regression", names, "a" * 64, "b" * 64, seed=2).fit(x, y)
    content = model.trusted_bytes()
    checksum = hashlib.sha256(content).hexdigest()
    assert ResearchModel.load_trusted(content, checksum).model_id == model.model_id
    with pytest.raises(EvidenceIntegrityError, match="checksum"):
        ResearchModel.load_trusted(content + b"attack", checksum)
    with pytest.raises(DataQualityError):
        create_model("unknown", "regression", names, "a" * 64, "b" * 64, seed=1)


def test_metrics_ranking_bootstrap_and_undefined_handling() -> None:
    _, y, _ = _arrays()
    prediction = y + 0.01
    metrics = regression_metrics(y, prediction)
    assert metrics["spearman"] > 0.9  # type: ignore[operator]
    frame = pd.DataFrame(
        {
            "formation_date": np.repeat(pd.date_range("2020-01-01", periods=6), 10),
            "security_id": [f"s{i}" for _ in range(6) for i in range(10)],
            "target": y[:60],
            "prediction": prediction[:60],
        }
    )
    assert ranking_metrics(frame)["spearman"] is not None
    interval = block_bootstrap_ic(frame, block_length=2, resamples=20, seed=1)
    assert interval["lower"] is not None
    assert calibration_error(np.array([0.0, 1.0]), np.array([0.1, 0.9])) < 0.2
    with pytest.raises(DataQualityError):
        regression_metrics(np.array([]), np.array([]))


def test_bounded_tuning_never_receives_test_data() -> None:
    x, y, names = _arrays()
    model, trials = bounded_grid_search(
        "ridge",
        "regression",
        names,
        "a" * 64,
        "b" * 64,
        x[:80],
        y[:80],
        x[80:100],
        y[80:100],
        {"alpha": (0.01, 0.1, 1.0)},
        maximum_trials=2,
        seed=4,
    )
    assert model.family == "ridge" and len(trials) == 2 and all(x.status == "PASS" for x in trials)
    with pytest.raises(DataQualityError):
        bounded_grid_search(
            "ridge",
            "regression",
            names,
            "a" * 64,
            "b" * 64,
            x[:80],
            y[:80],
            x[80:100],
            y[80:100],
            {},
            maximum_trials=2,
            seed=4,
        )


def test_calibration_explainability_and_future_background_rejection() -> None:
    x, y, names = _arrays()
    binary = (y > 0).astype(float)
    classifier = create_model("logistic", "classification", names, "a" * 64, "b" * 64, seed=1).fit(
        x[:80], binary[:80]
    )
    calibrated = calibrate_classifier(
        classifier,
        x[80:100],
        binary[80:100],
        method="sigmoid",
        validation_end=pd.Timestamp("2020-02-01"),
        test_start=pd.Timestamp("2020-03-01"),
    )
    assert calibrated.predict_proba(x[100:])[:, 1].shape == (20,)
    isotonic = calibrate_classifier(
        classifier,
        x[80:100],
        binary[80:100],
        method="isotonic",
        validation_end=pd.Timestamp("2020-02-01"),
        test_start=pd.Timestamp("2020-03-01"),
    )
    assert isotonic.predict_proba(x[100:])[:, 1].shape == (20,)
    with pytest.raises(TemporalIntegrityError):
        calibrate_classifier(
            classifier,
            x[80:100],
            binary[80:100],
            method="sigmoid",
            validation_end=pd.Timestamp("2020-04-01"),
            test_start=pd.Timestamp("2020-03-01"),
        )
    linear = create_model("linear", "regression", names, "a" * 64, "b" * 64, seed=1).fit(x, y)
    assert len(linear_explanation(linear)) == 3
    forest = create_model(
        "random_forest",
        "regression",
        names,
        "a" * 64,
        "b" * 64,
        seed=1,
        parameters={"n_estimators": 10, "max_depth": 2},
    ).fit(x[:80], y[:80])
    dates = pd.Series(pd.date_range("2020-01-01", periods=20))
    permutation, shap_values, background = tree_explanations(
        forest,
        x[:20],
        x[80:85],
        y[80:100],
        x[80:100],
        background_dates=dates,
        training_end=pd.Timestamp("2020-02-01"),
        seed=1,
    )
    assert permutation.shape[0] == 3 and shap_values.shape == (5, 3) and len(background) == 64
    with pytest.raises(TemporalIntegrityError):
        tree_explanations(
            forest,
            x[:20],
            x[80:85],
            y[80:100],
            x[80:100],
            background_dates=dates,
            training_end=pd.Timestamp("2020-01-10"),
            seed=1,
        )


def test_drift_and_ablation_reports() -> None:
    x, _, names = _arrays()
    left = pd.DataFrame(x[:60], columns=names)
    right = pd.DataFrame(x[60:] + 0.2, columns=names)
    report = drift_report(left, right, names, bins=5)
    assert set(report.columns) >= {"psi", "ks", "wasserstein"}
    ablations = feature_family_ablations(names, {"first": ("a",), "second": ("b",)})
    assert ablations["without_first"] == ("b", "c")
    with pytest.raises(DataQualityError):
        feature_family_ablations(("a",), {"all": ("a",)})


def test_economic_evaluation_uses_phase4_timing_costs_and_long_only() -> None:
    dates = pd.date_range("2020-01-31", periods=8, freq="ME")
    returns = pd.DataFrame({"A": 0.01, "B": 0.005, "C": 0.0}, index=dates)
    benchmark = pd.Series(0.003, index=dates)
    predictions = pd.DataFrame(
        [
            {
                "formation_date": d,
                "security_id": s,
                "prediction": p,
                "authentication_status": "PASS",
            }
            for d in dates
            for s, p in zip(("A", "B", "C"), (3.0, 2.0, 1.0), strict=True)
        ]
    )
    result = evaluate_ranked_signal(
        predictions,
        returns,
        benchmark,
        TransactionCostModel(1, 2, 1, 0),
        selection_fraction=1 / 3,
        window=3,
    )
    assert (result.allocations["weight"] >= 0).all() and result.returns[
        "transaction_cost"
    ].sum() > 0
    with pytest.raises(DataQualityError, match="Unauthenticated"):
        evaluate_ranked_signal(
            predictions.assign(authentication_status="FAIL"),
            returns,
            benchmark,
            TransactionCostModel(0, 0, 0, 0),
            selection_fraction=0.5,
            window=3,
        )


def _parquet_bytes() -> tuple[bytes, tuple[str, ...]]:
    table = pa.table({"value": [1.0]})
    buffer = io.BytesIO()
    pq.write_table(table, buffer)
    return buffer.getvalue(), tuple(table.column_names)


def test_immutable_publication_restart_model_load_and_tamper(tmp_path: Path) -> None:
    x, y, names = _arrays()
    model = create_model("ridge", "regression", names, "c" * 64, "d" * 64, seed=8).fit(x, y)
    parquet, columns = _parquet_bytes()
    contents = {}
    for name in REQUIRED_ARTIFACTS:
        if name == "model":
            contents[name] = (model.trusted_bytes(), "application/x-joblib", ())
        elif name in {
            "feature_matrix",
            "targets",
            "splits",
            "predictions",
            "explanations",
            "drift",
            "comparison",
        }:
            contents[name] = (parquet, "application/vnd.apache.parquet", columns)
        else:
            contents[name] = (
                json.dumps({"status": "PASS"}, sort_keys=True).encode(),
                "application/json",
                (),
            )
    values = {
        "phase2_publication_id": "phase2",
        "phase2_manifest_hash": "a" * 64,
        "phase3_publication_id": "phase3",
        "phase3_manifest_hash": "b" * 64,
        "configuration_hash": "e" * 64,
        "git_commit": "deadbeef",
        "model_id": model.model_id,
        "feature_schema_hash": "f" * 64,
        "target_hash": "d" * 64,
        "preprocessor_hash": "c" * 64,
        "random_seed": 8,
        "dependency_versions": {"numpy": np.__version__},
        "validation_status": "PASS",
    }
    first = publish_bundle(tmp_path, Path("outputs"), Path("manifests"), values, contents)
    second = publish_bundle(tmp_path, Path("outputs"), Path("manifests"), values, contents)
    repository = MLRepository(tmp_path, tmp_path / "manifests")
    assert (
        first.publication_id == second.publication_id
        and repository.load_model(first.publication_id).model_id == model.model_id
    )
    artifact = next(x for x in first.artifacts if x.name == "predictions")
    path = tmp_path / artifact.path
    path.write_bytes(path.read_bytes() + b"attack")
    with pytest.raises(EvidenceIntegrityError, match="changed"):
        repository.authenticate(first.publication_id)
    assert repository.list_authenticated() == ()
    with pytest.raises(EvidenceIntegrityError, match="incomplete"):
        publish_bundle(tmp_path, Path("o2"), Path("m2"), values, {})

    for target_name in (
        "model",
        "predictions",
        "calibration",
        "explanations",
        "model_card",
        "economic_evaluation",
    ):
        output_root = Path(f"tamper-{target_name}-outputs")
        manifest_root = Path(f"tamper-{target_name}-manifests")
        manifest = publish_bundle(tmp_path, output_root, manifest_root, values, contents)
        target_artifact = next(item for item in manifest.artifacts if item.name == target_name)
        target_path = tmp_path / target_artifact.path
        target_path.write_bytes(target_path.read_bytes() + b"attack")
        with pytest.raises(EvidenceIntegrityError, match="changed"):
            MLRepository(tmp_path, tmp_path / manifest_root).authenticate(manifest.publication_id)


def test_prediction_explanation_and_model_card_contracts() -> None:
    now = datetime.now(UTC)
    target = TargetSpecification(
        schema_version="1.0.0",
        target_type="future_return",
        horizon=1,
        benchmark_id=None,
        unit="decimal_return",
        transformation="future",
    )
    prediction = PredictionRecord(
        model_id="m",
        run_id="r",
        security_id="s",
        formation_date=now,
        decision_time=now,
        horizon=1,
        target_type="future_return",
        prediction=0.1,
        feature_coverage=1,
        mapping_status="VALID",
        model_version="1",
        feature_schema_hash="a" * 64,
        configuration_hash="b" * 64,
        git_commit="deadbeef",
        prediction_available_at=now,
    )
    assert len(prediction.content_hash()) == 64
    explanation = ExplanationRecord(
        model_id="m",
        model_checksum="a" * 64,
        prediction_checksum="b" * 64,
        preprocessing_hash="c" * 64,
        feature_schema_hash="d" * 64,
        feature_matrix_hash="e" * 64,
        security_id="s",
        formation_date=now,
        method="shap",
        library_version="0.51",
        background_hash="f" * 64,
        configuration_hash="1" * 64,
        seed=1,
        git_commit="deadbeef",
    )
    assert explanation.method == "shap"
    card = ModelCard(
        schema_version="1.0.0",
        model_id="m",
        family="ridge",
        task="regression",
        target=target,
        intended_use="research",
        prohibited_use="live trading",
        universe="synthetic fixture",
        training_period=("2020", "2021"),
        validation_period=("2022", "2022"),
        test_period=("2023", "2023"),
        features=("a",),
        preprocessing_hash="a" * 64,
        hyperparameters={},
        seed=1,
        metrics={},
        economic_evaluation={},
        explanations={"causal": False},
        drift={},
        limitations=("No empirical validation",),
        known_failure_modes=("drift",),
        data_dependencies=("phase2",),
        artifact_checksums={},
        configuration_hash="b" * 64,
        git_commit="deadbeef",
        status="EXPERIMENTAL",
    )
    assert card.status == "EXPERIMENTAL"
    with pytest.raises(ValidationError):
        card.model_copy(update={"status": "production"}).__class__.model_validate(
            {**card.model_dump(), "status": "production"}
        )


class _Factors:
    def __init__(self) -> None:
        self.frame = pa.Table.from_pandas(_factor_frame(), preserve_index=False)

    def authenticate(self, publication_id: str) -> SimpleNamespace:
        assert publication_id == "phase2"
        return SimpleNamespace(
            publication_id="phase2",
            content_hash=lambda: "a" * 64,
            market_source_dataset_ids=("market-source",),
            parents=(SimpleNamespace(dataset_id="market-source", artifact_checksum="c" * 64),),
        )

    def read_table(self, publication_id: str) -> pa.Table:
        self.authenticate(publication_id)
        return self.frame


class _Pricing:
    def authenticate(self, publication_id: str) -> SimpleNamespace:
        assert publication_id == "phase3"
        return SimpleNamespace(
            publication_id="phase3",
            phase2_publication_id="phase2",
            phase2_manifest_hash="a" * 64,
            content_hash=lambda: "b" * 64,
        )


class _Phase1:
    values = _returns().assign(benchmark_return=0.0)
    frame = pa.Table.from_pandas(values, preserve_index=False)

    def get(self, dataset_id: str) -> SimpleNamespace:
        assert dataset_id == "market-source"
        return SimpleNamespace(
            dataset_id=dataset_id,
            checksum="c" * 64,
            unit_metadata={"return": "decimal_return"},
        )

    def read_table(self, dataset_id: str) -> pa.Table:
        self.get(dataset_id)
        return self.frame


class _Portfolios:
    def __init__(self, root: Path) -> None:
        self.path = root / "phase4-configuration.json"
        self.path.write_text(
            json.dumps(
                {
                    "configuration": {
                        "costs": {
                            "commission_bps": 1.0,
                            "spread_bps": 2.0,
                            "slippage_bps": 1.0,
                            "market_impact_coefficient": 0.0,
                        }
                    }
                }
            ),
            "utf-8",
        )

    def authenticate(self, publication_id: str) -> SimpleNamespace:
        assert publication_id == "phase4"
        return SimpleNamespace(
            publication_id="phase4",
            phase2_publication_id="phase2",
            phase2_manifest_hash="a" * 64,
            phase3_publication_id="phase3",
            phase3_manifest_hash="b" * 64,
            configuration_hash="e" * 64,
            artifacts=(SimpleNamespace(name="configuration", path=self.path.name),),
            content_hash=lambda: "d" * 64,
        )


def test_service_accepts_only_connected_authenticated_repositories(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(
        "institutional_factor_platform.ml.service._git_commit", lambda root: "deadbeef"
    )
    service = MLResearchService(_explicit_config(), tmp_path, _Factors(), _Pricing(), _Phase1())  # type: ignore[arg-type]
    dataset, metadata = service.build_authenticated_dataset("phase3")
    assert not dataset.empty and metadata["phase2_publication_id"] == "phase2"
    assert (dataset.groupby("formation_date")["target"].nunique() > 1).any()
    assert metadata["target_source_dataset_id"] == "market-source"
    broken = _Pricing()
    broken.authenticate = lambda publication_id: SimpleNamespace(
        publication_id="phase3",
        phase2_publication_id="phase2",
        phase2_manifest_hash="0" * 64,
        content_hash=lambda: "b" * 64,
    )  # type: ignore[method-assign]
    with pytest.raises(EvidenceIntegrityError, match="lineage"):
        MLResearchService(
            _explicit_config(), tmp_path, _Factors(), broken, _Phase1()
        ).build_authenticated_dataset("phase3")  # type: ignore[arg-type]


def test_service_trains_publishes_and_restarts_authenticated_bundle(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(
        "institutional_factor_platform.ml.service._git_commit", lambda root: "deadbeef"
    )
    service = MLResearchService(
        _explicit_config(tmp_path),
        tmp_path,
        _Factors(),  # type: ignore[arg-type]
        _Pricing(),  # type: ignore[arg-type]
        _Phase1(),  # type: ignore[arg-type]
    )
    first = service.train_evaluate_publish("phase3", "ridge")
    second = service.train_evaluate_publish("phase3", "ridge")
    assert first.publication_id == second.publication_id
    repository = MLRepository(tmp_path, tmp_path / "manifests")
    assert repository.load_model(first.publication_id).family == "ridge"
    authenticated = repository.authenticate(first.publication_id)
    artifacts = {item.name: item for item in authenticated.artifacts}
    evaluation = json.loads((tmp_path / artifacts["evaluation"].path).read_text("utf-8"))
    trials = json.loads((tmp_path / artifacts["hyperparameter_trials"].path).read_text("utf-8"))
    card = json.loads((tmp_path / artifacts["model_card"].path).read_text("utf-8"))
    split_table = pq.read_table(tmp_path / artifacts["splits"].path).to_pandas()
    prediction_table = pq.read_table(tmp_path / artifacts["predictions"].path).to_pandas()
    assert evaluation["fold_count"] == split_table["fold"].nunique()
    assert prediction_table["fold"].nunique() == evaluation["fold_count"]
    assert {item["status"] for item in trials["trials"]} <= {
        "PASS",
        "FAIL",
        "REUSED_BY_RETRAINING_CADENCE",
    }
    assert card["target"]["source_publication_id"] == "market-source"
    assert card["training_period"] and card["test_period"]
    with pytest.raises(DataQualityError, match="not enabled"):
        service.train_evaluate_publish("phase3", "neural_network")


@pytest.mark.parametrize(("method", "minimum_folds"), (("holdout", 1), ("walk_forward", 2)))
def test_service_executes_remaining_temporal_split_modes(
    method: str,
    minimum_folds: int,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        "institutional_factor_platform.ml.service._git_commit", lambda root: "deadbeef"
    )
    base = _explicit_config(tmp_path)
    config = base.model_copy(
        update={
            "split": base.split.model_copy(update={"method": method}),
            "search": base.search.model_copy(update={"maximum_trials": 1}),
            "explainability": base.explainability.model_copy(update={"enabled": False}),
        }
    )
    manifest = MLResearchService(
        config,
        tmp_path,
        _Factors(),  # type: ignore[arg-type]
        _Pricing(),  # type: ignore[arg-type]
        _Phase1(),  # type: ignore[arg-type]
    ).train_evaluate_publish("phase3", "ridge")
    evaluation_artifact = next(item for item in manifest.artifacts if item.name == "evaluation")
    evaluation = json.loads((tmp_path / evaluation_artifact.path).read_text("utf-8"))
    assert evaluation["fold_count"] >= minimum_folds


@pytest.mark.parametrize(
    ("family", "classification"),
    (
        ("zero", False),
        ("historical_mean", False),
        ("factor_composite", False),
        ("linear", False),
        ("ridge", False),
        ("lasso", False),
        ("elastic_net", False),
        ("random_forest", False),
        ("xgboost", False),
        ("logistic", True),
        ("random_forest", True),
        ("xgboost", True),
    ),
)
def test_every_model_family_traverses_service_publication_boundary(
    family: str,
    classification: bool,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        "institutional_factor_platform.ml.service._git_commit", lambda root: "deadbeef"
    )
    base = _explicit_config(tmp_path)
    target = base.target.model_copy(
        update={
            "kind": "outperformance" if classification else "future_return",
            "benchmark_id": "SP500-TR" if classification else None,
        }
    )
    config = base.model_copy(
        update={
            "target": target,
            "split": base.split.model_copy(update={"method": "holdout"}),
            "models": base.models.model_copy(
                update={"enabled": tuple(sorted({*base.models.enabled, family}))}
            ),
            "search": base.search.model_copy(update={"maximum_trials": 1}),
            "calibration": base.calibration.model_copy(
                update={"method": "none", "minimum_samples": 10}
            ),
            "explainability": base.explainability.model_copy(update={"enabled": False}),
        }
    )
    manifest = MLResearchService(
        config,
        tmp_path,
        _Factors(),  # type: ignore[arg-type]
        _Pricing(),  # type: ignore[arg-type]
        _Phase1(),  # type: ignore[arg-type]
    ).train_evaluate_publish("phase3", family)
    assert (
        MLRepository(tmp_path, tmp_path / "manifests").load_model(manifest.publication_id).family
        == family
    )


def test_service_economic_evaluation_reuses_authenticated_phase4_engine_and_costs(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(
        "institutional_factor_platform.ml.service._git_commit", lambda root: "deadbeef"
    )
    base = _explicit_config(tmp_path)
    config = base.model_copy(
        update={
            "inputs": base.inputs.model_copy(update={"phase4_publication_id": "phase4"}),
            "economic_evaluation": base.economic_evaluation.model_copy(
                update={"enabled": True, "selection_quantile": 0.25}
            ),
        }
    )
    service = MLResearchService(
        config,
        tmp_path,
        _Factors(),  # type: ignore[arg-type]
        _Pricing(),  # type: ignore[arg-type]
        _Phase1(),  # type: ignore[arg-type]
        _Portfolios(tmp_path),  # type: ignore[arg-type]
    )
    manifest = service.train_evaluate_publish("phase3", "ridge")
    economic_artifact = next(
        item for item in manifest.artifacts if item.name == "economic_evaluation"
    )
    result = json.loads((tmp_path / economic_artifact.path).read_text("utf-8"))
    assert result["status"] == "PASS" and result["phase4_publication_id"] == "phase4"
    assert result["folds"] and all(item["long_only"] for item in result["folds"])
    assert all(item["reconciliation_status"] == "PASS" for item in result["folds"])
    assert result["costs"]["commission_bps"] == 1.0


def test_service_classifier_calibrates_only_on_validation_and_persists_identity(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(
        "institutional_factor_platform.ml.service._git_commit", lambda root: "deadbeef"
    )
    base = _explicit_config(tmp_path)
    config = base.model_copy(
        update={
            "target": base.target.model_copy(
                update={
                    "kind": "outperformance",
                    "benchmark_id": "SP500-TR",
                    "threshold": 0.0,
                }
            ),
            "models": base.models.model_copy(
                update={"enabled": (*base.models.enabled, "logistic")}
            ),
            "calibration": base.calibration.model_copy(
                update={"method": "sigmoid", "minimum_samples": 10}
            ),
        }
    )
    manifest = MLResearchService(
        config,
        tmp_path,
        _Factors(),  # type: ignore[arg-type]
        _Pricing(),  # type: ignore[arg-type]
        _Phase1(),  # type: ignore[arg-type]
    ).train_evaluate_publish("phase3", "logistic")
    artifacts = {item.name: item for item in manifest.artifacts}
    calibration = json.loads((tmp_path / artifacts["calibration"].path).read_text("utf-8"))
    predictions = pq.read_table(tmp_path / artifacts["predictions"].path).to_pandas()
    assert all(item["status"] == "PASS" for item in calibration["folds"])
    assert all(item["calibrator_id"] for item in calibration["folds"])
    assert predictions["probability"].between(0, 1).all()


def test_service_evaluates_all_rolling_folds_and_honors_retraining_cadence(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(
        "institutional_factor_platform.ml.service._git_commit", lambda root: "deadbeef"
    )
    base = _explicit_config(tmp_path)
    config = base.model_copy(
        update={
            "split": base.split.model_copy(
                update={"method": "rolling", "rolling_periods": 10, "retrain_every": 2}
            ),
            "search": base.search.model_copy(update={"maximum_trials": 1}),
        }
    )
    manifest = MLResearchService(
        config,
        tmp_path,
        _Factors(),  # type: ignore[arg-type]
        _Pricing(),  # type: ignore[arg-type]
        _Phase1(),  # type: ignore[arg-type]
    ).train_evaluate_publish("phase3", "ridge")
    artifacts = {item.name: item for item in manifest.artifacts}
    evaluation = json.loads((tmp_path / artifacts["evaluation"].path).read_text("utf-8"))
    trials = json.loads((tmp_path / artifacts["hyperparameter_trials"].path).read_text("utf-8"))
    predictions = pq.read_table(tmp_path / artifacts["predictions"].path).to_pandas()
    assert evaluation["fold_count"] > 1
    assert predictions["fold"].nunique() == evaluation["fold_count"]
    assert any(item["status"] == "REUSED_BY_RETRAINING_CADENCE" for item in trials["trials"])


def test_service_tree_model_persists_permutation_and_local_shap_evidence(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(
        "institutional_factor_platform.ml.service._git_commit", lambda root: "deadbeef"
    )
    base = _explicit_config(tmp_path)
    config = base.model_copy(
        update={
            "search": base.search.model_copy(update={"maximum_trials": 1}),
            "explainability": base.explainability.model_copy(
                update={"sample_size": 4, "background_size": 8}
            ),
        }
    )
    manifest = MLResearchService(
        config,
        tmp_path,
        _Factors(),  # type: ignore[arg-type]
        _Pricing(),  # type: ignore[arg-type]
        _Phase1(),  # type: ignore[arg-type]
    ).train_evaluate_publish("phase3", "random_forest")
    artifact = next(item for item in manifest.artifacts if item.name == "explanations")
    explanations = pq.read_table(tmp_path / artifact.path).to_pandas()
    assert {"permutation", "shap"} <= set(explanations["method"])
    assert explanations["prediction_artifact_checksum"].str.fullmatch(r"[a-f0-9]{64}").all()
    assert explanations["background_hash"].str.fullmatch(r"[a-f0-9]{64}").all()


def test_additional_fail_closed_contract_branches(tmp_path: Path) -> None:
    base = load_ml_config()
    with pytest.raises(ConfigurationError, match="Benchmark"):
        base.target.model_copy(
            update={"kind": "future_excess_return", "horizon": 5, "benchmark_id": None}
        ).require_explicit()
    with pytest.raises(ValidationError, match="Both winsorization"):
        base.preprocessing.__class__.model_validate(
            {**base.preprocessing.model_dump(), "winsor_lower": 0.05}
        )
    with pytest.raises(ValidationError, match="project-relative"):
        base.publication.__class__.model_validate(
            {"output_root": tmp_path.resolve(), "manifest_root": "manifests"}
        )
    with pytest.raises(DataQualityError, match="lacks"):
        assemble_factor_features(
            pd.DataFrame({"security_id": []}),
            ("value",),
            "raw_value",
            source_publication_id="p",
            minimum_coverage=0,
        )
    with pytest.raises(TemporalIntegrityError, match="future"):
        assemble_factor_features(
            _factor_frame(),
            ("future_alpha",),
            "raw_value",
            source_publication_id="p",
            minimum_coverage=0,
        )
    features, _, _ = assemble_factor_features(
        _factor_frame(),
        ("value_score", "momentum_score"),
        "raw_value",
        source_publication_id="p",
        minimum_coverage=0,
    )
    collision = add_interactions(features, (("value_score", "momentum_score"),))
    with pytest.raises(DataQualityError, match="collides"):
        add_interactions(collision, (("value_score", "momentum_score"),))


def test_additional_model_preprocessing_and_metric_guards() -> None:
    x, y, names = _arrays()
    baseline = create_model("historical_mean", "regression", names, "a" * 64, "b" * 64, seed=1)
    with pytest.raises(DataQualityError, match="not fitted"):
        baseline.predict(x, names)
    with pytest.raises(DataQualityError, match="empty or misaligned"):
        baseline.fit(x, y[:-1])
    regression = create_model("ridge", "regression", names, "a" * 64, "b" * 64, seed=1).fit(x, y)
    with pytest.raises(DataQualityError, match="Probability"):
        regression.predict_probability(x, names)
    processor = SafePreprocessor(names, "reject", "none")
    with pytest.raises(DataQualityError, match="not fitted"):
        processor.transform(pd.DataFrame(x, columns=names))
    missing = pd.DataFrame(x.copy(), columns=names)
    missing.loc[0, "a"] = np.nan
    with pytest.raises(DataQualityError, match="Missing"):
        processor.fit(
            missing,
            pd.Series(pd.date_range("2020-01-01", periods=len(x))),
            allowed_training_end=pd.Timestamp("2021-01-01", tz="UTC"),
        )
    native = SafePreprocessor(names, "native", "rank").fit(
        pd.DataFrame(x, columns=names),
        pd.Series(pd.date_range("2020-01-01", periods=len(x))),
        allowed_training_end=pd.Timestamp("2021-01-01", tz="UTC"),
    )
    assert native.transform(pd.DataFrame(x, columns=names)).notna().all().all()
    assert regression_metrics(np.ones(3), np.ones(3))["pearson"] is None
    with pytest.raises(DataQualityError, match="outside"):
        classification_metrics(np.array([0.0, 1.0]), np.array([-0.1, 1.1]))
    with pytest.raises(DataQualityError, match="Bootstrap"):
        block_bootstrap_ic(pd.DataFrame(), block_length=0, resamples=2, seed=1)


def test_additional_split_target_drift_and_explanation_guards() -> None:
    with pytest.raises(DataQualityError, match="lacks"):
        temporal_folds(
            pd.DataFrame(), method="holdout", train_periods=2, validation_periods=1, test_periods=1
        )
    data = _dataset()
    assert temporal_folds(
        data, method="walk_forward", train_periods=10, validation_periods=3, test_periods=2
    )
    with pytest.raises(DataQualityError, match="contract"):
        build_targets(pd.DataFrame(), kind="future_return", horizon=1)
    risk, spec = build_targets(_returns(), kind="future_volatility", horizon=3)
    assert not risk.empty and spec.unit == "annualized_volatility"
    with pytest.raises(DataQualityError, match="PSI"):
        drift_report(pd.DataFrame({"a": [1.0]}), pd.DataFrame({"a": [2.0]}), ("a",), bins=1)
    with pytest.raises(DataQualityError, match="empty"):
        drift_report(pd.DataFrame({"a": [np.nan]}), pd.DataFrame({"a": [2.0]}), ("a",))
    x, y, names = _arrays()
    forest = create_model(
        "random_forest",
        "regression",
        names,
        "a" * 64,
        "b" * 64,
        seed=1,
        parameters={"n_estimators": 5},
    ).fit(x, y)
    with pytest.raises(DataQualityError, match="coefficients"):
        linear_explanation(forest)
    with pytest.raises(EvidenceIntegrityError, match="schema"):
        tree_explanations(
            forest,
            x[:, :2],
            x[:2],
            y[:10],
            x[:10],
            background_dates=pd.Series(pd.date_range("2020-01-01", periods=len(x))),
            training_end=pd.Timestamp("2021-01-01", tz="UTC"),
            seed=1,
        )


def test_publication_rejects_substitution_and_invalid_pointer(tmp_path: Path) -> None:
    x, y, names = _arrays()
    model = create_model("ridge", "regression", names, "c" * 64, "d" * 64, seed=8).fit(x, y)
    parquet, columns = _parquet_bytes()
    contents = {
        name: (
            (model.trusted_bytes(), "application/x-joblib", ())
            if name == "model"
            else (parquet, "application/vnd.apache.parquet", columns)
            if name
            in {
                "feature_matrix",
                "targets",
                "splits",
                "predictions",
                "explanations",
                "drift",
                "comparison",
            }
            else (b"{}", "application/json", ())
        )
        for name in REQUIRED_ARTIFACTS
    }
    values = {
        "phase2_publication_id": "p2",
        "phase2_manifest_hash": "a" * 64,
        "phase3_publication_id": "p3",
        "phase3_manifest_hash": "b" * 64,
        "configuration_hash": "e" * 64,
        "git_commit": "deadbeef",
        "model_id": model.model_id,
        "feature_schema_hash": "f" * 64,
        "target_hash": "d" * 64,
        "preprocessor_hash": "c" * 64,
        "random_seed": 8,
        "dependency_versions": {},
        "validation_status": "PASS",
    }
    manifest = publish_bundle(tmp_path, Path("outputs"), Path("manifests"), values, contents)
    changed = dict(contents)
    changed["evaluation"] = (b'{"changed":true}', "application/json", ())
    with pytest.raises(PublicationConflictError, match="collision"):
        publish_bundle(tmp_path, Path("outputs"), Path("manifests"), values, changed)
    pointer = tmp_path / "manifests" / manifest.publication_id / "ml-publication.json"
    pointer.write_text("{}", encoding="utf-8")
    with pytest.raises(EvidenceIntegrityError, match="Invalid"):
        MLRepository(tmp_path, tmp_path / "manifests").authenticate(manifest.publication_id)
