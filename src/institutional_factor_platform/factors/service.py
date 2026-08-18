"""Orchestration for reproducible, immutable Phase 2 factor research publications."""

import hashlib
import os
import subprocess
import tempfile
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

from institutional_factor_platform.data.access import VerifiedDatasetHandle
from institutional_factor_platform.data.evidence import atomic_write_json, canonical_json_bytes
from institutional_factor_platform.data.storage import sha256_file
from institutional_factor_platform.exceptions import DataQualityError, EvidenceIntegrityError
from institutional_factor_platform.factors.config import FactorConfig
from institutional_factor_platform.factors.contracts import (
    FACTOR_PORTFOLIO_SCHEMA,
    FACTOR_SCHEMA,
    MARKET_REQUIRED_UNITS,
    REQUIRED_FUNDAMENTAL_FIELDS,
)
from institutional_factor_platform.factors.definitions import (
    FACTOR_DEFINITIONS,
    FACTOR_VERSION,
    compute_characteristics,
)
from institutional_factor_platform.factors.diagnostics import build_factor_diagnostics
from institutional_factor_platform.factors.portfolio import (
    compute_factor_portfolios,
    validate_factor_portfolios,
)
from institutional_factor_platform.factors.preprocessing import preprocess_characteristics
from institutional_factor_platform.factors.storage import (
    FactorManifest,
    FactorMetadata,
    FactorPublication,
    FactorRepository,
    ParentDatasetEvidence,
    publish_factor_parquet,
    schema_fingerprint,
)
from institutional_factor_platform.factors.temporal import (
    point_in_time_panel,
    validate_fundamental_input,
    validate_market_input,
)
from institutional_factor_platform.factors.validation import validate_factor_output


@dataclass(frozen=True, slots=True)
class FactorRunResult:
    publication_id: str
    manifest_path: Path
    publication_path: Path
    row_count: int
    validation_status: str


