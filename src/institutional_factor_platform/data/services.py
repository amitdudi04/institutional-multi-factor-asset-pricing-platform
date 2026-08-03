"""Phase 1 orchestration across adapters, storage, validation, manifests, and catalog."""

import io
import json
import subprocess
import uuid
from datetime import UTC, date, datetime
from pathlib import Path
from typing import Any

import pandas as pd
import pyarrow as pa

from institutional_factor_platform import __version__
from institutional_factor_platform.data.config import Phase1Config
from institutional_factor_platform.data.contracts import TableContract
from institutional_factor_platform.data.domain import (
    DatasetStatus,
    RetrievalRequest,
    RetrievalStatus,
)
from institutional_factor_platform.data.manifests import (
    DatasetManifest,
    RunManifest,
    SourceManifest,
)
from institutional_factor_platform.data.sources.base import SourceAdapter
from institutional_factor_platform.data.storage import (
    DuckDBCatalog,
    ParquetStorage,
    QuarantineStorage,
    RawStorage,
)
from institutional_factor_platform.data.validation import (
    ValidationReport,
    status_from_results,
    validate_daily_market,
    validate_french_factors,
    validate_macro,
    validate_sec_facts,
    validate_table,
)
from institutional_factor_platform.exceptions import DataQualityError, PartialRetrievalError
from institutional_factor_platform.project import find_project_root


