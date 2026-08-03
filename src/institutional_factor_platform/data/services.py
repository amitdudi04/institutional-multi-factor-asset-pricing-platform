"""Controlled Phase 1 publication across raw, validation, lineage, manifests, and catalog."""

import hashlib
import io
import json
import subprocess
import uuid
from datetime import UTC, date, datetime
from pathlib import Path
from typing import Any, Literal

import pandas as pd
import pyarrow as pa
import pyarrow.ipc as ipc

from institutional_factor_platform import __version__
from institutional_factor_platform.data.calendar import USEquityCalendar
from institutional_factor_platform.data.config import Phase1Config
from institutional_factor_platform.data.contracts import TableContract
from institutional_factor_platform.data.domain import (
    DataArtifact,
    DatasetStatus,
    RetrievalRequest,
    RetrievalStatus,
)
from institutional_factor_platform.data.lineage import (
    LineageDocument,
    LineageEdge,
    LineageStore,
    RelationshipType,
)
from institutional_factor_platform.data.manifests import (
    DatasetManifest,
    PromotionManifest,
    RunManifest,
    SourceManifest,
)
from institutional_factor_platform.data.sources.base import SourceAdapter
from institutional_factor_platform.data.storage import (
    DuckDBCatalog,
    ParquetStorage,
    QuarantineStorage,
    RawStorage,
    sha256_file,
)
from institutional_factor_platform.data.validation import (
    ValidationReport,
    enrich_findings,
    status_from_results,
    validate_daily_market,
    validate_french_factors,
    validate_macro,
    validate_market_coverage,
    validate_sec_facts,
    validate_table,
)
from institutional_factor_platform.exceptions import DataQualityError, PartialRetrievalError
from institutional_factor_platform.project import find_project_root

TRANSFORMATION_VERSION = "2.0.0"
TEMPORAL_POLICY_VERSION = "2.0.0"
_NO_PAYLOAD = object()