class FactorResearchService:
    """Build factors only from explicitly authenticated Phase 1 parent handles."""

    def __init__(self, config: FactorConfig, project_root: Path) -> None:
        self.config = config
        self.root = project_root.resolve()
        self.output_root = (self.root / config.publication.output_root).resolve()
        self.manifest_root = (self.root / config.publication.manifest_root).resolve()
        self.repository = FactorRepository(self.root, self.manifest_root)

    def compute_and_publish(
        self,
        parents: tuple[VerifiedDatasetHandle, ...],
        *,
        market_dataset_id: str,
        fundamental_dataset_id: str,
    ) -> FactorRunResult:
        """Read the exact authenticated parent artifacts; callers cannot inject data frames."""
        _authenticate_parents(parents)
        by_id = {parent.dataset_id: parent for parent in parents}
        if market_dataset_id == fundamental_dataset_id or set(by_id) != {
            market_dataset_id,
            fundamental_dataset_id,
        }:
            raise EvidenceIntegrityError(
                "Factor publication requires exactly its market and fundamental parent artifacts."
            )
        try:
            market_parent = by_id[market_dataset_id]
            fundamental_parent = by_id[fundamental_dataset_id]
        except KeyError as exc:
            raise EvidenceIntegrityError(
                "Factor input roles must identify supplied authenticated parents."
            ) from exc
        return self._compute_and_publish(
            parents,
            _read_parent_table(market_parent).to_pandas(),
            _read_parent_table(fundamental_parent).to_pandas(),
            market_units=market_parent.unit_metadata,
            fundamental_units=fundamental_parent.unit_metadata,
            market_dataset_id=market_dataset_id,
            fundamental_dataset_id=fundamental_dataset_id,
        )

    def _compute_and_publish(
        self,
        parents: tuple[VerifiedDatasetHandle, ...],
        market: pd.DataFrame,
        fundamentals: pd.DataFrame,
        *,
        market_units: dict[str, str],
        fundamental_units: dict[str, str],
        market_dataset_id: str,
        fundamental_dataset_id: str,
    ) -> FactorRunResult:
        parent_evidence = _authenticate_parents(parents)
        parent_ids = {parent.dataset_id for parent in parents}
        _validate_units(market_units, fundamentals, fundamental_units)
        market_value = validate_market_input(market, self.config.plausibility)
        fundamental_value = validate_fundamental_input(fundamentals)
        market_source_ids = (market_dataset_id,)
        fundamental_source_ids = (fundamental_dataset_id,)
        eligible_market = market_value.loc[market_value["eligible"]].copy()
        if eligible_market.empty:
            raise DataQualityError(
                "No securities are point-in-time eligible for factor computation."
            )
        panel = point_in_time_panel(eligible_market, fundamental_value)
        characteristics = compute_characteristics(panel, self.config)
        factor_ids = tuple(item.factor_id for item in FACTOR_DEFINITIONS)
        output = preprocess_characteristics(characteristics, factor_ids, self.config.preprocessing)
        portfolios = compute_factor_portfolios(
            output,
            characteristics,
            eligible_market,
            quantiles=self.config.portfolios.quantiles,
            rebalancing=self.config.rebalancing,
        )
        validate_factor_portfolios(portfolios, self.config.portfolios.quantiles)
        diagnostics = build_factor_diagnostics(
            output, portfolios, self.config.portfolios.rolling_periods
        )
        git_commit = _git_commit(self.root)
        publication_id = _publication_id(
            parent_evidence,
            self.config.canonical_hash(),
            git_commit,
        )
        diagnostics["publication_id"] = publication_id
        existing_publication = self.manifest_root / publication_id / "factor-publication.json"
        if existing_publication.is_file():
            manifest = self.repository.authenticate(publication_id)
            return FactorRunResult(
                publication_id,
                self.manifest_root / publication_id / "factor-manifest.json",
                existing_publication,
                manifest.row_count,
                manifest.validation_status,
            )
        report = validate_factor_output(output, publication_id)
        if report.status == "FAIL":
            raise DataQualityError("Factor validation failed; publication is forbidden.")
        approved_status = report.status
        run_root = self.manifest_root / publication_id
        artifact_path = self.output_root / publication_id / "factors.parquet"
        portfolio_artifact_path = self.output_root / publication_id / "factor-portfolios.parquet"
        snapshot_path = run_root / "configuration.json"
        validation_path = run_root / "validation.json"
        lineage_path = run_root / "lineage.json"
        diagnostics_path = run_root / "diagnostics.json"
        manifest_path = run_root / "factor-manifest.json"
        publication_path = run_root / "factor-publication.json"
        staging_parent = self.manifest_root / ".staging"
        staging_parent.mkdir(parents=True, exist_ok=True)
        staging_root = Path(tempfile.mkdtemp(prefix=f"{publication_id}-", dir=staging_parent))
        staged_snapshot = staging_root / snapshot_path.name
        staged_validation = staging_root / validation_path.name
        staged_diagnostics = staging_root / diagnostics_path.name
        staged_lineage = staging_root / lineage_path.name
        staged_manifest = staging_root / manifest_path.name
        staged_publication = staging_root / publication_path.name
        self.config.write_snapshot(staged_snapshot)
        atomic_write_json(staged_validation, report.model_dump(mode="json"))
        atomic_write_json(staged_diagnostics, diagnostics)
        table = pa.Table.from_pandas(output, schema=FACTOR_SCHEMA, preserve_index=False, safe=True)
        artifact_checksum, artifact_size = publish_factor_parquet(artifact_path, table)
        portfolio_table = pa.Table.from_pandas(
            portfolios, schema=FACTOR_PORTFOLIO_SCHEMA, preserve_index=False, safe=True
        )
        portfolio_checksum, portfolio_size = publish_factor_parquet(
            portfolio_artifact_path, portfolio_table, schema=FACTOR_PORTFOLIO_SCHEMA
        )
        created_at = datetime.now(UTC)
        lineage = {
            "schema_version": "1.0.0",
            "publication_id": publication_id,
            "parent_dataset_ids": sorted(parent_ids),
            "market_source_dataset_ids": market_source_ids,
            "fundamental_source_dataset_ids": fundamental_source_ids,
            "parent_artifact_checksums": sorted(
                parent.artifact_checksum for parent in parent_evidence
            ),
            "artifact_checksum": artifact_checksum,
            "portfolio_artifact_checksum": portfolio_checksum,
            "transformation": "phase2_point_in_time_factor_engine",
            "transformation_version": FACTOR_VERSION,
            "universe_policy": "explicit_point_in_time_eligibility_only",
            "excluded_ineligible_rows": int((~market_value["eligible"]).sum()),
            "configuration_hash": self.config.canonical_hash(),
            "git_commit": git_commit,
            "created_at": created_at.isoformat(),
        }
        atomic_write_json(staged_lineage, lineage)
        metadata = tuple(
            FactorMetadata(
                factor_id=item.factor_id,
                definition=item.definition,
                formula=item.formula,
                economic_rationale=item.rationale,
                required_inputs=item.required_inputs,
                unit=item.unit,
                direction=item.direction,  # type: ignore[arg-type]
                transformation_chain=(
                    "point_in_time_alignment@1.0.0",
                    f"winsorize@{self.config.preprocessing.winsor_lower:.4f}/"
                    f"{self.config.preprocessing.winsor_upper:.4f}",
                    f"{self.config.preprocessing.method}@1.0.0",
                    f"neutralize:{self.config.preprocessing.neutralize_by}@1.0.0",
                    f"direction:{item.direction:+d}@1.0.0",
                ),
                dependencies=tuple(parent.dataset_id for parent in parent_evidence),
                version=FACTOR_VERSION,
                research_notes=item.research_notes,
            )
            for item in FACTOR_DEFINITIONS
        )
        dates = pd.to_datetime(output["date"])
        manifest = FactorManifest(
            schema_version="1.0.0",
            publication_id=publication_id,
            created_at=created_at,
            factor_version=FACTOR_VERSION,
            artifact_path=_relative(artifact_path, self.root),
            artifact_checksum=artifact_checksum,
            artifact_byte_size=artifact_size,
            schema_fingerprint=schema_fingerprint(),
            portfolio_artifact_path=_relative(portfolio_artifact_path, self.root),
            portfolio_artifact_checksum=portfolio_checksum,
            portfolio_artifact_byte_size=portfolio_size,
            portfolio_schema_fingerprint=schema_fingerprint(FACTOR_PORTFOLIO_SCHEMA),
            portfolio_row_count=len(portfolios),
            row_count=len(output),
            security_count=output["security_id"].nunique(),
            date_start=dates.min().date().isoformat(),
            date_end=dates.max().date().isoformat(),
            factor_ids=factor_ids,
            parents=parent_evidence,
            market_source_dataset_ids=market_source_ids,
            fundamental_source_dataset_ids=fundamental_source_ids,
            configuration_hash=self.config.canonical_hash(),
            configuration_snapshot_path=_relative(snapshot_path, self.root),
            configuration_snapshot_checksum=sha256_file(staged_snapshot),
            validation_report_path=_relative(validation_path, self.root),
            validation_report_checksum=sha256_file(staged_validation),
            validation_status=approved_status,
            diagnostics_path=_relative(diagnostics_path, self.root),
            diagnostics_checksum=sha256_file(staged_diagnostics),
            lineage_path=_relative(lineage_path, self.root),
            lineage_checksum=sha256_file(staged_lineage),
            git_commit=git_commit,
            metadata=metadata,
        )
        atomic_write_json(staged_manifest, manifest.model_dump(mode="json"))
        publication = FactorPublication(
            schema_version="1.0.0",
            publication_id=publication_id,
            manifest_path=_relative(manifest_path, self.root),
            manifest_hash=manifest.content_hash(),
            artifact_checksum=artifact_checksum,
            git_commit=manifest.git_commit,
            configuration_hash=manifest.configuration_hash,
        )
        atomic_write_json(staged_publication, publication.model_dump(mode="json"))
        run_root.parent.mkdir(parents=True, exist_ok=True)
        _activate_publication(staging_root, run_root, self.repository, publication_id)
        self.repository.read_table(publication_id)
        return FactorRunResult(
            publication_id,
            manifest_path,
            publication_path,
            len(output),
            report.status,
        )


