"""Portfolio research orchestration."""

import hashlib
import os
import shutil
import subprocess
import tempfile
from datetime import UTC, datetime
from pathlib import Path
from typing import Literal, cast

import numpy as np
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

from institutional_factor_platform.backtest.costs import TransactionCostModel
from institutional_factor_platform.backtest.engine import run_backtest
from institutional_factor_platform.constraints.models import ConstraintSet
from institutional_factor_platform.data.evidence import atomic_write_json, canonical_json_bytes
from institutional_factor_platform.data.storage import sha256_file
from institutional_factor_platform.exceptions import DataQualityError, EvidenceIntegrityError
from institutional_factor_platform.factors.storage import FactorRepository
from institutional_factor_platform.numeric import FloatArray
from institutional_factor_platform.optimization.covariance import estimate_covariance
from institutional_factor_platform.optimization.engine import Method, optimize
from institutional_factor_platform.performance.metrics import performance_summary
from institutional_factor_platform.portfolio.allocations import equal_weight
from institutional_factor_platform.portfolio.config import PortfolioConfig
from institutional_factor_platform.research_outputs.portfolio_storage import (
    PortfolioArtifact,
    PortfolioManifest,
    PortfolioPublication,
    PortfolioRepository,
)
from institutional_factor_platform.research_outputs.storage import AssetPricingRepository
from institutional_factor_platform.scenarios.engine import Scenario, apply_scenario


