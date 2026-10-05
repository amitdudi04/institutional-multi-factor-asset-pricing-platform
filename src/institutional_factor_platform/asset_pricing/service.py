"""Asset-pricing research orchestration."""

import hashlib
import os
import shutil
import subprocess
import tempfile
from datetime import UTC, datetime
from pathlib import Path
from typing import Literal

import pandas as pd
import pyarrow as pa

from institutional_factor_platform.asset_pricing.config import AssetPricingConfig
from institutional_factor_platform.asset_pricing.inputs import build_research_panel
from institutional_factor_platform.asset_pricing.models import MODEL_SPECS, ModelSpec
from institutional_factor_platform.data.evidence import atomic_write_json, canonical_json_bytes
from institutional_factor_platform.data.storage import sha256_file
from institutional_factor_platform.diagnostics.regression import regression_diagnostics
from institutional_factor_platform.exceptions import DataQualityError, EvidenceIntegrityError
from institutional_factor_platform.factors.storage import FactorRepository
from institutional_factor_platform.regression.engine import fit_regression, window_regressions
from institutional_factor_platform.research_outputs.storage import (
    AssetPricingManifest,
    AssetPricingPublication,
    AssetPricingRepository,
    BoundArtifact,
    publish_parquet,
)


class AssetPricingResearchService:
    def __init__(
        self, config: AssetPricingConfig, project_root: Path, factor_repository: FactorRepository
    ) -> None:
        self.config = config
        self.root = project_root.resolve()
        self.factor_repository = factor_repository
        self.output_root = (self.root / config.publication.output_root).resolve()
        self.manifest_root = (self.root / config.publication.manifest_root).resolve()
        self.repository = AssetPricingRepository(self.root, self.manifest_root)

    def compute_and_publish(
        self,
        factor_publication_id: str,
        model_ids: tuple[str, ...] | None = None,
        *,
        custom_models: tuple[ModelSpec, ...] = (),
    ) -> AssetPricingManifest:
        phase2 = self.factor_repository.authenticate(factor_publication_id)
        custom_by_id = {spec.model_id: spec for spec in custom_models}
        if len(custom_by_id) != len(custom_models):
            raise DataQualityError("Custom model identifiers must be unique")
        if set(custom_by_id) & set(MODEL_SPECS):
            raise DataQualityError("Custom model identifiers cannot replace approved models")
        specifications = {**MODEL_SPECS, **custom_by_id}
        selected = tuple(sorted(model_ids or (*self.config.models, *custom_by_id)))
        approved = set(self.config.models) | set(custom_by_id)
        if not selected or set(selected) - approved:
            raise DataQualityError("Requested model set is empty or not approved by configuration")
        required_aliases = {
            factor
            for model_id in selected
            for factor in specifications[model_id].factors
            if factor != "market_excess"
        }
        missing_mappings = required_aliases - set(self.config.factor_mappings)
        if missing_mappings:
            raise DataQualityError(
                "Selected models lack configured Phase 2 mappings: "
                + ", ".join(sorted(missing_mappings))
            )
        selected_mappings = {
            alias: self.config.factor_mappings[alias] for alias in sorted(required_aliases)
        }
        factor_table = self.factor_repository.read_table(factor_publication_id).to_pandas()
        portfolio_table = self.factor_repository.read_portfolios(factor_publication_id).to_pandas()
        panel = build_research_panel(factor_table, portfolio_table, selected_mappings)
        git_commit = _git_commit(self.root)
        selected_specs = {model_id: specifications[model_id] for model_id in selected}
        publication_id = _publication_id(
            phase2.content_hash(),
            self.config.canonical_hash(),
            git_commit,
            selected_specs,
        )
        existing = self.manifest_root / publication_id / "asset-pricing-publication.json"
        if existing.is_file():
            return self.repository.authenticate(publication_id)

        coefficients: list[pd.DataFrame] = []
        residuals: list[pd.DataFrame] = []
        comparisons: list[dict[str, object]] = []
        rolling: list[pd.DataFrame] = []
        influences: list[pd.DataFrame] = []
        diagnostics: dict[str, object] = {"publication_id": publication_id, "models": {}}
        for asset_id, asset in panel.groupby("asset_id", sort=True):
            for model_id in selected:
                spec = specifications[model_id]
                result = fit_regression(
                    asset,
                    "excess_return",
                    spec.factors,
                    model_id=model_id,
                    covariance="HAC",
                    hac_lags=self.config.hac_lags,
                    confidence_level=self.config.confidence_level,
                    minimum_observations=self.config.minimum_observations,
                )
                coefficient = result.coefficients.assign(
                    asset_id=asset_id,
                    model_id=model_id,
                    nobs=result.nobs,
                    covariance=result.covariance,
                )
                coefficients.append(coefficient)
                residuals.append(
                    pd.DataFrame(
                        {
                            "asset_id": asset_id,
                            "model_id": model_id,
                            "date": asset.loc[result.residuals.index, "date"].to_numpy(),
                            "observed_excess_return": asset.loc[
                                result.residuals.index, "excess_return"
                            ].to_numpy(),
                            "fitted_return": result.fitted.to_numpy(),
                            "residual": result.residuals.to_numpy(),
                        }
                    )
                )
                comparisons.append(
                    {
                        "asset_id": asset_id,
                        "model_id": model_id,
                        "nobs": result.nobs,
                        **result.metrics,
                    }
                )
                diagnostic, influence = regression_diagnostics(result, asset, spec.factors)
                diagnostics["models"][f"{asset_id}|{model_id}"] = diagnostic  # type: ignore[index]
                influences.append(influence.assign(asset_id=asset_id, model_id=model_id))
                if len(asset) >= self.config.rolling_window:
                    rolling.append(
                        window_regressions(
                            asset,
                            "date",
                            "excess_return",
                            spec.factors,
                            window=self.config.rolling_window,
                            model_id=model_id,
                            covariance="HAC",
                            hac_lags=self.config.hac_lags,
                            confidence_level=self.config.confidence_level,
                            minimum_observations=self.config.minimum_observations,
                        ).assign(asset_id=asset_id, model_id=model_id, window_type="rolling")
                    )
                if len(asset) >= self.config.expanding_minimum:
                    rolling.append(
                        window_regressions(
                            asset,
                            "date",
                            "excess_return",
                            spec.factors,
                            window=self.config.expanding_minimum,
                            expanding=True,
                            model_id=model_id,
                            covariance="HAC",
                            hac_lags=self.config.hac_lags,
                            confidence_level=self.config.confidence_level,
                            minimum_observations=self.config.minimum_observations,
                        ).assign(asset_id=asset_id, model_id=model_id, window_type="expanding")
                    )

        coefficient_frame = pd.concat(coefficients, ignore_index=True)
        residual_frame = pd.concat(residuals, ignore_index=True)
        comparison_frame = pd.DataFrame(comparisons)
        rolling_frame = (
            pd.concat(rolling, ignore_index=True)
            if rolling
            else pd.DataFrame(
                columns=[
                    "window_end",
                    "window_start",
                    "term",
                    "estimate",
                    "standard_error",
                    "t_statistic",
                    "p_value",
                    "confidence_lower",
                    "confidence_upper",
                    "asset_id",
                    "model_id",
                    "window_type",
                ]
            )
        )
        influence_frame = pd.concat(influences, ignore_index=True)
        return self._publish(
            publication_id,
            phase2.publication_id,
            phase2.content_hash(),
            selected,
            panel,
            coefficient_frame,
            residual_frame,
            comparison_frame,
            rolling_frame,
            influence_frame,
            diagnostics,
            git_commit,
            selected_specs,
        )

    def _publish(
        self,
        publication_id: str,
        phase2_id: str,
        phase2_hash: str,
        model_ids: tuple[str, ...],
        panel: pd.DataFrame,
        coefficients: pd.DataFrame,
        residuals: pd.DataFrame,
        comparisons: pd.DataFrame,
        rolling: pd.DataFrame,
        influence: pd.DataFrame,
        diagnostics: dict[str, object],
        git_commit: str,
        model_specs: dict[str, ModelSpec],
    ) -> AssetPricingManifest:
        output = self.output_root / publication_id
        run_root = self.manifest_root / publication_id
        staging_parent = self.manifest_root / ".staging"
        staging_parent.mkdir(parents=True, exist_ok=True)
        staging = Path(tempfile.mkdtemp(prefix=f"{publication_id}-", dir=staging_parent))
        artifacts: list[BoundArtifact] = []
        try:
            for name, frame in (
                ("coefficients", coefficients),
                ("residuals", residuals),
                ("model_comparison", comparisons),
                ("rolling_coefficients", rolling),
                ("influence", influence),
            ):
                path = output / f"{name}.parquet"
                checksum, size = publish_parquet(
                    path, pa.Table.from_pandas(frame, preserve_index=False)
                )
                artifacts.append(
                    _artifact(
                        name, path, checksum, size, "application/vnd.apache.parquet", self.root
                    )
                )
            assumptions = {
                "publication_id": publication_id,
                "frequency": self.config.frequency,
                "return_unit": "decimal simple return",
                "dependent_variable": (
                    "portfolio simple return minus authenticated risk-free simple return"
                ),
                "factor_construction": (
                    "date-aligned high-minus-low Phase 2 quantile returns; "
                    "market excess from Phase 2 characteristic"
                ),
                "inference": f"Newey-West HAC with {self.config.hac_lags} lags",
                "confidence_level": self.config.confidence_level,
                "limitations": [
                    "Project-specific characteristic spreads are not official provider factors.",
                    "Statistical association is not causal evidence.",
                ],
                "model_specifications": {
                    model_id: {
                        "factors": spec.factors,
                        "equation": spec.equation,
                        "dependent_variable": spec.dependent_variable,
                        "frequency": spec.frequency,
                        "return_unit": spec.return_unit,
                    }
                    for model_id, spec in sorted(model_specs.items())
                },
            }
            validation = {
                "publication_id": publication_id,
                "status": "PASS",
                "coefficient_rows": len(coefficients),
                "residual_rows": len(residuals),
                "asset_count": int(panel["asset_id"].nunique()),
                "model_count": len(model_ids),
                "failure_count": 0,
            }
            configuration = {
                "publication_id": publication_id,
                "configuration_hash": self.config.canonical_hash(),
                "configuration": self.config.model_dump(mode="json"),
                "selected_model_specifications": {
                    model_id: {
                        "factors": spec.factors,
                        "dependent_variable": spec.dependent_variable,
                        "frequency": spec.frequency,
                        "return_unit": spec.return_unit,
                    }
                    for model_id, spec in sorted(model_specs.items())
                },
            }
            lineage = {
                "publication_id": publication_id,
                "phase2_publication_id": phase2_id,
                "phase2_manifest_hash": phase2_hash,
                "transformation": "phase3_authenticated_asset_pricing",
                "git_commit": git_commit,
                "configuration_hash": self.config.canonical_hash(),
            }
            for name, value in (
                ("diagnostics", diagnostics),
                ("assumptions", assumptions),
                ("validation", validation),
                ("configuration", configuration),
                ("lineage", lineage),
            ):
                staged = staging / f"{name}.json"
                atomic_write_json(staged, value)
                target = run_root / staged.name
                artifacts.append(
                    _artifact(
                        name,
                        target,
                        sha256_file(staged),
                        staged.stat().st_size,
                        "application/json",
                        self.root,
                    )
                )
            dates = pd.to_datetime(panel["date"])
            manifest = AssetPricingManifest(
                schema_version="1.0.0",
                publication_id=publication_id,
                created_at=datetime.now(UTC),
                phase2_publication_id=phase2_id,
                phase2_manifest_hash=phase2_hash,
                configuration_hash=self.config.canonical_hash(),
                git_commit=git_commit,
                model_ids=model_ids,
                asset_ids=tuple(sorted(panel["asset_id"].unique())),
                observation_start=dates.min().date().isoformat(),
                observation_end=dates.max().date().isoformat(),
                artifacts=tuple(artifacts),
                validation_status="PASS",
            )
            atomic_write_json(
                staging / "asset-pricing-manifest.json", manifest.model_dump(mode="json")
            )
            publication = AssetPricingPublication(
                schema_version="1.0.0",
                publication_id=publication_id,
                manifest_path=_relative(run_root / "asset-pricing-manifest.json", self.root),
                manifest_hash=manifest.content_hash(),
                configuration_hash=manifest.configuration_hash,
                git_commit=git_commit,
            )
            atomic_write_json(
                staging / "asset-pricing-publication.json", publication.model_dump(mode="json")
            )
            run_root.parent.mkdir(parents=True, exist_ok=True)
            os.replace(staging, run_root)
            return self.repository.authenticate(publication_id)
        except Exception:
            shutil.rmtree(staging, ignore_errors=True)
            raise


