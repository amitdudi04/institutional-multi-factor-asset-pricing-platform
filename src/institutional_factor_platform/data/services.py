"""Controlled Phase 1 publication across raw, validation, lineage, manifests, and catalog."""

import hashlib
import io
import json
import os
import socket
import subprocess
import uuid
from collections.abc import Callable
from datetime import UTC, date, datetime
from pathlib import Path
from typing import Any, Literal

import pandas as pd
import pyarrow as pa
import pyarrow.ipc as ipc

from institutional_factor_platform import __version__
from institutional_factor_platform.data.access import RecoveryService, ResearchDatasetRepository
from institutional_factor_platform.data.calendar import USEquityCalendar
from institutional_factor_platform.data.config import Phase1Config
from institutional_factor_platform.data.contracts import TableContract
from institutional_factor_platform.data.domain import (
    DataArtifact,
    DatasetStatus,
    DataSource,
    IssuerId,
    MappingStatus,
    RetrievalRequest,
    RetrievalStatus,
)
from institutional_factor_platform.data.lineage import (
    LifecycleEvent,
    LifecycleEventStore,
    LifecycleState,
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
from institutional_factor_platform.data.security_master import (
    IssuerListingMappingStore,
    SecurityMappingStore,
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
from institutional_factor_platform.exceptions import (
    DataQualityError,
    EvidenceIntegrityError,
    PartialRetrievalError,
)
from institutional_factor_platform.project import find_project_root

TRANSFORMATION_VERSION = "2.0.0"
TEMPORAL_POLICY_VERSION = "2.0.0"
_NO_PAYLOAD = object()


class DataIngestionService:
    def __init__(
        self,
        config: Phase1Config,
        root: Path | None = None,
        failure_hook: Callable[[str], None] | None = None,
    ) -> None:
        self.config = config
        self.root = (root or find_project_root()).resolve()
        self.paths = config.paths.resolved(self.root)
        self.raw = RawStorage(self.paths["raw"])
        self.parquet = ParquetStorage(self.paths["processed"], config.storage.parquet_compression)
        self.quarantine = QuarantineStorage(self.paths["quarantine"])
        self.catalog = DuckDBCatalog(self.paths["duckdb"], self.root)
        self.failure_hook = failure_hook
        self.recovery = RecoveryService(self.catalog, self.root, self.paths["manifests"])
        self.research = ResearchDatasetRepository(self.catalog, self.root)
        if self.catalog.path.exists():
            self.recovery.reconcile_startup()
        self.recovery.reconcile_locks(self.paths["metadata"] / "publication-locks")

    def _boundary(self, name: str) -> None:
        if self.failure_hook is not None:
            self.failure_hook(name)

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
        snapshot_checksum = sha256_file(snapshot)
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
        lock_path = (
            self.paths["metadata"]
            / "publication-locks"
            / (
                hashlib.sha256(f"{request.source.value}|{request.dataset}".encode()).hexdigest()
                + ".lock"
            )
        )
        _acquire_publication_lock(lock_path, run_id, request.dataset)
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
            unit_metadata = _reconcile_units(records, request, contract)
            mapping = _authenticate_mapping_authority(
                adapter, records, request, contract, self.root
            )
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
            source_checksum = sha256_file(source_path)
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
            self._boundary("artifact_publication")
            parquet_id = f"parquet:{published.checksum}"
            raw_id = f"raw:{artifact.checksum}"
            registered_id = f"catalog:{dataset_id}"
            promotion_id = f"promotion:{run_id}:{dataset_id}"
            final_lineage_path = run_root / "lineage.json"
            final_lineage_id = f"lineage:{run_id}:published"
            final_lineage = _lineage_document(
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
                lineage_id=final_lineage_id,
                registration_id=registered_id,
                promotion_id=promotion_id,
            )
            LineageStore(final_lineage_path).persist(final_lineage)
            journal = LifecycleEventStore(run_root / "lifecycle")
            manifest_revision_id = f"manifest:{run_id}:{dataset_id}:published"
            snapshot_id = f"config:{config_hash}"
            lifecycle_context = {
                "dataset_id": dataset_id,
                "artifact_id": parquet_id,
                "run_id": run_id,
                "registration_id": registered_id,
                "manifest_revision_id": manifest_revision_id,
                "validation_report_id": validation_id,
                "lineage_document_id": final_lineage_id,
                "configuration_snapshot_id": snapshot_id,
                "catalog_identity": _relative(self.catalog.path, self.root),
                "code_commit": commit,
                "configuration_hash": config_hash,
            }
            previous: LifecycleEvent | None = None
            for state in (
                LifecycleState.CREATED,
                LifecycleState.RAW_VERIFIED,
                LifecycleState.STANDARDIZED,
                LifecycleState.VALIDATED,
                LifecycleState.ARTIFACT_PUBLISHED,
            ):
                previous = _append_lifecycle(journal, lifecycle_context, state, previous)
            if previous is None:
                raise EvidenceIntegrityError("Lifecycle initialization failed.")
            manifest = DatasetManifest(
                schema_version="5.0.0",
                manifest_revision_id=f"manifest:{run_id}:{dataset_id}:registered",
                run_id=run_id,
                dataset_id=dataset_id,
                dataset_type=contract.name,
                schema_name=contract.name,
                schema_fingerprint=_schema_fingerprint(contract.schema),
                parent_artifacts=(raw_id,),
                source_manifest_id=source_id,
                source_manifest_path=_relative(source_path, self.root),
                source_manifest_checksum=source_checksum,
                transformation_name=f"{request.source.value}_standardize",
                transformation_version=TRANSFORMATION_VERSION,
                row_count=table.num_rows,
                column_count=table.num_columns,
                primary_key=contract.primary_key,
                date_start=report.observed_start,
                date_end=report.observed_end,
                security_count=report.entity_count,
                missingness_summary={name: table[name].null_count for name in table.column_names},
                unit_metadata=unit_metadata,
                mapping_status=mapping[0],
                mapping_evidence_path=mapping[1],
                mapping_evidence_checksum=mapping[2],
                mapping_evidence_id=mapping[3],
                validation_report_id=validation_id,
                validation_report_path=_relative(validation_json, self.root),
                validation_report_checksum=sha256_file(validation_json),
                validation_status=status,
                lineage_path=_relative(final_lineage_path, self.root),
                lineage_id=final_lineage_id,
                lineage_checksum=sha256_file(final_lineage_path),
                lineage_complete=True,
                quarantine_status=False,
                parquet_path=_relative(published.path, self.root),
                output_artifact_id=parquet_id,
                output_checksum=published.checksum,
                output_byte_size=published.byte_size,
                catalog_registration_state="REGISTERED",
                promotion_state="ELIGIBLE",
                catalog_registration_id=registered_id,
                creation_time=datetime.now(UTC),
                configuration_hash=config_hash,
                configuration_snapshot_path=_relative(snapshot, self.root),
                configuration_snapshot_checksum=snapshot_checksum,
                configuration_snapshot_id=snapshot_id,
                lifecycle_journal_path=_relative(journal.root, self.root),
                lifecycle_head_event_id=previous.event_id,
                code_version=__version__,
                git_commit=commit,
                temporal_policy_version=TEMPORAL_POLICY_VERSION,
            )
            registered_path = run_root / "dataset-registered.json"
            manifest.write_immutable(registered_path)
            self.catalog.register_persisted(dataset_id, registered_path, self.root)
            self._boundary("catalog_registration")
            previous = _append_lifecycle(
                journal, lifecycle_context, LifecycleState.REGISTERED, previous
            )
            previous = _append_lifecycle(
                journal, lifecycle_context, LifecycleState.PROMOTION_PENDING, previous
            )
            promoted_at = datetime.now(UTC)
            final_manifest = manifest.model_copy(
                update={
                    "manifest_revision_id": manifest_revision_id,
                    "promotion_state": "PUBLISHED",
                    "promotion_event_id": promotion_id,
                    "promotion_timestamp": promoted_at,
                    "lifecycle_head_event_id": previous.event_id,
                }
            )
            dataset_path = run_root / "dataset.json"
            final_manifest.write_immutable(dataset_path)
            self._boundary("final_manifest_persistence")
            self.catalog.stage_promotion(dataset_id, dataset_path, self.root)
            promoted_dataset = dataset_id
            self._boundary("catalog_promotion")
            previous = _append_lifecycle(
                journal, lifecycle_context, LifecycleState.PROMOTED, previous
            )
            self._boundary("promotion_event_persistence")
            final_event_id = _lifecycle_event_id(
                run_id, previous.sequence + 1, LifecycleState.FINALIZED
            )
            promotion = PromotionManifest(
                schema_version="4.0.0",
                promotion_manifest_id=promotion_id,
                run_id=run_id,
                dataset_id=dataset_id,
                dataset_manifest_path=_relative(dataset_path, self.root),
                dataset_manifest_hash=final_manifest.content_hash(),
                output_checksum=published.checksum,
                lineage_path=_relative(final_lineage_path, self.root),
                validation_status=status,
                promoted_at=promoted_at,
                git_commit=commit,
                configuration_hash=config_hash,
                lifecycle_final_event_id=final_event_id,
                run_manifest_path=_relative(run_root / "run.json", self.root),
            )
            promotion_path = run_root / "promotion.json"
            promotion.write_immutable(promotion_path)
            self._boundary("promotion_manifest_persistence")
            self._boundary("run_completion")
            previous = _append_lifecycle(
                journal,
                lifecycle_context,
                LifecycleState.FINALIZED,
                previous,
                additional_supporting_evidence=(
                    f"promotion-envelope:{promotion.content_hash()}",
                    f"run-terminal:{run_id}",
                ),
            )
            if previous.event_id != final_event_id:
                raise EvidenceIntegrityError("Final lifecycle event identity is inconsistent.")
            self._boundary("journal_finalization")
            self.catalog.promote_persisted(dataset_id, dataset_path, self.root)
            self._boundary("catalog_activation")
            self._write_run(
                run_root / "run.json",
                run_id,
                started,
                "SUCCESS",
                config_hash,
                snapshot,
                request,
                commit,
                (dataset_id, promotion.promotion_manifest_id),
            )
            return final_manifest
        except Exception as exc:
            if promoted_dataset is not None:
                self.catalog.demote(promoted_dataset, record_lifecycle=False)
                events = journal.load()
                if events:
                    last = events[-1]
                    pending_state = (
                        LifecycleState.DEMOTION_PENDING
                        if last.new_state is LifecycleState.FINALIZED
                        else LifecycleState.RECOVERY_REQUIRED
                    )
                    last = _append_lifecycle(
                        journal, lifecycle_context, pending_state, last, reason=str(exc)
                    )
                    _append_lifecycle(
                        journal,
                        lifecycle_context,
                        LifecycleState.DEMOTED,
                        last,
                        reason=str(exc),
                    )
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
            if not (run_root / "run.json").exists():
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
        finally:
            lock_path.unlink(missing_ok=True)

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


def _acquire_publication_lock(path: Path, run_id: str, dataset: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        descriptor = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    except FileExistsError as exc:
        raise EvidenceIntegrityError(
            "Publication lock exists. Verify process ownership and lifecycle evidence; "
            f"automatic stale-lock deletion is prohibited: {path.name}"
        ) from exc
    with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
        json.dump(
            {
                "lock_id": f"publication:{run_id}",
                "process_id": os.getpid(),
                "host": socket.gethostname(),
                "acquired_at": datetime.now(UTC).isoformat(),
                "operation": "phase1_publication",
                "dataset_id": dataset,
            },
            handle,
            sort_keys=True,
        )
        handle.flush()
        os.fsync(handle.fileno())


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
    lineage_id: str,
    registration_id: str | None = None,
    promotion_id: str | None = None,
) -> LineageDocument:
    request_id = f"request:{run_id}"
    response_id = f"response:{run_id}"
    transform_id = f"transformation:{run_id}"
    now = datetime.now(UTC)
    artifacts = (
        (
            request_id,
            response_id,
            source_id,
            raw_id,
            transform_id,
            validation_id,
            parquet_id,
            dataset_id,
        )
        + ((registration_id,) if registration_id else ())
        + ((promotion_id,) if promotion_id else ())
    )
    specs = (
        (
            (request_id, response_id, RelationshipType.REQUESTED, source_path),
            (response_id, source_id, RelationshipType.RETRIEVED, source_path),
            (source_id, raw_id, RelationshipType.PERSISTED_RAW, source_path),
            (raw_id, transform_id, RelationshipType.STANDARDIZED, None),
            (transform_id, validation_id, RelationshipType.VALIDATED, validation_path),
            (validation_id, parquet_id, RelationshipType.PUBLISHED_PARQUET, parquet_path),
            (parquet_id, dataset_id, RelationshipType.MANIFESTED, None),
        )
        + (
            ((dataset_id, registration_id, RelationshipType.REGISTERED_IN_CATALOG, None),)
            if registration_id
            else ()
        )
        + (
            ((registration_id, promotion_id, RelationshipType.PROMOTED_TO_RESEARCH_READY, None),)
            if registration_id and promotion_id
            else ()
        )
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
    return LineageDocument(
        schema_version="4.0.0",
        lineage_id=lineage_id,
        dataset_id=dataset_id,
        run_id=run_id,
        artifacts=artifacts,
        edges=edges,
    )


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


def _authenticate_mapping_authority(
    adapter: SourceAdapter[Any],
    records: tuple[dict[str, object], ...],
    request: RetrievalRequest,
    contract: TableContract,
    project_root: Path,
) -> tuple[
    Literal["NOT_APPLICABLE", "RESOLVED", "AUTHORITY_DATASET"],
    str | None,
    str | None,
    str | None,
]:
    """Verify canonical IDs centrally and return content-bound mapping evidence."""
    if contract.name == "security_master":
        return ("AUTHORITY_DATASET", None, None, None)
    identified = tuple(row for row in records if row.get("security_id") is not None)
    if not identified:
        return ("NOT_APPLICABLE", None, None, None)
    if len(identified) != len(records):
        raise DataQualityError("A dataset cannot mix mapped and unmapped security identities.")
    authority = adapter.mapping_authority_path()
    if authority is None:
        raise DataQualityError("Canonical security IDs require persisted mapping authority.")
    authority = authority.resolve()
    try:
        relative = authority.relative_to(project_root.resolve()).as_posix()
    except ValueError as exc:
        raise DataQualityError("Mapping authority must be inside the project data root.") from exc
    if not authority.is_file():
        raise DataQualityError("Persisted mapping authority is missing.")
    try:
        if request.source in {DataSource.YAHOO_FINANCE, DataSource.HF_DATA_LIBRARY}:
            security_store = SecurityMappingStore(authority)
            for row in identified:
                observed = str(row["security_id"])
                expected = security_store.resolve(
                    request.source.value,
                    str(row["ticker"]),
                    row["trading_date"],  # type: ignore[arg-type]
                ).value
                if observed != expected:
                    raise DataQualityError("Market record identity differs from mapping authority.")
        elif request.source is DataSource.SEC_EDGAR:
            issuer_store = IssuerListingMappingStore(authority)
            for row in identified:
                observed = str(row["security_id"])
                expected = issuer_store.resolve(
                    IssuerId(str(row["issuer_id"])),
                    row["filing_date"],  # type: ignore[arg-type]
                ).value
                if observed != expected:
                    raise DataQualityError("SEC record identity differs from mapping authority.")
        elif request.source is DataSource.OWNER_SUPPLIED and contract.name in {
            "factor_market_input",
            "factor_fundamental_input",
        }:
            mappings = SecurityMappingStore(authority).load()
            for row in identified:
                as_of = row.get("date") or row.get("period_end")
                if not isinstance(as_of, date):
                    raise DataQualityError("Owner Phase 2 mapping date is missing or invalid.")
                matches = {
                    item.security_id.value
                    for item in mappings
                    if item.security_id is not None
                    and item.status is MappingStatus.RESOLVED
                    and item.valid_from <= as_of
                    and (item.valid_to is None or as_of <= item.valid_to)
                }
                if str(row["security_id"]) not in matches:
                    raise DataQualityError(
                        "Owner Phase 2 record identity differs from mapping authority."
                    )
        else:
            raise DataQualityError(
                f"Security identity authority is not defined for source {request.source.value}."
            )
    except DataQualityError:
        raise
    except Exception as exc:
        raise DataQualityError(f"Mapping authority validation failed: {exc}") from exc
    checksum = sha256_file(authority)
    return ("RESOLVED", relative, checksum, f"mapping:{checksum}")


def _unit_metadata(records: tuple[dict[str, object], ...]) -> dict[str, str]:
    keys = ("source_unit", "standardized_unit", "unit", "currency")
    return {
        key: ",".join(sorted({str(row[key]) for row in records if row.get(key) is not None}))
        for key in keys
        if any(row.get(key) is not None for row in records)
    }


def _reconcile_units(
    records: tuple[dict[str, object], ...],
    request: RetrievalRequest,
    contract: TableContract,
) -> dict[str, str]:
    """Bind request, row, source, contract, output, and transformation unit evidence."""
    declared_raw = request.parameters.get("units", {})
    declared = (
        {str(key): str(value).strip() for key, value in declared_raw.items()}
        if isinstance(declared_raw, dict)
        else {}
    )
    observed = _unit_metadata(records)
    metadata = {f"request.{key}": value for key, value in sorted(declared.items())}
    metadata.update({f"row.{key}": value for key, value in sorted(observed.items())})
    metadata.update(observed)

    if contract.name == "macro_observations":
        row_units = {
            str(row.get("source_unit", "")).strip().lower().replace(" ", "_") for row in records
        }
        if "" in row_units or len(row_units) != 1:
            raise DataQualityError("Macro series requires one explicit homogeneous source unit.")
        row_unit = next(iter(row_units))
        declared_unit = declared.get("value", "").lower().replace(" ", "_")
        if declared and declared_unit != row_unit:
            raise DataQualityError(
                f"Owner request unit {declared.get('value')!r} contradicts row unit {row_unit!r}."
            )
        if request.source is DataSource.FRED and request.dataset in {"DGS3MO", "TB3MS"}:
            if row_unit != "percent_per_annum":
                raise DataQualityError("Approved Treasury series must remain percent_per_annum.")
        metadata.update(
            {
                "contract.value": row_unit,
                "standardized.value": row_unit,
                "transformation.value": "identity@1.0.0",
            }
        )
    elif contract.name == "french_factor_returns":
        source_units = {str(row.get("source_unit", "")).strip() for row in records}
        output_units = {str(row.get("standardized_unit", "")).strip() for row in records}
        if source_units != {"percent"} or output_units != {"decimal_return"}:
            raise DataQualityError("French factors require percent to decimal_return evidence.")
        if declared and declared.get("factor_value") not in {"decimal", "decimal_return"}:
            raise DataQualityError("Owner factor output unit must be decimal_return.")
        metadata.update(
            {
                "contract.factor_value": "decimal_return",
                "standardized.factor_value": "decimal_return",
                "transformation.factor_value": "percent_to_decimal@1.0.0",
            }
        )
    elif contract.name == "daily_market":
        currencies = {str(row.get("currency", "")).strip() for row in records}
        if currencies != {"USD"}:
            raise DataQualityError(
                "Daily-market currency requires USD or an explicit FX transform."
            )
        if declared:
            for field in ("open", "high", "low", "close", "adjusted_close", "dividend"):
                if declared.get(field) not in {"USD", "currency:USD"}:
                    raise DataQualityError(f"Owner price unit is incompatible for {field}.")
            if declared.get("volume") != "shares" or declared.get("split_factor") != "ratio":
                raise DataQualityError("Owner volume/split units are incompatible.")
        metadata.update(
            {
                "contract.price": "USD",
                "contract.volume": "shares",
                "standardized.price": "USD",
                "standardized.volume": "shares",
                "transformation.market": "identity@1.0.0",
            }
        )
    elif contract.name == "sec_financial_facts":
        row_units = {str(row.get("unit", "")).strip() for row in records}
        if "" in row_units:
            raise DataQualityError("SEC XBRL units must be preserved explicitly.")
        if declared and declared.get("value") != "xbrl_source_unit":
            raise DataQualityError("SEC owner metadata must declare xbrl_source_unit.")
        metadata.update(
            {
                "contract.value": "xbrl_source_unit",
                "standardized.value": "xbrl_source_unit",
                "transformation.value": "identity@1.0.0",
            }
        )
    elif declared:
        metadata.update({f"contract.{key}": value for key, value in sorted(declared.items())})
        metadata["transformation"] = "identity@1.0.0"
    return metadata


def _lifecycle_event_id(run_id: str, sequence: int, state: LifecycleState) -> str:
    return f"lifecycle:{run_id}:{sequence:04d}:{state.value.lower()}"


def _append_lifecycle(
    store: LifecycleEventStore,
    context: dict[str, str],
    state: LifecycleState,
    previous: LifecycleEvent | None,
    *,
    reason: str = "controlled Phase 1 publication",
    additional_supporting_evidence: tuple[str, ...] = (),
) -> LifecycleEvent:
    sequence = 1 if previous is None else previous.sequence + 1
    event = LifecycleEvent.create(
        sequence=sequence,
        event_id=_lifecycle_event_id(context["run_id"], sequence, state),
        event_type=state.value,
        prior_event_id=previous.event_id if previous else None,
        prior_state=previous.new_state if previous else None,
        new_state=state,
        event_timestamp=datetime.now(UTC),
        reason=reason,
        supporting_evidence_ids=(
            context["artifact_id"],
            context["validation_report_id"],
            context["lineage_document_id"],
            *additional_supporting_evidence,
        ),
        **context,
    )
    store.persist(event)
    return event


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
        try:
            return subprocess.check_output(
                ["git", "rev-parse", "HEAD"], text=True, stderr=subprocess.DEVNULL
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