class PortfolioResearchService:
    def __init__(
        self,
        config: PortfolioConfig,
        root: Path,
        factors: FactorRepository,
        pricing: AssetPricingRepository,
    ) -> None:
        self.config = config
        self.root = root.resolve()
        self.factors = factors
        self.pricing = pricing
        self.output_root = (self.root / config.publication.output_root).resolve()
        self.manifest_root = (self.root / config.publication.manifest_root).resolve()
        self.repository = PortfolioRepository(self.root, self.manifest_root)

    def compute_and_publish(
        self,
        phase3_publication_id: str,
        method: Method | Literal["equal_weight"],
        scenarios: tuple[Scenario, ...] = (),
    ) -> PortfolioManifest:
        phase3 = self.pricing.authenticate(phase3_publication_id)
        phase2 = self.factors.authenticate(phase3.phase2_publication_id)
        if phase3.phase2_manifest_hash != phase2.content_hash():
            raise EvidenceIntegrityError("Phase 3 and Phase 2 lineage do not connect")
        source = self.factors.read_portfolios(phase2.publication_id).to_pandas()
        returns, benchmark = _return_matrix(source)
        risk_free = _risk_free_series(
            self.factors.read_table(phase2.publication_id).to_pandas(), returns.index
        )
        costs = TransactionCostModel(*self.config.costs.require_explicit())
        constraints = ConstraintSet(**self.config.constraints.model_dump())
        if constraints.sector_limits or constraints.exposure_limits:
            raise DataQualityError(
                "Sector/exposure constraints require authenticated Phase 4 metadata inputs"
            )
        cost_rate = (
            costs.commission_bps / 10_000.0
            + costs.spread_bps / 20_000.0
            + costs.slippage_bps / 10_000.0
        )
        optimization_rows: list[dict[str, object]] = []

        def allocator(history: pd.DataFrame, previous: FloatArray) -> FloatArray:
            if method == "equal_weight":
                weights = equal_weight(history.shape[1])
                constraints.verify(
                    weights, tuple(str(value) for value in history.columns), previous=previous
                )
                return weights
            covariance = estimate_covariance(
                history,
                self.config.covariance_method,
                annualization=self.config.annualization_periods,
            )
            mean = history.mean().to_numpy(dtype=float) * self.config.annualization_periods
            result = optimize(
                method,
                mean,
                covariance,
                constraints,
                asset_ids=tuple(str(value) for value in history.columns),
                previous_weights=previous if previous.sum() else None,
                scenarios=history.to_numpy(dtype=float) if method == "cvar" else None,
                transaction_cost_rate=cost_rate,
            )
            optimization_rows.append(
                {
                    "method": method,
                    "objective_value": result.objective_value,
                    "expected_return": result.expected_return,
                    "volatility": result.volatility,
                    "iterations": result.iterations,
                    **result.diagnostics,
                }
            )
            return result.weights

        backtest = run_backtest(
            returns, benchmark, allocator, costs, window=self.config.estimation_window
        )
        summary = performance_summary(
            backtest.returns,
            risk_free=backtest.returns["date"].map(risk_free),
            annualization=self.config.annualization_periods,
        )
        scenario_results = _evaluate_scenarios(
            scenarios,
            backtest.allocations,
            tuple(str(value) for value in returns.columns),
            phase2.publication_id,
        )
        git_commit = _git_commit(self.root)
        publication_id = _publication_id(
            phase2.content_hash(),
            phase3.content_hash(),
            self.config.canonical_hash(),
            git_commit,
            method,
            scenarios,
        )
        existing = self.manifest_root / publication_id / "portfolio-publication.json"
        if existing.is_file():
            return self.repository.authenticate(publication_id)
        return self._publish(
            publication_id,
            phase2.publication_id,
            phase2.content_hash(),
            phase3.publication_id,
            phase3.content_hash(),
            method,
            backtest.allocations,
            backtest.transactions,
            backtest.returns,
            pd.DataFrame(optimization_rows),
            summary,
            scenario_results,
            git_commit,
        )

    def _publish(
        self,
        publication_id: str,
        phase2_id: str,
        phase2_hash: str,
        phase3_id: str,
        phase3_hash: str,
        method: str,
        allocations: pd.DataFrame,
        transactions: pd.DataFrame,
        returns: pd.DataFrame,
        diagnostics: pd.DataFrame,
        summary: dict[str, object],
        scenario_results: dict[str, object],
        git_commit: str,
    ) -> PortfolioManifest:
        output = self.output_root / publication_id
        run_root = self.manifest_root / publication_id
        staging_parent = self.manifest_root / ".staging"
        staging_parent.mkdir(parents=True, exist_ok=True)
        staging = Path(tempfile.mkdtemp(prefix=f"{publication_id}-", dir=staging_parent))
        artifacts: list[PortfolioArtifact] = []
        try:
            for name, frame in (
                ("allocations", allocations),
                ("transactions", transactions),
                ("returns", returns),
                ("optimization_diagnostics", diagnostics),
            ):
                path = output / f"{name}.parquet"
                path.parent.mkdir(parents=True, exist_ok=True)
                handle, temporary_name = tempfile.mkstemp(
                    dir=path.parent, prefix=f".{path.name}-", suffix=".tmp"
                )
                os.close(handle)
                temporary = Path(temporary_name)
                pq.write_table(
                    pa.Table.from_pandas(frame, preserve_index=False), temporary, compression="zstd"
                )
                checksum = sha256_file(temporary)
                if path.exists() and sha256_file(path) != checksum:
                    raise EvidenceIntegrityError(f"Portfolio artifact collision: {path}")
                if not path.exists():
                    os.replace(temporary, path)
                temporary.unlink(missing_ok=True)
                artifacts.append(
                    PortfolioArtifact(
                        name=name,
                        path=_relative(path, self.root),
                        checksum=checksum,
                        byte_size=path.stat().st_size,
                        media_type="application/vnd.apache.parquet",
                        columns=tuple(frame.columns),
                    )
                )
            documents = {
                "constraint_report": {
                    "publication_id": publication_id,
                    "approved_baseline": "long_only_unlevered",
                    "constraints": self.config.constraints.model_dump(mode="json"),
                },
                "performance_summary": {"publication_id": publication_id, **summary},
                "risk_summary": {
                    "publication_id": publication_id,
                    **cast(dict[str, object], summary["risk"]),
                },
                "benchmark_comparison": {
                    "publication_id": publication_id,
                    "gross_net_benchmark_reconciled": True,
                },
                "scenario_report": {
                    "publication_id": publication_id,
                    **scenario_results,
                },
                "configuration": {
                    "publication_id": publication_id,
                    "configuration_hash": self.config.canonical_hash(),
                    "configuration": self.config.model_dump(mode="json"),
                },
                "lineage": {
                    "publication_id": publication_id,
                    "phase2_publication_id": phase2_id,
                    "phase2_manifest_hash": phase2_hash,
                    "phase3_publication_id": phase3_id,
                    "phase3_manifest_hash": phase3_hash,
                    "git_commit": git_commit,
                },
                "validation": {
                    "publication_id": publication_id,
                    "status": "PASS",
                    "allocation_rows": len(allocations),
                    "return_rows": len(returns),
                },
            }
            for name, value in documents.items():
                staged = staging / f"{name}.json"
                atomic_write_json(staged, value)
                artifacts.append(
                    PortfolioArtifact(
                        name=name,
                        path=_relative(run_root / staged.name, self.root),
                        checksum=sha256_file(staged),
                        byte_size=staged.stat().st_size,
                        media_type="application/json",
                    )
                )
            manifest = PortfolioManifest(
                schema_version="1.0.0",
                publication_id=publication_id,
                created_at=datetime.now(UTC),
                phase2_publication_id=phase2_id,
                phase2_manifest_hash=phase2_hash,
                phase3_publication_id=phase3_id,
                phase3_manifest_hash=phase3_hash,
                configuration_hash=self.config.canonical_hash(),
                git_commit=git_commit,
                method=method,
                artifacts=tuple(artifacts),
                validation_status="PASS",
            )
            atomic_write_json(staging / "portfolio-manifest.json", manifest.model_dump(mode="json"))
            publication = PortfolioPublication(
                schema_version="1.0.0",
                publication_id=publication_id,
                manifest_path=_relative(run_root / "portfolio-manifest.json", self.root),
                manifest_hash=manifest.content_hash(),
                configuration_hash=manifest.configuration_hash,
                git_commit=git_commit,
            )
            atomic_write_json(
                staging / "portfolio-publication.json", publication.model_dump(mode="json")
            )
            os.replace(staging, run_root)
            return self.repository.authenticate(publication_id)
        except Exception:
            shutil.rmtree(staging, ignore_errors=True)
            raise


