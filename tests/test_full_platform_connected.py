"""Connected Phase 1-to-6 integration regression tests."""

import json
from datetime import UTC, date, datetime, timedelta
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
import pytest
import yaml
from fastapi.testclient import TestClient

from institutional_factor_platform.api.app import create_app
from institutional_factor_platform.asset_pricing.config import load_asset_pricing_config
from institutional_factor_platform.asset_pricing.models import custom_model
from institutional_factor_platform.asset_pricing.service import AssetPricingResearchService
from institutional_factor_platform.cli import main as cli_main
from institutional_factor_platform.dashboard import app as dashboard_app
from institutional_factor_platform.dashboard.presentation import PAGES
from institutional_factor_platform.data.config import load_phase1_config
from institutional_factor_platform.data.contracts import (
    FACTOR_FUNDAMENTAL_INPUT,
    FACTOR_MARKET_INPUT,
)
from institutional_factor_platform.data.domain import DataSource, RetrievalRequest, SecurityId
from institutional_factor_platform.data.security_master import (
    SecurityMappingStore,
    mapping_from_listing,
)
from institutional_factor_platform.data.services import DataIngestionService
from institutional_factor_platform.data.sources.owner_supplied import OwnerSuppliedAdapter
from institutional_factor_platform.delivery.config import load_delivery_config
from institutional_factor_platform.delivery.schemas import PublicationReference, ReportRequest
from institutional_factor_platform.delivery.service import DeliveryService
from institutional_factor_platform.exceptions import EvidenceIntegrityError
from institutional_factor_platform.factors.config import load_factor_config
from institutional_factor_platform.factors.contracts import MARKET_REQUIRED_UNITS
from institutional_factor_platform.factors.service import FactorResearchService
from institutional_factor_platform.factors.storage import FactorRepository
from institutional_factor_platform.ml.config import load_ml_config
from institutional_factor_platform.ml.publication import MLRepository
from institutional_factor_platform.ml.service import MLResearchService
from institutional_factor_platform.portfolio.config import load_portfolio_config
from institutional_factor_platform.portfolio.service import PortfolioResearchService
from institutional_factor_platform.research_outputs.portfolio_storage import PortfolioRepository
from institutional_factor_platform.research_outputs.storage import AssetPricingRepository
from institutional_factor_platform.scenarios.engine import Scenario

FIELDS = (
    "book_equity",
    "net_income",
    "operating_cash_flow",
    "dividends",
    "shareholder_equity",
    "total_assets",
    "gross_profit",
    "operating_income",
    "revenue",
    "average_assets",
    "total_accruals",
    "total_debt",
    "interest_expense",
    "prior_total_assets",
    "capex",
    "prior_capex",
    "net_equity_issuance",
    "working_capital",
    "prior_working_capital",
)


class _ConnectedDashboardAPI:
    """Route dashboard requests through the real authenticated delivery application."""

    def __init__(self, client: TestClient) -> None:
        self.client = client

    def get(self, path: str) -> Any:
        response = self.client.get(f"/api/v1/{path}")
        response.raise_for_status()
        return response.json()

    def post_report(self, payload: dict[str, Any]) -> Any:
        response = self.client.post("/api/v1/reports", json=payload)
        response.raise_for_status()
        return response.json()


class _DashboardRecorder:
    """Capture presentation objects without requiring a browser process."""

    def __init__(self) -> None:
        self.calls: list[tuple[str, tuple[Any, ...]]] = []
        self.sidebar = self

    def __getattr__(self, name: str) -> Any:
        def call(*args: Any, **kwargs: Any) -> Any:
            del kwargs
            self.calls.append((name, args))
            if name == "columns":
                return [self, self, self]
            if name == "selectbox":
                return args[1][0]
            if name == "multiselect":
                return list(args[1])
            if name == "button":
                return False
            return None

        return call