class DataIngestionService:
    def __init__(self, config: Phase1Config, root: Path | None = None) -> None:
        self.config = config
        self.root = (root or find_project_root()).resolve()
        paths = config.paths.resolved(self.root)
        self.paths = paths
        self.raw = RawStorage(paths["raw"])
        self.parquet = ParquetStorage(paths["processed"], config.storage.parquet_compression)
        self.quarantine = QuarantineStorage(paths["quarantine"])
        self.catalog = DuckDBCatalog(paths["duckdb"])

    def initialize_storage(self) -> tuple[Path, ...]:
        directories = tuple(
            self.paths[name]
            for name in (
                "raw",
                "interim",
                "processed",
                "manifests",
                "quarantine",
                "data_quality",
                "metadata",
                "logs",
            )
        )
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
        self.catalog.initialize()
        return directories

    def ingest(
        self,
        adapter: SourceAdapter[Any],
        request: RetrievalRequest,
        contract: TableContract,
        extension: str,
        media_type: str,
    ) -> DatasetManifest:
        self.initialize_storage()
        run_id = str(uuid.uuid4())
        started = datetime.now(UTC)
        config_hash = self.config.configuration_hash()
        snapshot = self.paths["manifests"] / run_id / "configuration.json"
        self.config.write_snapshot(snapshot)
        run_path = self.paths["manifests"] / run_id / "run.json"
        source_path = self.paths["manifests"] / run_id / "source.json"
        artifact = None
        try:
            payload = adapter.retrieve(request)
            raw_bytes = _payload_bytes(payload)
            artifact = self.raw.persist(
                source=request.source,
                dataset=request.dataset,
                content=raw_bytes,
                extension=extension,
                media_type=media_type,
                retrieved_at=started,
            )
            records = adapter.standardize(payload, request)
            table = pa.Table.from_pylist(list(records), schema=contract.schema)
            findings = list(validate_table(table, contract))
            if contract.name == "daily_market":
                findings.extend(
                    validate_daily_market(
                        list(records),
                        stale_sessions=self.config.validation.stale_price_sessions,
                        extreme_return_threshold=self.config.validation.extreme_return_threshold,
                    )
                )
            elif contract.name == "macro_observations":
                findings.extend(validate_macro(list(records)))
            elif contract.name == "french_factors":
                findings.extend(validate_french_factors(list(records)))
            elif contract.name == "sec_facts":
                findings.extend(validate_sec_facts(list(records)))
            status = status_from_results(findings)
            report = ValidationReport(
                dataset_id=f"{contract.name}-{artifact.checksum[:12]}",
                source=request.source.value,
                run_id=run_id,
                schema_version=contract.version,
                row_count=table.num_rows,
                entity_count=_entity_count(records),
                requested_start=request.date_range.start.isoformat()
                if request.date_range
                else None,
                requested_end=request.date_range.end.isoformat() if request.date_range else None,
                observed_start=_observed_date(records, minimum=True),
                observed_end=_observed_date(records, minimum=False),
                results=tuple(findings),
                final_status=status,
            )
            quality_base = self.paths["data_quality"] / run_id
            report.write(quality_base / "validation.json", quality_base / "validation.md")
            source_manifest = self._source_manifest(
                request, artifact, table.num_rows, RetrievalStatus.SUCCESS
            )
            source_manifest.write_immutable(source_path)
            if status in {DatasetStatus.QUARANTINED, DatasetStatus.FAIL}:
                location = self.quarantine.quarantine(
                    artifact, "Blocking validation failure", {"status": status.value}
                )
                raise DataQualityError(
                    f"Dataset {contract.name} blocked and quarantined at {location}"
                )
            dataset_id = f"{contract.name}-{artifact.checksum[:16]}"
            parquet_path, _ = self.parquet.write(contract.name, dataset_id, table, contract.schema)
            manifest = DatasetManifest(
                schema_version=self.config.manifests.schema_version,
                dataset_id=dataset_id,
                dataset_type=contract.name,
                schema_name=contract.name,
                parent_artifacts=(artifact.checksum,),
                transformation_name=f"{request.source.value}_standardize",
                transformation_version="1.0.0",
                row_count=table.num_rows,
                column_count=table.num_columns,
                primary_key=contract.primary_key,
                date_start=report.observed_start,
                date_end=report.observed_end,
                security_count=report.entity_count,
                missingness_summary={name: table[name].null_count for name in table.column_names},
                validation_status=status,
                quarantine_status=False,
                parquet_path=_relative(parquet_path, self.root),
                duckdb_registered=True,
                creation_time=datetime.now(UTC),
                configuration_hash=config_hash,
                code_version=__version__,
                lineage_references=(source_manifest.content_hash(),),
            )
            dataset_path = self.paths["manifests"] / run_id / "dataset.json"
            self.catalog.register(
                dataset_id, contract.name, parquet_path, dataset_path, status.value
            )
            manifest.write_immutable(dataset_path)
            self._write_run(
                run_path, run_id, started, "SUCCESS", config_hash, snapshot, request, (dataset_id,)
            )
            return manifest
        except Exception as exc:
            if artifact is not None and not source_path.exists():
                retrieval_status = (
                    RetrievalStatus.PARTIAL
                    if isinstance(exc, PartialRetrievalError)
                    else RetrievalStatus.FAILED
                )
                self._source_manifest(
                    request,
                    artifact,
                    0,
                    retrieval_status,
                    partial_failures=(str(exc),),
                ).write_immutable(source_path)
            self._write_run(
                run_path, run_id, started, "FAILED", config_hash, snapshot, request, (), (str(exc),)
            )
            raise

    def _source_manifest(
        self,
        request: RetrievalRequest,
        artifact: Any,
        rows: int,
        status: RetrievalStatus,
        partial_failures: tuple[str, ...] = (),
    ) -> SourceManifest:
        return SourceManifest(
            schema_version=self.config.manifests.schema_version,
            source=request.source.value,
            request={
                "dataset": request.dataset,
                "identifiers": list(request.identifiers),
                "date_start": request.date_range.start.isoformat() if request.date_range else None,
                "date_end": request.date_range.end.isoformat() if request.date_range else None,
            },
            retrieval_time=artifact.retrieval_timestamp,
            response_status=status,
            raw_artifact_path=_relative(artifact.path, self.root),
            checksum=artifact.checksum,
            row_count=rows,
            date_start=request.date_range.start.isoformat() if request.date_range else None,
            date_end=request.date_range.end.isoformat() if request.date_range else None,
            partial_failures=partial_failures,
            source_terms_note=(
                "External source terms apply; repository MIT license does not cover source data."
            ),
        )

    def _write_run(
        self,
        path: Path,
        run_id: str,
        started: datetime,
        status: str,
        config_hash: str,
        snapshot: Path,
        request: RetrievalRequest,
        outputs: tuple[str, ...],
        errors: tuple[str, ...] = (),
    ) -> None:
        manifest = RunManifest(
            schema_version=self.config.manifests.schema_version,
            run_id=run_id,
            run_type="data_ingestion",
            start_time=started,
            completion_time=datetime.now(UTC),
            status=status,  # type: ignore[arg-type]
            code_version=__version__,
            git_commit=_git_commit(self.root),
            configuration_hash=config_hash,
            configuration_snapshot_path=_relative(snapshot, self.root),
            environment_version=f"institutional-factor-platform {__version__}",
            requested_sources=(request.source.value,),
            requested_datasets=(request.dataset,),
            output_artifacts=outputs,
            errors=errors,
        )
        if path.exists():
            path.unlink()
        manifest.write_immutable(path)


def _payload_bytes(payload: Any) -> bytes:
    if isinstance(payload, bytes):
        return payload
    if isinstance(payload, pd.DataFrame):
        buffer = io.StringIO()
        payload.to_csv(buffer)
        return buffer.getvalue().encode()
    return json.dumps(payload, sort_keys=True, default=str).encode()


def _relative(path: Path, root: Path) -> str:
    try:
        return path.resolve().relative_to(root).as_posix()
    except ValueError:
        return str(path.resolve())


def _git_commit(root: Path) -> str:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "HEAD"],
            cwd=root,
            text=True,
            stderr=subprocess.DEVNULL,
        ).strip()
    except (OSError, subprocess.CalledProcessError):
        return "unavailable"


def _entity_count(records: tuple[dict[str, object], ...]) -> int | None:
    values = {str(row.get("security_id")) for row in records if row.get("security_id")}
    return len(values) if values else None


def _observed_date(records: tuple[dict[str, object], ...], *, minimum: bool) -> str | None:
    keys = ("trading_date", "observation_date", "factor_date", "period_end")
    values = [
        value
        for row in records
        for key in keys
        if isinstance((value := row.get(key)), (date, datetime))
    ]
    if not values:
        return None
    result = min(values) if minimum else max(values)
    return result.isoformat() if hasattr(result, "isoformat") else str(result)
