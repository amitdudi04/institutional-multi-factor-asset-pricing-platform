"""Phase 3 numerical, temporal, publication, and adversarial tests."""

from datetime import UTC, date, datetime, timedelta
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pandas as pd
import pyarrow as pa
import pytest
from pydantic import ValidationError

from institutional_factor_platform.asset_pricing import service as service_module
from institutional_factor_platform.asset_pricing.config import (
    AssetPricingConfig,
    load_asset_pricing_config,
)
from institutional_factor_platform.asset_pricing.inputs import build_research_panel
from institutional_factor_platform.asset_pricing.models import MODEL_SPECS, custom_model
from institutional_factor_platform.asset_pricing.service import AssetPricingResearchService
from institutional_factor_platform.diagnostics.regression import regression_diagnostics
from institutional_factor_platform.exceptions import (
    ConfigurationError,
    DataQualityError,
    EvidenceIntegrityError,
    TemporalIntegrityError,
)
from institutional_factor_platform.regression.engine import (
    fama_macbeth,
    fit_panel,
    fit_regression,
    window_regressions,
)
from institutional_factor_platform.research_outputs.storage import (
    AssetPricingRepository,
    authenticate_asset_pricing_publication,
)
from institutional_factor_platform.statistical_tests.tests import normal_prediction_interval


def _regression_frame(count: int = 80) -> pd.DataFrame:
    index = np.arange(count, dtype=float)
    x1 = np.sin(index / 4.0) + index / 100.0
    x2 = np.cos(index / 7.0) - index / 200.0
    noise = np.sin(index * 1.7) * 0.01
    return pd.DataFrame(
        {
            "date": [date(2020, 1, 1) + timedelta(days=int(value)) for value in index],
            "entity": [f"E{int(value) % 8}" for value in index],
            "x1": x1,
            "x2": x2,
            "return": 0.02 + 1.5 * x1 - 0.7 * x2 + noise,
        }
    )


def _phase2_tables(periods: int = 20) -> tuple[pd.DataFrame, pd.DataFrame]:
    start = date(2018, 1, 31)
    dates = [start + timedelta(days=31 * index) for index in range(periods)]
    factor_rows: list[dict[str, object]] = []
    portfolio_rows: list[dict[str, object]] = []
    mapped = tuple(dict.fromkeys(load_asset_pricing_config().factor_mappings.values()))
    for index, current in enumerate(dates):
        available = datetime.combine(current, datetime.min.time(), tzinfo=UTC)
        market = 0.01 + 0.015 * np.sin(index / 3.0)
        risk_free = 0.001 + index * 0.000001
        for security in ("sec-a", "sec-b"):
            factor_rows.extend(
                [
                    {
                        "security_id": security,
                        "date": current,
                        "factor_id": "excess_return",
                        "raw_value": market,
                        "available_at": available,
                    },
                    {
                        "security_id": security,
                        "date": current,
                        "factor_id": "risk_free_rate",
                        "raw_value": risk_free,
                        "available_at": available,
                    },
                ]
            )
        for factor_number, factor_id in enumerate(mapped, start=1):
            spread = (
                0.002 * factor_number * np.sin((index + factor_number) / (factor_number + 1))
                + 0.0002 * index
            )
            base = 0.008 + 0.001 * np.cos(index / 4.0 + factor_number)
            for quantile, value in ((1, base), (3, base + spread)):
                portfolio_rows.append(
                    {
                        "formation_date": current - timedelta(days=30),
                        "date": current,
                        "factor_id": factor_id,
                        "quantile": quantile,
                        "value_weighted_return": value + 0.5 * market,
                        "available_at": available,
                    }
                )
    return pd.DataFrame(factor_rows), pd.DataFrame(portfolio_rows)


def _small_config(tmp_path: Path) -> AssetPricingConfig:
    base = load_asset_pricing_config()
    return base.model_copy(
        update={
            "minimum_observations": 8,
            "hac_lags": 1,
            "rolling_window": 12,
            "expanding_minimum": 8,
            "publication": base.publication.model_copy(
                update={
                    "output_root": Path("data") / "pricing",
                    "manifest_root": Path("manifests"),
                }
            ),
        }
    )