class DataIngestionService:
    def __init__(self, config: Phase1Config, root: Path | None = None) -> None:
        self.config = config
        self.root = (root or find_project_root()).resolve()
        self.paths = config.paths.resolved(self.root)
        self.raw = RawStorage(self.paths["raw"])
        self.parquet = ParquetStorage(self.paths["processed"], config.storage.parquet_compression)
        self.quarantine = QuarantineStorage(self.paths["quarantine"])
        self.catalog = DuckDBCatalog(self.paths["duckdb"])

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
        *,
        _payload_override: Any = _NO_PAYLOAD,
        _artifact_override: DataArtifact | None = None,
    ) -> DatasetManifest:
        self.initialize_storage()
        run_id = str(uuid.uuid4())
        started = datetime.now(UTC)
        commit = _git_commit(self.root)
        config_hash = self.config.configuration_hash()
        run_root = self.paths["manifests"] / run_id
        snapshot = run_root / "configuration.json"
        self.config.write_snapshot(snapshot)
        self._write_run(
            run_root / "run-started.json",
            run_id,
            started,
            "RUNNING",
            config_hash,
            snapshot,
            request,
            commit,
        )
        source_path = run_root / "source.json"
        source_id = f"source:{run_id}"
        artifact: DataArtifact | None = None
        promoted_dataset: str | None = None
        try:
            payload = (
                adapter.retrieve(request) if _payload_override is _NO_PAYLOAD else _payload_override
            )
            artifact = _artifact_override or self.raw.persist(
                source=request.source,
                dataset=request.dataset,
                content=_payload_bytes(payload),
                extension=extension,
                media_type=media_type,
                retrieved_at=started,
            )
            RawStorage.verify(artifact)
            records = adapter.standardize(payload, request)
            _require_exact_record_columns(records, contract)
            table = pa.Table.from_pylist(list(records), schema=contract.schema)
            findings = self._validate(records, table, contract, request)
            dataset_seed = _artifact_seed(
                request, contract, artifact.checksum, config_hash, _table_hash(table)
            )
            dataset_id = f"{contract.name}-{dataset_seed[:24]}"
            findings = enrich_findings(
                findings,
                dataset_id=dataset_id,
                source=request.source.value,
                timestamp=datetime.now(UTC),
            )
            status = status_from_results(findings)
            report = ValidationReport(
                dataset_id=dataset_id,
                source=request.source.value,
                run_id=run_id,
                schema_version=self.config.validation.schema_version,
                row_count=table.num_rows,
                entity_count=_entity_count(records),
                requested_start=_requested_date(request, True),
                requested_end=_requested_date(request, False),
                observed_start=_observed_date(records, minimum=True),
                observed_end=_observed_date(records, minimum=False),
                results=findings,
                final_status=status,
            )
            quality_base = self.paths["data_quality"] / run_id
            validation_json = quality_base / "validation.json"
            validation_md = quality_base / "validation.md"
            report.write(validation_json, validation_md)
            validation_id = f"validation:{sha256_file(validation_json)}"
            source_manifest = self._source_manifest(
                source_id, request, artifact, table.num_rows, records, RetrievalStatus.SUCCESS
            )
            source_manifest.write_immutable(source_path)
            if status in {DatasetStatus.QUARANTINED, DatasetStatus.FAIL}:
                location = self.quarantine.quarantine(
                    artifact,
                    "Blocking validation failure",
                    {"status": status.value, "validation_report": str(validation_json)},
                )
                raise DataQualityError(
                    f"Dataset {contract.name} blocked and quarantined at {location}"
                )

            published = self.parquet.publish(contract.name, dataset_id, table, contract.schema)
            self.parquet.verify(published)
            parquet_id = f"parquet:{published.checksum}"
            raw_id = f"raw:{artifact.checksum}"
            lineage_path = run_root / "lineage.json"
            lineage = _lineage_document(
                run_id=run_id,
                source_id=source_id,
                raw_id=raw_id,
                validation_id=validation_id,
                parquet_id=parquet_id,
                dataset_id=dataset_id,
                source_path=_relative(source_path, self.root),
                validation_path=_relative(validation_json, self.root),
                parquet_path=_relative(published.path, self.root),
                commit=commit,
                config_hash=config_hash,
            )
            lineage_store = LineageStore(lineage_path)
            lineage_store.persist(lineage)
            lineage_store.verify_complete(
                (source_id, raw_id, validation_id, parquet_id, dataset_id)
            )

            manifest = DatasetManifest(
                schema_version="2.0.0",
                dataset_id=dataset_id,
                dataset_type=contract.name,
                schema_name=contract.name,
                schema_fingerprint=_schema_fingerprint(contract.schema),
                parent_artifacts=(raw_id,),
                source_manifest_id=source_id,
                transformation_name=f"{request.source.value}_standardize",
                transformation_version=TRANSFORMATION_VERSION,
                row_count=table.num_rows,
                column_count=table.num_columns,
                primary_key=contract.primary_key,
                date_start=report.observed_start,
                date_end=report.observed_end,
                security_count=report.entity_count,
                missingness_summary={name: table[name].null_count for name in table.column_names},
                unit_metadata=_unit_metadata(records),
                validation_report_id=validation_id,
                validation_report_path=_relative(validation_json, self.root),
                validation_status=status,
                lineage_path=_relative(lineage_path, self.root),
                lineage_complete=True,
                quarantine_status=False,
                parquet_path=_relative(published.path, self.root),
                output_checksum=published.checksum,
                output_byte_size=published.byte_size,
                catalog_registration_state="NOT_REGISTERED",
                promotion_state="ELIGIBLE",
                creation_time=datetime.now(UTC),
                configuration_hash=config_hash,
                code_version=__version__,
                git_commit=commit,
                temporal_policy_version=TEMPORAL_POLICY_VERSION,
            )
            dataset_path = run_root / "dataset.json"
            manifest.write_immutable(dataset_path)
            self.catalog.promote(manifest, dataset_path, lineage_path, published.path)
            promoted_dataset = dataset_id
            promotion = PromotionManifest(
                schema_version="2.0.0",
                dataset_id=dataset_id,
                dataset_manifest_path=_relative(dataset_path, self.root),
                dataset_manifest_hash=manifest.content_hash(),
                output_checksum=published.checksum,
                lineage_path=_relative(lineage_path, self.root),
                validation_status=status,
                promoted_at=datetime.now(UTC),
                git_commit=commit,
                configuration_hash=config_hash,
            )
            promotion_path = run_root / "promotion.json"
            promotion.write_immutable(promotion_path)
            self._write_run(
                run_root / "run.json",
                run_id,
                started,
                "SUCCESS",
                config_hash,
                snapshot,
                request,
                commit,
                (dataset_id, promotion.content_hash()),
            )
            return manifest
        except Exception as exc:
            if promoted_dataset is not None:
                self.catalog.demote(promoted_dataset)
            if not source_path.exists():
                retrieval_status = (
                    RetrievalStatus.PARTIAL
                    if isinstance(exc, PartialRetrievalError)
                    else RetrievalStatus.FAILED
                )
                self._source_manifest(
                    source_id,
                    request,
                    artifact,
                    0,
                    (),
                    retrieval_status,
                    (str(exc),),
                ).write_immutable(source_path)
            self._write_run(
                run_root / "run.json",
                run_id,
                started,
                "FAILED",
                config_hash,
                snapshot,
                request,
                commit,
                errors=(str(exc),),
            )
            raise

    def reprocess(
        self,
        adapter: SourceAdapter[bytes],
        artifact: DataArtifact,
        request: RetrievalRequest,
        contract: TableContract,
    ) -> DatasetManifest:
        """Reprocess verified existing raw bytes without provider retrieval."""
        if artifact.source is not request.source:
            raise DataQualityError("Raw artifact source does not match the reprocessing request.")
        RawStorage.verify(artifact)
        return self.ingest(
            adapter,
            request,
            contract,
            artifact.path.suffix.lstrip("."),
            artifact.media_type,
            _payload_override=artifact.path.read_bytes(),
            _artifact_override=artifact,
        )

    def _validate(
        self,
        records: tuple[dict[str, object], ...],
        table: pa.Table,
        contract: TableContract,
        request: RetrievalRequest,
    ) -> tuple[Any, ...]:
        findings = list(validate_table(table, contract))
        validators = {
            "macro_observations": validate_macro,
            "french_factor_returns": validate_french_factors,
            "sec_financial_facts": validate_sec_facts,
        }
        validator = validators.get(contract.name)
        if validator is not None:
            findings.extend(validator(list(records)))
        if contract.name == "daily_market":
            findings.extend(
                validate_daily_market(
                    list(records),
                    stale_sessions=self.config.validation.stale_price_sessions,
                    extreme_return_threshold=self.config.validation.extreme_return_threshold,
                )
            )
            if request.date_range:
                findings.extend(
                    validate_market_coverage(
                        list(records),
                        calendar=USEquityCalendar(),
                        start=request.date_range.start,
                        end=request.date_range.end,
                        warning_ratio=self.config.validation.market_coverage_warning_ratio,
                        critical_ratio=self.config.validation.market_coverage_critical_ratio,
                        listing_periods=_listing_periods(request.parameters),
                    )
                )
        return tuple(findings)

    def _source_manifest(
        self,
        source_id: str,
        request: RetrievalRequest,
        artifact: DataArtifact | None,
        rows: int,
        records: tuple[dict[str, object], ...],
        status: RetrievalStatus,
        partial_failures: tuple[str, ...] = (),
    ) -> SourceManifest:
        return SourceManifest(
            schema_version="2.0.0",
            source_manifest_id=source_id,
            source=request.source.value,
            request={
                "dataset": request.dataset,
                "identifiers": list(request.identifiers),
                "parameters": _json_safe(request.parameters),
            },
            retrieval_time=artifact.retrieval_timestamp if artifact else datetime.now(UTC),
            response_status=status,
            response_metadata={"adapter_source": request.source.value},
            raw_artifact_id=f"raw:{artifact.checksum}" if artifact else None,
            raw_artifact_path=_relative(artifact.path, self.root) if artifact else None,
            checksum=artifact.checksum if artifact else None,
            byte_size=artifact.byte_size if artifact else None,
            media_type=artifact.media_type if artifact else None,
            row_count=rows,
            requested_start=_requested_date(request, True),
            requested_end=_requested_date(request, False),
            returned_start=_observed_date(records, minimum=True),
            returned_end=_observed_date(records, minimum=False),
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
        status: Literal["RUNNING", "SUCCESS", "PARTIAL", "FAILED"],
        config_hash: str,
        snapshot: Path,
        request: RetrievalRequest,
        commit: str,
        outputs: tuple[str, ...] = (),
        errors: tuple[str, ...] = (),
    ) -> None:
        RunManifest(
            schema_version="2.0.0",
            run_id=run_id,
            run_type="data_ingestion",
            start_time=started,
            completion_time=None if status == "RUNNING" else datetime.now(UTC),
            status=status,
            code_version=__version__,
            git_commit=commit,
            configuration_hash=config_hash,
            configuration_snapshot_path=_relative(snapshot, self.root),
            environment_version=f"institutional-factor-platform {__version__}",
            requested_sources=(request.source.value,),
            requested_datasets=(request.dataset,),
            output_artifacts=outputs,
            errors=errors,
        ).write_immutable(path)