def _artifact(
    name: str,
    path: Path,
    checksum: str,
    size: int,
    media_type: Literal["application/json", "application/vnd.apache.parquet"],
    root: Path,
) -> BoundArtifact:
    return BoundArtifact(
        name=name,
        path=_relative(path, root),
        checksum=checksum,
        byte_size=size,
        media_type=media_type,
    )


def _relative(path: Path, root: Path) -> str:
    try:
        return path.resolve().relative_to(root).as_posix()
    except ValueError as exc:
        raise EvidenceIntegrityError(f"Phase 3 evidence path escapes project root: {path}") from exc


def _publication_id(
    parent_hash: str,
    config_hash: str,
    git_commit: str,
    models: dict[str, ModelSpec],
) -> str:
    digest = hashlib.sha256(
        canonical_json_bytes(
            {
                "phase2_manifest_hash": parent_hash,
                "configuration_hash": config_hash,
                "git_commit": git_commit,
                "models": {
                    model_id: {
                        "factors": spec.factors,
                        "dependent_variable": spec.dependent_variable,
                        "frequency": spec.frequency,
                        "return_unit": spec.return_unit,
                    }
                    for model_id, spec in sorted(models.items())
                },
                "engine_version": "1.0.0",
            }
        )
    ).hexdigest()
    return f"asset-pricing-{digest[:32]}"


def _git_commit(root: Path) -> str:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=root, text=True, stderr=subprocess.DEVNULL
        ).strip()
    except (OSError, subprocess.CalledProcessError) as exc:
        raise EvidenceIntegrityError(
            "Phase 3 publication requires an available Git commit"
        ) from exc