def test_approved_models_and_configuration_are_explicit(tmp_path: Path) -> None:
    config = load_asset_pricing_config()
    assert set(config.models) == set(MODEL_SPECS)
    assert config.canonical_hash() == config.canonical_hash()
    assert custom_model("liquidity", ("LIQ",)).factors == ("LIQ",)
    with pytest.raises(ConfigurationError):
        custom_model("", ("LIQ",))
    with pytest.raises(ConfigurationError, match="unique"):
        custom_model("duplicate", ("HML", "HML"))
    with pytest.raises(ConfigurationError, match="dependent"):
        custom_model("bad-dependent", ("HML",), dependent_variable="return")
    with pytest.raises(ConfigurationError, match="frequency"):
        custom_model("bad-frequency", ("HML",), frequency="daily")
    with pytest.raises(ConfigurationError, match="decimal_return"):
        custom_model("bad-unit", ("HML",), return_unit="percent")
    with pytest.raises(ValidationError):
        config.publication.__class__(output_root="../escape", manifest_root="safe")
    broken = tmp_path / "broken.yaml"
    broken.write_text("unknown: true\n", encoding="utf-8")
    with pytest.raises(ConfigurationError):
        load_asset_pricing_config(broken)
    raw = config.model_dump(mode="python")
    for updates in (
        {"expanding_minimum": 8, "minimum_observations": 9},
        {"rolling_window": 8, "minimum_observations": 9},
        {"models": {"unknown": ("market_excess",)}},
        {"models": {"fama_french_3": MODEL_SPECS["fama_french_3"].factors}, "factor_mappings": {}},
    ):
        with pytest.raises(ValidationError):
            AssetPricingConfig.model_validate({**raw, **updates})


@pytest.mark.parametrize("covariance", ["nonrobust", "HC0", "HC1", "HC2", "HC3", "HAC"])
def test_regression_recovers_known_coefficients_and_inference(covariance: str) -> None:
    frame = _regression_frame()
    result = fit_regression(
        frame,
        "return",
        ("x1", "x2"),
        model_id="known",
        covariance=covariance,  # type: ignore[arg-type]
        hac_lags=2,
    )
    estimates = result.coefficients.set_index("term")["estimate"]
    assert estimates["const"] == pytest.approx(0.02, abs=0.005)
    assert estimates["x1"] == pytest.approx(1.5, abs=0.01)
    assert estimates["x2"] == pytest.approx(-0.7, abs=0.01)
    assert result.metrics["adjusted_r_squared"] > 0.99
    assert (result.coefficients["standard_error"] >= 0).all()


@pytest.mark.parametrize("model_id", sorted(MODEL_SPECS))
def test_every_approved_model_specification_is_estimable(model_id: str) -> None:
    spec = MODEL_SPECS[model_id]
    index = np.arange(60, dtype=float)
    frame = pd.DataFrame(
        {
            factor: np.sin(index / (number + 2.0)) + np.cos(index * (number + 1.0) / 17.0)
            for number, factor in enumerate(spec.factors, start=1)
        }
    )
    frame["excess_return"] = (
        0.005
        + sum(
            (number / 10.0) * frame[factor] for number, factor in enumerate(spec.factors, start=1)
        )
        + np.sin(index * 1.9) * 0.0001
    )
    result = fit_regression(
        frame,
        "excess_return",
        spec.factors,
        model_id=model_id,
        covariance="HAC",
        hac_lags=2,
    )
    assert result.model_id == model_id
    assert set(result.coefficients["term"]) == {"const", *spec.factors}


def test_wls_panel_and_diagnostics() -> None:
    frame = _regression_frame()
    weights = pd.Series(np.linspace(1.0, 2.0, len(frame)), index=frame.index)
    wls = fit_regression(frame, "return", ("x1", "x2"), weights=weights, covariance="HC3")
    assert wls.estimator == "WLS"
    panel = fit_panel(
        frame,
        "return",
        ("x1", "x2"),
        entity="entity",
        time="date",
        entity_effects=True,
        minimum_observations=20,
        covariance="HC1",
    )
    assert panel.nobs == len(frame)
    diagnostics, influence = regression_diagnostics(wls, frame, ("x1", "x2"))
    assert "jarque_bera" in diagnostics["residual_tests"]
    assert len(influence) == len(frame)
    interval = normal_prediction_interval(wls.fitted, pd.Series(0.1, index=wls.fitted.index), 0.95)
    assert (interval["prediction_lower"] < interval["prediction_upper"]).all()