def _payload_bytes(payload: Any) -> bytes:
    if isinstance(payload, bytes):
        return payload
    if isinstance(payload, pd.DataFrame):
        buffer = io.StringIO()
        payload.to_csv(buffer)
        return buffer.getvalue().encode()
    return json.dumps(payload, sort_keys=True, default=str).encode()


def _require_exact_record_columns(
    records: tuple[dict[str, object], ...], contract: TableContract
) -> None:
    expected = set(contract.schema.names)
    for index, row in enumerate(records):
        if set(row) != expected:
            raise DataQualityError(
                f"Record {index} columns differ from {contract.name}; "
                f"missing={sorted(expected - set(row))}, extra={sorted(set(row) - expected)}"
            )


def _table_hash(table: pa.Table) -> str:
    sink = pa.BufferOutputStream()
    with ipc.new_stream(sink, table.schema) as writer:
        writer.write_table(table)
    return hashlib.sha256(sink.getvalue().to_pybytes()).hexdigest()


def _artifact_seed(
    request: RetrievalRequest,
    contract: TableContract,
    raw_checksum: str,
    config_hash: str,
    table_hash: str,
) -> str:
    value = {
        "dataset": request.dataset,
        "contract": contract.name,
        "schema_version": contract.version,
        "transformation_version": TRANSFORMATION_VERSION,
        "raw_checksum": raw_checksum,
        "configuration_hash": config_hash,
        "table_hash": table_hash,
    }
    return hashlib.sha256(json.dumps(value, sort_keys=True).encode()).hexdigest()