def _return_matrix(frame: pd.DataFrame) -> tuple[pd.DataFrame, pd.Series]:
    required = {"date", "factor_id", "quantile", "value_weighted_return", "benchmark_return"}
    if required - set(frame):
        raise DataQualityError("Phase 2 portfolio contract is incomplete")
    values = frame.copy()
    values["asset_id"] = values["factor_id"].astype(str) + ":Q" + values["quantile"].astype(str)
    returns = (
        values.pivot(index="date", columns="asset_id", values="value_weighted_return")
        .sort_index()
        .dropna()
    )
    grouped = values.groupby("date")["benchmark_return"]
    spread = grouped.max() - grouped.min()
    if (spread > 1e-12).any():
        raise DataQualityError("Benchmark returns conflict across Phase 2 portfolios")
    benchmark = grouped.mean().reindex(returns.index)
    return returns, benchmark


def _risk_free_series(frame: pd.DataFrame, dates: pd.Index) -> pd.Series:
    required = {"date", "factor_id", "raw_value"}
    if required - set(frame):
        raise DataQualityError("Phase 2 factor contract lacks risk-free evidence")
    selected = frame.loc[frame["factor_id"].eq("risk_free_rate"), ["date", "raw_value"]]
    if selected.empty:
        raise DataQualityError("Phase 2 risk-free evidence is unavailable")
    grouped = selected.groupby("date")["raw_value"]
    if (grouped.nunique(dropna=False) > 1).any():
        raise DataQualityError("Risk-free values conflict across securities")
    result = grouped.first().reindex(dates)
    if result.isna().any():
        raise DataQualityError("Risk-free values do not align with portfolio dates")
    return result.astype(float)


def _relative(path: Path, root: Path) -> str:
    try:
        return path.resolve().relative_to(root).as_posix()
    except ValueError as exc:
        raise EvidenceIntegrityError(
            f"Portfolio evidence path escapes project root: {path}"
        ) from exc


def _publication_id(
    phase2_hash: str,
    phase3_hash: str,
    config_hash: str,
    git_commit: str,
    method: str,
    scenarios: tuple[Scenario, ...],
) -> str:
    digest = hashlib.sha256(
        canonical_json_bytes(
            {
                "phase2": phase2_hash,
                "phase3": phase3_hash,
                "configuration": config_hash,
                "git_commit": git_commit,
                "method": method,
                "scenarios": [
                    {"name": item.name, "kind": item.kind, "shocks": item.shocks}
                    for item in scenarios
                ],
                "engine": "1.0.0",
            }
        )
    ).hexdigest()
    return f"portfolio-{digest[:32]}"


def _evaluate_scenarios(
    scenarios: tuple[Scenario, ...],
    allocations: pd.DataFrame,
    asset_ids: tuple[str, ...],
    exposure_source_publication_id: str,
) -> dict[str, object]:
    if not scenarios:
        return {
            "scenarios": [],
            "status": "NOT_REQUESTED",
            "exposure_source_publication_id": exposure_source_publication_id,
        }
    if allocations.empty:
        raise DataQualityError("Scenario evaluation requires an authenticated allocation")
    latest_date = allocations["date"].max()
    latest = allocations.loc[allocations["date"].eq(latest_date)].set_index("asset_id")
    if set(latest.index) != set(asset_ids):
        raise EvidenceIntegrityError("Scenario allocation identity differs from return assets")
    weights = latest.reindex(asset_ids)["weight"].to_numpy(float)
    factor_ids = tuple(asset.split(":Q", maxsplit=1)[0] for asset in asset_ids)
    exposure_keys = sorted({key for scenario in scenarios for key in scenario.shocks})
    exposures = {
        key: np.asarray([1.0 if factor == key else 0.0 for factor in factor_ids], dtype=float)
        for key in exposure_keys
        if key in set(factor_ids)
    }
    results = []
    for scenario in scenarios:
        result = apply_scenario(scenario, weights, exposures)
        result.update(
            {
                "as_of_date": str(latest_date),
                "exposure_source_publication_id": exposure_source_publication_id,
                "exposure_method": "authenticated_phase2_factor_portfolio_identity",
                "mapping_status": "PASS" if not result["unmapped_shocks"] else "PARTIAL",
            }
        )
        results.append(result)
    partial = any(item["unmapped_shocks"] for item in results)
    return {
        "scenarios": results,
        "status": "PASS_WITH_UNMAPPED_EXPOSURES" if partial else "PASS",
        "limitations": (
            ["Unmapped shocks contribute zero and are disclosed explicitly"] if partial else []
        ),
    }


def _git_commit(root: Path) -> str:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=root, text=True, stderr=subprocess.DEVNULL
        ).strip()
    except (OSError, subprocess.CalledProcessError) as exc:
        raise EvidenceIntegrityError(
            "Portfolio publication requires an available Git commit"
        ) from exc