def _inputs(periods: int = 48, securities: int = 24) -> tuple[pd.DataFrame, pd.DataFrame]:
    market_rows: list[dict[str, object]] = []
    security_ids = tuple(f"sec_{number:032d}" for number in range(securities))
    for period in range(periods):
        current = date(2020, 1, 31) + timedelta(days=31 * period)
        available = datetime.combine(current, datetime.min.time(), tzinfo=UTC) + timedelta(hours=12)
        benchmark = 0.001 + 0.006 * np.sin(period / 4)
        for number, security_id in enumerate(security_ids, start=1):
            security_return = (
                benchmark
                + 0.0015 * np.sin(number * 1.37 + period / 3.0)
                + 0.001 * np.cos(period / (number % 5 + 1))
                + 0.0004 * np.cos(number * period / 11.0)
            )
            price = 20.0 + (number * 7) % 29 + number * 0.3 + period * 0.2
            market_rows.append(
                {
                    "security_id": security_id,
                    "date": current,
                    "available_at": available,
                    "eligible": True,
                    "eligibility_available_at": available,
                    "sector": f"sector-{number % 3}",
                    "industry": f"industry-{number}",
                    "classification_available_at": available,
                    "return": security_return,
                    "price": price,
                    "high": price * 1.01,
                    "low": price * 0.99,
                    "volume": float(1_000_000 + number * 10_000 + period),
                    "shares_outstanding": float(10_000_000 + number * 1_000_000),
                    "exchange": "XNYS",
                    "market_return": benchmark + 0.0005,
                    "risk_free": 0.0001,
                    "benchmark_return": benchmark,
                }
            )
    fundamental_rows = []
    for number, security_id in enumerate(security_ids, start=1):
        for field_number, field in enumerate(FIELDS, start=1):
            fundamental_rows.append(
                {
                    "security_id": security_id,
                    "period_end": date(2019, 9, 30),
                    "available_at": datetime(2020, 1, 1, tzinfo=UTC),
                    "field": field,
                    "value": float(
                        1_000
                        + field_number * 30
                        + number * (field_number % 5 + 1)
                        + 100 * np.sin(number * field_number * 0.37)
                    ),
                    "unit": "USD",
                }
            )
    return pd.DataFrame(market_rows), pd.DataFrame(fundamental_rows)


def _owner_request(
    path: Path, schema: str, units: dict[str, str], mapping_path: Path
) -> RetrievalRequest:
    return RetrievalRequest(
        DataSource.OWNER_SUPPLIED,
        f"connected-{schema}",
        parameters={
            "path": str(path),
            "schema": schema,
            "contract_version": "1.0.0",
            "source_name": "authenticated synthetic connected fixture",
            "source_ownership": "test-only generated evidence",
            "units": units,
            "date_semantics": "explicit synthetic observation and availability dates",
            "security_identifier_semantics": "persisted canonical synthetic mappings",
            "mapping_authority_path": str(mapping_path),
        },
    )