def _schema_fingerprint(schema: pa.Schema) -> str:
    return hashlib.sha256(schema.serialize().to_pybytes()).hexdigest()


def _lineage_document(
    *,
    run_id: str,
    source_id: str,
    raw_id: str,
    validation_id: str,
    parquet_id: str,
    dataset_id: str,
    source_path: str,
    validation_path: str,
    parquet_path: str,
    commit: str,
    config_hash: str,
) -> LineageDocument:
    request_id = f"request:{run_id}"
    response_id = f"response:{run_id}"
    transform_id = f"transformation:{run_id}"
    now = datetime.now(UTC)
    artifacts = (
        request_id,
        response_id,
        source_id,
        raw_id,
        transform_id,
        validation_id,
        parquet_id,
        dataset_id,
    )
    specs = (
        (request_id, response_id, RelationshipType.REQUESTED, source_path),
        (response_id, source_id, RelationshipType.RETRIEVED, source_path),
        (source_id, raw_id, RelationshipType.PERSISTED_RAW, source_path),
        (raw_id, transform_id, RelationshipType.STANDARDIZED, None),
        (transform_id, validation_id, RelationshipType.VALIDATED, validation_path),
        (validation_id, parquet_id, RelationshipType.PUBLISHED_PARQUET, parquet_path),
        (parquet_id, dataset_id, RelationshipType.MANIFESTED, None),
    )
    edges = tuple(
        LineageEdge(
            parent_artifact_id=parent,
            child_artifact_id=child,
            relationship_type=relationship,
            transformation_name="phase1_publication",
            transformation_version=TRANSFORMATION_VERSION,
            run_id=run_id,
            creation_timestamp=now,
            code_commit=commit,
            configuration_hash=config_hash,
            evidence_path=evidence,
        )
        for parent, child, relationship, evidence in specs
    )
    return LineageDocument(schema_version="2.0.0", artifacts=artifacts, edges=edges)


def _json_safe(value: Any) -> Any:
    return json.loads(json.dumps(value, sort_keys=True, default=str))


def _listing_periods(parameters: dict[str, Any]) -> dict[str, tuple[date | None, date | None]]:
    raw = parameters.get("listing_periods", {})
    if not isinstance(raw, dict):
        return {}
    result: dict[str, tuple[date | None, date | None]] = {}
    for key, value in raw.items():
        if isinstance(value, dict):
            start = date.fromisoformat(str(value["start"])) if value.get("start") else None
            end = date.fromisoformat(str(value["end"])) if value.get("end") else None
            result[str(key)] = (start, end)
    return result


def _unit_metadata(records: tuple[dict[str, object], ...]) -> dict[str, str]:
    keys = ("source_unit", "standardized_unit", "unit", "currency")
    return {
        key: ",".join(sorted({str(row[key]) for row in records if row.get(key) is not None}))
        for key in keys
        if any(row.get(key) is not None for row in records)
    }


def _relative(path: Path, root: Path) -> str:
    try:
        return path.resolve().relative_to(root).as_posix()
    except ValueError:
        return str(path.resolve())


def _git_commit(root: Path) -> str:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=root, text=True, stderr=subprocess.DEVNULL
        ).strip()
    except (OSError, subprocess.CalledProcessError):
        return "unavailable"


def _entity_count(records: tuple[dict[str, object], ...]) -> int | None:
    values = {str(row.get("security_id")) for row in records if row.get("security_id")}
    return len(values) if values else None


def _requested_date(request: RetrievalRequest, start: bool) -> str | None:
    if not request.date_range:
        return None
    value = request.date_range.start if start else request.date_range.end
    return value.isoformat()


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
    return result.isoformat()