def _authenticate_parents(
    parents: tuple[VerifiedDatasetHandle, ...],
) -> tuple[ParentDatasetEvidence, ...]:
    if not parents:
        raise EvidenceIntegrityError("Factor computation requires authenticated Phase 1 parents.")
    if len({parent.dataset_id for parent in parents}) != len(parents):
        raise EvidenceIntegrityError("Factor parent dataset identities must be unique.")
    evidence: list[ParentDatasetEvidence] = []
    for parent in parents:
        if (
            parent.lifecycle_state != "FINALIZED"
            or parent.validation_status.value not in {"PASS", "PASS_WITH_WARNINGS"}
            or parent.mapping_status not in {"RESOLVED", "NOT_APPLICABLE"}
            or not parent.artifact_path.is_file()
            or sha256_file(parent.artifact_path) != parent.checksum
        ):
            raise EvidenceIntegrityError(f"Factor parent is not authenticated: {parent.dataset_id}")
        evidence.append(
            ParentDatasetEvidence(
                dataset_id=parent.dataset_id,
                artifact_checksum=parent.checksum,
                lineage_id=parent.lineage_id,
                promotion_id=parent.promotion_id,
                run_id=parent.run_id,
                validation_status=parent.validation_status.value,
                schema_version=parent.schema_version,
                unit_metadata=parent.unit_metadata,
                configuration_hash=parent.configuration_hash,
                git_commit=parent.git_commit,
                mapping_status=parent.mapping_status,
                mapping_evidence_id=parent.mapping_evidence_id,
                temporal_policy=parent.temporal_policy,
            )
        )
    return tuple(sorted(evidence, key=lambda item: item.dataset_id))