def test_full_connected_phase1_to_phase6_pipeline_restart_and_tamper(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    for target in (
        "institutional_factor_platform.data.services._git_commit",
        "institutional_factor_platform.factors.service._git_commit",
        "institutional_factor_platform.asset_pricing.service._git_commit",
        "institutional_factor_platform.portfolio.service._git_commit",
        "institutional_factor_platform.ml.service._git_commit",
    ):
        monkeypatch.setattr(target, lambda root: "deadbeef")

    market, fundamentals = _inputs()
    market_path = tmp_path / "market.parquet"
    fundamental_path = tmp_path / "fundamentals.parquet"
    pq.write_table(
        pa.Table.from_pandas(market, schema=FACTOR_MARKET_INPUT.schema, preserve_index=False),
        market_path,
    )
    pq.write_table(
        pa.Table.from_pandas(
            fundamentals, schema=FACTOR_FUNDAMENTAL_INPUT.schema, preserve_index=False
        ),
        fundamental_path,
    )
    mapping_path = tmp_path / "security-mapping.json"
    SecurityMappingStore(mapping_path).persist(
        tuple(
            mapping_from_listing(
                source=DataSource.OWNER_SUPPLIED,
                source_identifier=f"connected-{index}",
                ticker=f"S{index}",
                exchange="XNYS",
                mic="XNYS",
                valid_from=date(2019, 1, 1),
                valid_to=None,
                provenance="authenticated synthetic connected fixture",
                retrieval_timestamp=datetime(2020, 1, 1, tzinfo=UTC),
                security_id=SecurityId(security_id),
            )
            for index, security_id in enumerate(sorted(market["security_id"].unique()), start=1)
        )
    )
    phase1 = DataIngestionService(load_phase1_config(), root=tmp_path)
    market_manifest = phase1.ingest(
        OwnerSuppliedAdapter(),
        _owner_request(
            market_path, "factor_market_input", dict(MARKET_REQUIRED_UNITS), mapping_path
        ),
        FACTOR_MARKET_INPUT,
        "parquet",
        "application/vnd.apache.parquet",
    )
    fundamental_manifest = phase1.ingest(
        OwnerSuppliedAdapter(),
        _owner_request(
            fundamental_path,
            "factor_fundamental_input",
            {field: "USD" for field in FIELDS},
            mapping_path,
        ),
        FACTOR_FUNDAMENTAL_INPUT,
        "parquet",
        "application/vnd.apache.parquet",
    )

    factor_base = load_factor_config()
    factor_config = factor_base.model_copy(
        update={
            "windows": factor_base.windows.model_copy(
                update={
                    "short": 2,
                    "medium": 3,
                    "half_year": 4,
                    "one_year": 5,
                    "two_year": 6,
                    "minimum_observations": 2,
                }
            )
        }
    )
    phase2_service = FactorResearchService(factor_config, tmp_path)
    phase2_result = phase2_service.compute_and_publish(
        (
            phase1.research.get(market_manifest.dataset_id),
            phase1.research.get(fundamental_manifest.dataset_id),
        ),
        market_dataset_id=market_manifest.dataset_id,
        fundamental_dataset_id=fundamental_manifest.dataset_id,
    )
    phase2 = phase2_service.repository.authenticate(phase2_result.publication_id)
    factor_ids = phase2_service.repository.read_table(phase2.publication_id).column("factor_id")
    assert len(set(factor_ids.to_pylist())) == 48

    pricing_base = load_asset_pricing_config()
    pricing_config = pricing_base.model_copy(
        update={
            "minimum_observations": 8,
            "hac_lags": 1,
            "rolling_window": 24,
            "expanding_minimum": 24,
        }
    )
    phase3_service = AssetPricingResearchService(
        pricing_config,
        tmp_path,
        FactorRepository(tmp_path, tmp_path / factor_config.publication.manifest_root),
    )
    phase3_by_model = {
        model_id: phase3_service.compute_and_publish(phase2.publication_id, (model_id,))
        for model_id in (
            "capm",
            "fama_french_3",
            "carhart_4",
            "fama_french_5",
            "hou_xue_zhang_q",
        )
    }
    custom_specification = custom_model("custom_value_momentum", ("market_excess", "HML", "MOM"))
    phase3_by_model[custom_specification.model_id] = phase3_service.compute_and_publish(
        phase2.publication_id,
        (custom_specification.model_id,),
        custom_models=(custom_specification,),
    )
    phase3 = phase3_by_model["capm"]
    for model_id, publication in phase3_by_model.items():
        assert publication.model_ids == (model_id,)
        for artifact in (
            "coefficients",
            "diagnostics",
            "residuals",
            "model_comparison",
            "rolling_coefficients",
        ):
            if artifact in {"diagnostics"}:
                path = next(item.path for item in publication.artifacts if item.name == artifact)
                assert (tmp_path / path).stat().st_size > 0
            else:
                assert (
                    phase3_service.repository.read_table(
                        publication.publication_id, artifact
                    ).num_rows
                    > 0
                )

    portfolio_base = load_portfolio_config()
    portfolio_config = portfolio_base.model_copy(
        update={
            "estimation_window": 6,
            "minimum_observations": 6,
            "covariance_method": "sample",
            "costs": portfolio_base.costs.model_copy(
                update={
                    "commission_bps": 1.0,
                    "spread_bps": 2.0,
                    "slippage_bps": 1.0,
                    "market_impact_coefficient": 0.0,
                }
            ),
        }
    )
    phase4_service = PortfolioResearchService(
        portfolio_config,
        tmp_path,
        phase2_service.repository,
        phase3_service.repository,
    )
    phase4 = phase4_service.compute_and_publish(
        phase3.publication_id,
        "equal_weight",
        (
            Scenario("market stress", {"book_to_market": -0.1}, "market_crash"),
            Scenario("rates stress", {"book_to_market": -0.03}, "interest_rate"),
            Scenario("volatility stress", {"momentum_12_1m": -0.05}, "volatility"),
            Scenario("inflation stress", {"book_to_market": -0.025}, "inflation"),
            Scenario("liquidity stress", {"momentum_12_1m": -0.015}, "liquidity"),
            Scenario("custom sensitivity", {"book_to_market": 0.01}, "custom"),
        ),
    )
    scenario_path = next(item.path for item in phase4.artifacts if item.name == "scenario_report")
    scenario_report = json.loads((tmp_path / scenario_path).read_text("utf-8"))
    assert len(scenario_report["scenarios"]) == 6

    ml_base = load_ml_config()
    ml_config = ml_base.model_copy(
        update={
            "inputs": ml_base.inputs.model_copy(
                update={"phase4_publication_id": phase4.publication_id}
            ),
            "features": ml_base.features.model_copy(
                update={
                    "families": ("book_to_market", "momentum_12_1m"),
                    "minimum_coverage": 0.9,
                }
            ),
            "target": ml_base.target.model_copy(update={"kind": "future_return", "horizon": 1}),
            "split": ml_base.split.model_copy(
                update={
                    "method": "holdout",
                    "train_periods": 20,
                    "validation_periods": 8,
                    "test_periods": 5,
                    "embargo_periods": 0,
                }
            ),
            "search": ml_base.search.model_copy(update={"maximum_trials": 1}),
            "explainability": ml_base.explainability.model_copy(update={"enabled": False}),
            "economic_evaluation": ml_base.economic_evaluation.model_copy(
                update={"enabled": True, "selection_quantile": 0.25}
            ),
        }
    )
    phase5_service = MLResearchService(
        ml_config,
        tmp_path,
        phase2_service.repository,
        phase3_service.repository,
        phase1.research,
        phase4_service.repository,
    )
    phase5 = phase5_service.train_evaluate_publish(phase3.publication_id, "ridge")

    target_publications: dict[str, str] = {}
    for target_kind in (
        "future_return",
        "future_excess_return",
        "percentile_rank",
        "ordinal_rank",
        "quantile_bucket",
        "outperformance",
        "future_volatility",
        "future_downside_volatility",
        "future_drawdown",
        "future_risk_quantile",
    ):
        target_config = ml_config.model_copy(
            update={
                "target": ml_config.target.model_copy(
                    update={
                        "kind": target_kind,
                        "horizon": 3,
                        "benchmark_id": (
                            "SP500-TR"
                            if target_kind in {"future_excess_return", "outperformance"}
                            else None
                        ),
                        "threshold": 0.0,
                        "quantiles": 4,
                        "annualization_periods": 12,
                        "risk_quantile_alpha": 0.05,
                    }
                )
            }
        )
        target_service = MLResearchService(
            target_config,
            tmp_path,
            phase2_service.repository,
            phase3_service.repository,
            phase1.research,
            phase4_service.repository,
        )
        connected_dataset, target_metadata = target_service.build_authenticated_dataset(
            phase3.publication_id
        )
        assert not connected_dataset.empty
        assert target_metadata["target_source_dataset_id"] == market_manifest.dataset_id
        assert (
            target_metadata["target_source_artifact_checksum"]
            == phase1.research.get(market_manifest.dataset_id).checksum
        )
        assert target_metadata["target_source_unit"] == "decimal_return"
        target_publications[target_kind] = str(target_metadata["target_hash"])
    assert len(set(target_publications.values())) == 10

    restarted = DeliveryService(load_delivery_config(), tmp_path)
    publications = restarted.publications(None, 0, 100)
    expected = {
        market_manifest.dataset_id,
        fundamental_manifest.dataset_id,
        phase2.publication_id,
        phase4.publication_id,
        phase5.publication_id,
    } | {publication.publication_id for publication in phase3_by_model.values()}
    assert expected <= {str(item["publication_id"]) for item in publications.items}
    client = TestClient(create_app(load_delivery_config(), restarted))
    assert client.get("/api/v1/ready").json()["status"] == "ready"
    endpoint_matrix = {
        phase2.publication_id: (
            "factors",
            ("definitions", "diagnostics", "observations"),
        ),
        phase3.publication_id: (
            "asset-pricing",
            ("models", "coefficients", "diagnostics", "comparisons"),
        ),
        phase4.publication_id: (
            "portfolios",
            ("weights", "performance", "risk", "scenarios", "costs"),
        ),
        phase5.publication_id: (
            "ml",
            (
                "model-card",
                "predictions",
                "evaluation",
                "explanations",
                "drift",
                "economic-evaluation",
            ),
        ),
    }
    for publication_id, (family, suffixes) in endpoint_matrix.items():
        listing = client.get(f"/api/v1/{family}/publications")
        assert listing.status_code == 200 and listing.json()["total"] > 0
        detail = client.get(f"/api/v1/{family}/publications/{publication_id}")
        assert detail.status_code == 200
        for suffix in suffixes:
            response = client.get(f"/api/v1/{family}/publications/{publication_id}/{suffix}")
            assert response.status_code == 200
            assert response.json()

    dashboard = _ConnectedDashboardAPI(client)
    dashboard_recorder = _DashboardRecorder()
    monkeypatch.setattr(dashboard_app, "st", dashboard_recorder)
    for page in PAGES:
        if page.key == "overview":
            dashboard_app._overview(dashboard)
        elif page.key == "reports":
            dashboard_app._reports(dashboard)
        else:
            dashboard_app._research_page(dashboard, page.key)
    assert len(PAGES) == 9
    assert {name for name, _ in dashboard_recorder.calls} >= {
        "metric",
        "json",
        "selectbox",
        "multiselect",
    }

    report_sources = (
        PublicationReference(kind="factors", publication_id=phase2.publication_id),
        PublicationReference(kind="asset_pricing", publication_id=phase3.publication_id),
        PublicationReference(kind="portfolio", publication_id=phase4.publication_id),
        PublicationReference(kind="ml", publication_id=phase5.publication_id),
    )
    for format_name in ("markdown", "html", "json", "csv"):
        report = restarted.create_report(
            ReportRequest(publications=report_sources, format=format_name)
        )
        assert restarted.reports.verify(report.report_id) == report
        assert restarted.reports.read(report.report_id)

    assert FactorRepository(
        tmp_path, tmp_path / factor_config.publication.manifest_root
    ).authenticate(phase2.publication_id)
    restarted_pricing = AssetPricingRepository(
        tmp_path, tmp_path / pricing_config.publication.manifest_root
    )
    for publication in phase3_by_model.values():
        assert restarted_pricing.authenticate(publication.publication_id)
    assert PortfolioRepository(
        tmp_path, tmp_path / portfolio_config.publication.manifest_root
    ).authenticate(phase4.publication_id)
    assert MLRepository(tmp_path, tmp_path / ml_config.publication.manifest_root).authenticate(
        phase5.publication_id
    )

    monkeypatch.setattr(
        "institutional_factor_platform.data.services.find_project_root", lambda: tmp_path
    )
    config_paths: dict[str, Path] = {}
    for name, config in (
        ("factor", factor_config),
        ("pricing", pricing_config),
        ("portfolio", portfolio_config),
        ("ml", ml_config),
    ):
        path = tmp_path / f"{name}.yaml"
        path.write_text(yaml.safe_dump(config.model_dump(mode="json")), "utf-8")
        config_paths[name] = path
    cli_commands = (
        [
            "compute-factors",
            "--parent",
            market_manifest.dataset_id,
            "--parent",
            fundamental_manifest.dataset_id,
            "--market-dataset",
            market_manifest.dataset_id,
            "--fundamental-dataset",
            fundamental_manifest.dataset_id,
            "--factor-config",
            str(config_paths["factor"]),
        ],
        [
            "compute-asset-pricing",
            phase2.publication_id,
            "--model",
            "capm",
            "--asset-pricing-config",
            str(config_paths["pricing"]),
        ],
        [
            "compute-portfolio",
            phase3.publication_id,
            "equal_weight",
            "--portfolio-config",
            str(config_paths["portfolio"]),
        ],
        [
            "build-ml-dataset",
            phase3.publication_id,
            "--ml-config",
            str(config_paths["ml"]),
        ],
        [
            "train-ml-model",
            phase3.publication_id,
            "ridge",
            "--ml-config",
            str(config_paths["ml"]),
        ],
        ["validate-factor-config"],
        ["validate-asset-pricing-config"],
        ["validate-portfolio-config"],
        ["validate-ml-config", "--ml-config", str(config_paths["ml"])],
        ["validate-delivery-config"],
        ["list-factor-publications"],
        ["list-asset-pricing-publications"],
        ["list-portfolio-publications"],
        ["list-ml-publications"],
        [
            "verify-factor-publication",
            str(
                tmp_path
                / factor_config.publication.manifest_root
                / phase2.publication_id
                / "factor-publication.json"
            ),
        ],
        [
            "verify-asset-pricing-publication",
            str(
                tmp_path
                / pricing_config.publication.manifest_root
                / phase3.publication_id
                / "asset-pricing-publication.json"
            ),
        ],
        [
            "verify-portfolio-publication",
            str(
                tmp_path
                / portfolio_config.publication.manifest_root
                / phase4.publication_id
                / "portfolio-publication.json"
            ),
        ],
        ["verify-ml-publication", phase5.publication_id],
        ["verify-delivery-platform"],
    )
    for command in cli_commands:
        assert cli_main(command) == 0
        assert capsys.readouterr().out.strip()

    market_handle = phase1.research.get(market_manifest.dataset_id)
    market_handle.artifact_path.write_bytes(market_handle.artifact_path.read_bytes() + b"tamper")
    with pytest.raises(EvidenceIntegrityError):
        phase5_service.build_authenticated_dataset(phase3.publication_id)