def test_regression_rejects_invalid_inputs_and_weights() -> None:
    frame = _regression_frame(20)
    with pytest.raises(DataQualityError, match="missing"):
        fit_regression(frame, "return", ("missing",))
    singular = frame.assign(copy=frame["x1"] * 2)
    with pytest.raises(DataQualityError, match="rank deficient"):
        fit_regression(singular, "return", ("x1", "copy"))
    with pytest.raises(DataQualityError, match="weights"):
        fit_regression(frame, "return", ("x1",), weights=pd.Series(-1.0, index=frame.index))
    with pytest.raises(DataQualityError, match="lags"):
        fit_regression(frame, "return", ("x1",), hac_lags=len(frame))
    with pytest.raises(DataQualityError, match="constant"):
        fit_regression(frame.assign(flat=1.0), "return", ("flat",))
    with pytest.raises(DataQualityError, match="at least"):
        fit_regression(frame.iloc[:3], "return", ("x1",), minimum_observations=8)
    with pytest.raises(DataQualityError, match="Dependent"):
        fit_regression(frame.assign(return_value=1.0), "return_value", ("x1",))


def test_rolling_and_expanding_are_past_only() -> None:
    frame = _regression_frame(30)
    original = window_regressions(
        frame, "date", "return", ("x1", "x2"), window=12, covariance="HC1"
    )
    changed = frame.copy()
    changed.loc[changed.index[-1], "return"] += 100.0
    rerun = window_regressions(changed, "date", "return", ("x1", "x2"), window=12, covariance="HC1")
    cutoff = frame["date"].iloc[-2]
    pd.testing.assert_frame_equal(
        original.loc[original["window_end"] <= cutoff].reset_index(drop=True),
        rerun.loc[rerun["window_end"] <= cutoff].reset_index(drop=True),
    )
    expanding = window_regressions(
        frame, "date", "return", ("x1", "x2"), window=10, expanding=True, covariance="HC1"
    )
    assert expanding["window_start"].nunique() == 1
    with pytest.raises(DataQualityError, match="one observation"):
        window_regressions(pd.concat([frame, frame.iloc[[0]]]), "date", "return", ("x1",), window=8)


def test_fama_macbeth_cross_sectional_workflow() -> None:
    rows: list[dict[str, object]] = []
    for period in range(15):
        for asset in range(12):
            beta = asset / 10.0
            rows.append(
                {
                    "date": period,
                    "beta": beta,
                    "return": 0.01 + 0.03 * beta + 0.001 * np.sin(asset + period),
                }
            )
    result = fama_macbeth(
        pd.DataFrame(rows), "date", "return", ("beta",), minimum_cross_section=8, hac_lags=1
    )
    assert result.set_index("term").loc["beta", "estimate"] == pytest.approx(0.03, abs=0.002)
    with pytest.raises(DataQualityError, match="cross-sections"):
        fama_macbeth(
            pd.DataFrame(rows).loc[lambda value: value["date"] == 0],
            "date",
            "return",
            ("beta",),
            minimum_cross_section=8,
            hac_lags=1,
        )


def test_phase2_alignment_and_temporal_attacks_are_rejected() -> None:
    factors, portfolios = _phase2_tables()
    panel = build_research_panel(factors, portfolios, load_asset_pricing_config().factor_mappings)
    assert {"market_excess", "risk_free_rate", "SMB", "HML", "excess_return"} <= set(panel)
    expected = panel["value_weighted_return"] - panel["risk_free_rate"]
    pd.testing.assert_series_equal(panel["excess_return"], expected, check_names=False)
    future = factors.copy()
    future.loc[0, "available_at"] = datetime(2030, 1, 1, tzinfo=UTC)
    with pytest.raises(TemporalIntegrityError):
        build_research_panel(future, portfolios, load_asset_pricing_config().factor_mappings)
    delayed = portfolios.copy()
    delayed.loc[0, "available_at"] = pd.to_datetime(delayed.loc[0, "available_at"]) + pd.Timedelta(
        days=1
    )
    with pytest.raises(TemporalIntegrityError):
        build_research_panel(factors, delayed, load_asset_pricing_config().factor_mappings)
    conflict = pd.concat([factors, factors.iloc[[0]].assign(raw_value=999.0)], ignore_index=True)
    with pytest.raises(DataQualityError, match="conflict"):
        build_research_panel(conflict, portfolios, load_asset_pricing_config().factor_mappings)
    with pytest.raises(DataQualityError, match="unavailable"):
        build_research_panel(factors, portfolios, {"BAD": "not_present"})