def _read_parent_table(parent: VerifiedDatasetHandle) -> pa.Table:
    try:
        content = parent.artifact_path.read_bytes()
    except OSError as exc:
        raise EvidenceIntegrityError(f"Factor parent cannot be read: {parent.dataset_id}") from exc
    if hashlib.sha256(content).hexdigest() != parent.checksum:
        raise EvidenceIntegrityError(
            f"Factor parent changed before authenticated parsing: {parent.dataset_id}"
        )
    try:
        return pq.read_table(pa.BufferReader(content))
    except pa.ArrowException as exc:
        raise EvidenceIntegrityError(
            f"Factor parent is not a readable Parquet artifact: {parent.dataset_id}"
        ) from exc


def _validate_units(
    market_units: dict[str, str],
    fundamentals: pd.DataFrame,
    fundamental_units: dict[str, str],
) -> None:
    normalized_market_units = _extract_units(market_units, set(MARKET_REQUIRED_UNITS))
    if normalized_market_units != MARKET_REQUIRED_UNITS:
        raise DataQualityError(
            "Market units must exactly match the approved Phase 2 decimal/USD/share contract."
        )
    fields = set(fundamentals["field"]) if "field" in fundamentals else set()
    if not fields:
        raise DataQualityError("Fundamental inputs must contain at least one approved field.")
    unsupported = fields - REQUIRED_FUNDAMENTAL_FIELDS
    if unsupported:
        raise DataQualityError(
            "Fundamental inputs contain fields outside the approved Phase 2 vocabulary: "
            + ", ".join(sorted(unsupported))
        )
    normalized_fundamental_units = _extract_units(fundamental_units, fields)
    if set(normalized_fundamental_units) != fields:
        raise DataQualityError("Fundamental unit declarations must exactly cover observed fields.")
    for field_name, declared in normalized_fundamental_units.items():
        if declared != "USD":
            raise DataQualityError(f"Fundamental field {field_name} must use the USD contract.")
        observed = set(fundamentals.loc[fundamentals["field"].eq(field_name), "unit"])
        if observed != {declared}:
            raise DataQualityError(f"Fundamental unit contradiction for {field_name}.")


def _extract_units(metadata: dict[str, str], fields: set[str]) -> dict[str, str]:
    extracted: dict[str, str] = {}
    for field_name in fields:
        values = {
            metadata[key]
            for key in (
                field_name,
                f"request.{field_name}",
                f"contract.{field_name}",
                f"standardized.{field_name}",
            )
            if key in metadata
        }
        if len(values) == 1:
            extracted[field_name] = values.pop()
        elif len(values) > 1:
            raise DataQualityError(f"Contradictory unit evidence for {field_name}.")
    return extracted


def _publication_id(
    parents: tuple[ParentDatasetEvidence, ...],
    configuration_hash: str,
    git_commit: str,
) -> str:
    payload = {
        "parents": [parent.model_dump(mode="json") for parent in parents],
        "configuration_hash": configuration_hash,
        "factor_version": FACTOR_VERSION,
        "git_commit": git_commit,
    }
    digest = hashlib.sha256(canonical_json_bytes(payload)).hexdigest()
    return f"factor-{digest[:32]}"


def _relative(path: Path, root: Path) -> str:
    try:
        return path.resolve().relative_to(root).as_posix()
    except ValueError as exc:
        raise EvidenceIntegrityError(f"Factor evidence path escapes project root: {path}") from exc


def _activate_publication(
    staging_root: Path,
    run_root: Path,
    repository: FactorRepository,
    publication_id: str,
) -> None:
    try:
        os.replace(staging_root, run_root)
    except OSError:
        # A concurrent identical run may have won the atomic publication race.
        repository.authenticate(publication_id)


def _git_commit(root: Path) -> str:
    for candidate in (root, Path.cwd()):
        try:
            return subprocess.check_output(
                ["git", "rev-parse", "HEAD"],
                cwd=candidate,
                text=True,
                stderr=subprocess.DEVNULL,
            ).strip()
        except (OSError, subprocess.CalledProcessError):
            continue
    raise EvidenceIntegrityError("Factor publication requires an available Git commit.")