class _FactorRepositoryFixture:
    def __init__(self, factors: pd.DataFrame, portfolios: pd.DataFrame) -> None:
        self.factors = pa.Table.from_pandas(factors, preserve_index=False)
        self.portfolios = pa.Table.from_pandas(portfolios, preserve_index=False)
        self.manifest = SimpleNamespace(
            publication_id="factor-fixture", content_hash=lambda: "a" * 64
        )

    def authenticate(self, publication_id: str) -> SimpleNamespace:
        assert publication_id == "factor-fixture"
        return self.manifest

    def read_table(self, publication_id: str) -> pa.Table:
        self.authenticate(publication_id)
        return self.factors

    def read_portfolios(self, publication_id: str) -> pa.Table:
        self.authenticate(publication_id)
        return self.portfolios


def test_authenticated_publication_is_reproducible_and_tamper_evident(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    factors, portfolios = _phase2_tables()
    fixture = _FactorRepositoryFixture(factors, portfolios)
    config = _small_config(tmp_path)
    monkeypatch.setattr(service_module, "_git_commit", lambda root: "deadbeef")
    service = AssetPricingResearchService(config, tmp_path, fixture)  # type: ignore[arg-type]
    first = service.compute_and_publish("factor-fixture", ("capm",))
    second = service.compute_and_publish("factor-fixture", ("capm",))
    assert first.publication_id == second.publication_id
    assert service.repository.list_authenticated() == (first.publication_id,)
    assert service.repository.read_table(first.publication_id, "coefficients").num_rows > 0
    publication = tmp_path / "manifests" / first.publication_id / "asset-pricing-publication.json"
    assert authenticate_asset_pricing_publication(publication, tmp_path) == first
    coefficient = next(item for item in first.artifacts if item.name == "coefficients")
    target = tmp_path / coefficient.path
    target.write_bytes(target.read_bytes() + b"tamper")
    with pytest.raises(EvidenceIntegrityError, match="changed"):
        service.repository.authenticate(first.publication_id)
    assert AssetPricingRepository(tmp_path, tmp_path / "manifests").list_authenticated() == ()


def test_custom_model_traverses_authenticated_service_publication_boundary(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    factors, portfolios = _phase2_tables()
    fixture = _FactorRepositoryFixture(factors, portfolios)
    monkeypatch.setattr(service_module, "_git_commit", lambda root: "deadbeef")
    service = AssetPricingResearchService(
        _small_config(tmp_path),
        tmp_path,
        fixture,  # type: ignore[arg-type]
    )
    specification = custom_model("custom_value_momentum", ("market_excess", "HML", "MOM"))

    manifest = service.compute_and_publish(
        "factor-fixture",
        (specification.model_id,),
        custom_models=(specification,),
    )

    assert manifest.model_ids == (specification.model_id,)
    coefficients = service.repository.read_table(manifest.publication_id, "coefficients")
    assert set(coefficients.column("model_id").to_pylist()) == {specification.model_id}
    restarted = AssetPricingRepository(tmp_path, tmp_path / "manifests")
    assert restarted.authenticate(manifest.publication_id) == manifest

    missing = custom_model("custom_missing", ("market_excess", "UNMAPPED"))
    with pytest.raises(DataQualityError, match="mappings"):
        service.compute_and_publish("factor-fixture", (missing.model_id,), custom_models=(missing,))


def test_service_rejects_unapproved_model_set(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    factors, portfolios = _phase2_tables(10)
    service = AssetPricingResearchService(
        _small_config(tmp_path), tmp_path, _FactorRepositoryFixture(factors, portfolios)
    )  # type: ignore[arg-type]
    monkeypatch.setattr(service_module, "_git_commit", lambda root: "deadbeef")
    with pytest.raises(DataQualityError, match="not approved"):
        service.compute_and_publish("factor-fixture", ("unknown",))


def test_capm_does_not_resolve_unused_factor_mappings(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    factors, portfolios = _phase2_tables()
    base = _small_config(tmp_path)
    config = base.model_copy(
        update={"factor_mappings": {**base.factor_mappings, "MOM": "not-present"}}
    )
    monkeypatch.setattr(service_module, "_git_commit", lambda root: "deadbeef")
    service = AssetPricingResearchService(
        config, tmp_path, _FactorRepositoryFixture(factors, portfolios)
    )  # type: ignore[arg-type]

    publication = service.compute_and_publish("factor-fixture", ("capm",))

    assert publication.model_ids == ("capm",)
