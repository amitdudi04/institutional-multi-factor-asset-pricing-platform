"""Persisted, deterministic Phase 1 artifact lineage."""

import hashlib
from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator

from institutional_factor_platform.data.evidence import atomic_write_json, canonical_json_bytes
from institutional_factor_platform.exceptions import ManifestError


@dataclass(slots=True)
class LineageGraph:
    """Compatibility helper for constructing and querying an acyclic graph in memory."""

    parents: dict[str, set[str]] = field(default_factory=dict)

    def add(self, artifact_id: str, parent_ids: tuple[str, ...] = ()) -> None:
        if artifact_id in parent_ids:
            raise ManifestError("An artifact cannot be its own parent.")
        self.parents.setdefault(artifact_id, set()).update(parent_ids)
        if _graph_has_cycle(self.parents):
            self.parents[artifact_id].difference_update(parent_ids)
            raise ManifestError("Lineage relationship would create a cycle.")

    def ancestors(self, artifact_id: str) -> tuple[str, ...]:
        found: set[str] = set()
        stack = list(self.parents.get(artifact_id, set()))
        while stack:
            item = stack.pop()
            if item not in found:
                found.add(item)
                stack.extend(self.parents.get(item, set()))
        return tuple(sorted(found))


class RelationshipType(StrEnum):
    REQUESTED = "REQUESTED"
    RETRIEVED = "RETRIEVED"
    PERSISTED_RAW = "PERSISTED_RAW"
    STANDARDIZED = "STANDARDIZED"
    VALIDATED = "VALIDATED"
    PUBLISHED_PARQUET = "PUBLISHED_PARQUET"
    MANIFESTED = "MANIFESTED"
    REGISTERED_IN_CATALOG = "REGISTERED_IN_CATALOG"
    PROMOTED_TO_RESEARCH_READY = "PROMOTED_TO_RESEARCH_READY"
    DEMOTED_FROM_RESEARCH_READY = "DEMOTED_FROM_RESEARCH_READY"
    INVALIDATED = "INVALIDATED"
    SUPERSEDED = "SUPERSEDED"


class LifecycleState(StrEnum):
    CREATED = "CREATED"
    RAW_VERIFIED = "RAW_VERIFIED"
    STANDARDIZED = "STANDARDIZED"
    VALIDATED = "VALIDATED"
    ARTIFACT_PUBLISHED = "ARTIFACT_PUBLISHED"
    REGISTERED = "REGISTERED"
    PROMOTION_PENDING = "PROMOTION_PENDING"
    PROMOTED = "PROMOTED"
    FINALIZED = "FINALIZED"
    DEMOTION_PENDING = "DEMOTION_PENDING"
    DEMOTED = "DEMOTED"
    INVALIDATED = "INVALIDATED"
    SUPERSEDED = "SUPERSEDED"
    RECOVERY_REQUIRED = "RECOVERY_REQUIRED"


ALLOWED_TRANSITIONS: frozenset[tuple[LifecycleState, LifecycleState]] = frozenset(
    {
        (LifecycleState.CREATED, LifecycleState.RAW_VERIFIED),
        (LifecycleState.RAW_VERIFIED, LifecycleState.STANDARDIZED),
        (LifecycleState.STANDARDIZED, LifecycleState.VALIDATED),
        (LifecycleState.VALIDATED, LifecycleState.ARTIFACT_PUBLISHED),
        (LifecycleState.ARTIFACT_PUBLISHED, LifecycleState.REGISTERED),
        (LifecycleState.REGISTERED, LifecycleState.PROMOTION_PENDING),
        (LifecycleState.PROMOTION_PENDING, LifecycleState.PROMOTED),
        (LifecycleState.PROMOTION_PENDING, LifecycleState.RECOVERY_REQUIRED),
        (LifecycleState.ARTIFACT_PUBLISHED, LifecycleState.RECOVERY_REQUIRED),
        (LifecycleState.REGISTERED, LifecycleState.RECOVERY_REQUIRED),
        (LifecycleState.PROMOTED, LifecycleState.FINALIZED),
        (LifecycleState.FINALIZED, LifecycleState.DEMOTION_PENDING),
        (LifecycleState.DEMOTION_PENDING, LifecycleState.DEMOTED),
        (LifecycleState.FINALIZED, LifecycleState.INVALIDATED),
        (LifecycleState.FINALIZED, LifecycleState.SUPERSEDED),
        (LifecycleState.PROMOTED, LifecycleState.RECOVERY_REQUIRED),
        (LifecycleState.RECOVERY_REQUIRED, LifecycleState.DEMOTED),
    }
)


class LineageEdge(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    parent_artifact_id: str
    child_artifact_id: str
    relationship_type: RelationshipType
    transformation_name: str
    transformation_version: str = Field(pattern=r"^\d+\.\d+\.\d+$")
    run_id: str
    creation_timestamp: datetime
    code_commit: str
    configuration_hash: str = Field(pattern=r"^[a-f0-9]{64}$")
    evidence_path: str | None = None


class LineageDocument(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    schema_version: str = Field(pattern=r"^\d+\.\d+\.\d+$")
    lineage_id: str = "lineage:legacy"
    dataset_id: str = "legacy"
    run_id: str = "legacy"
    artifacts: tuple[str, ...]
    edges: tuple[LineageEdge, ...]

    @classmethod
    def v3(
        cls,
        *,
        lineage_id: str,
        dataset_id: str,
        run_id: str,
        artifacts: tuple[str, ...],
        edges: tuple[LineageEdge, ...],
    ) -> "LineageDocument":
        return cls(
            schema_version="3.0.0",
            lineage_id=lineage_id,
            dataset_id=dataset_id,
            run_id=run_id,
            artifacts=artifacts,
            edges=edges,
        )


class LifecycleEvent(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    schema_version: str = Field(pattern=r"^4\.0\.0$")
    sequence: int = Field(ge=1)
    event_id: str
    dataset_id: str
    event_type: str
    artifact_id: str
    run_id: str
    prior_event_id: str | None
    prior_state: LifecycleState | None
    new_state: LifecycleState
    registration_id: str
    manifest_revision_id: str
    validation_report_id: str
    lineage_document_id: str
    configuration_snapshot_id: str
    catalog_identity: str
    event_timestamp: datetime
    code_commit: str
    configuration_hash: str = Field(pattern=r"^[a-f0-9]{64}$")
    reason: str
    supporting_evidence_ids: tuple[str, ...]
    actor: str = "phase1_data_service"
    event_checksum: str = Field(pattern=r"^[a-f0-9]{64}$")

    @classmethod
    def create(cls, **values: object) -> "LifecycleEvent":
        values.pop("schema_version", None)
        values.pop("event_checksum", None)
        construction_values: dict[str, Any] = dict(values)
        construction_values.update(schema_version="4.0.0", event_checksum="0" * 64)
        prototype = cls.model_construct(**construction_values)
        payload = prototype.model_dump(mode="json", exclude={"event_checksum"})
        payload["event_checksum"] = _event_checksum(payload)
        return cls.model_validate(payload)

    @model_validator(mode="after")
    def checksum_is_authentic(self) -> "LifecycleEvent":
        if self.event_checksum != _event_checksum(self.model_dump(mode="json")):
            raise ValueError("lifecycle event checksum mismatch")
        return self


class LifecycleEventStore:
    """Append-only immutable publication lifecycle journal."""

    def __init__(self, root: Path) -> None:
        self.root = root

    def persist(self, event: LifecycleEvent) -> Path:
        path = self.root / f"{event.sequence:04d}_{event.event_id.replace(':', '_')}.json"
        if path.exists():
            try:
                persisted = LifecycleEvent.model_validate_json(path.read_text(encoding="utf-8"))
            except (OSError, ValueError) as exc:
                raise ManifestError(f"Invalid lifecycle journal {self.root}: {exc}") from exc
            if persisted != event:
                raise ManifestError(f"Refusing to overwrite lifecycle event: {path}")
            return path
        existing = self.load()
        _validate_lifecycle((*existing, event))
        atomic_write_json(path, event.model_dump(mode="json"))
        return path

    def load(self) -> tuple[LifecycleEvent, ...]:
        try:
            events = tuple(
                LifecycleEvent.model_validate_json(path.read_text(encoding="utf-8"))
                for path in sorted(self.root.glob("*.json"))
            )
            _validate_lifecycle(events)
            return events
        except (OSError, ValueError) as exc:
            raise ManifestError(f"Invalid lifecycle journal {self.root}: {exc}") from exc

    def current_state(self, dataset_id: str) -> LifecycleState | None:
        events = self.load()
        if not events:
            return None
        if any(event.dataset_id != dataset_id for event in events):
            raise ManifestError("Lifecycle journal mixes dataset identities.")
        return events[-1].new_state


class LineageStore:
    def __init__(self, path: Path) -> None:
        self.path = path

    def persist(self, document: LineageDocument) -> None:
        self._validate(document)
        atomic_write_json(self.path, document.model_dump(mode="json"))

    def load(self) -> LineageDocument:
        try:
            return LineageDocument.model_validate_json(self.path.read_text(encoding="utf-8"))
        except (OSError, ValueError) as exc:
            raise ManifestError(f"Invalid persisted lineage {self.path}: {exc}") from exc

    def verify_complete(self, required_artifacts: tuple[str, ...]) -> None:
        document = self.load()
        self._validate(document)
        missing = set(required_artifacts) - set(document.artifacts)
        if missing:
            raise ManifestError(f"Lineage is missing required artifacts: {sorted(missing)}")

    @staticmethod
    def _validate(document: LineageDocument) -> None:
        artifacts = set(document.artifacts)
        if len(artifacts) != len(document.artifacts):
            raise ManifestError("Lineage artifact IDs must be unique.")
        pairs: set[tuple[str, str, RelationshipType]] = set()
        graph: dict[str, set[str]] = {}
        for edge in document.edges:
            if edge.parent_artifact_id == edge.child_artifact_id:
                raise ManifestError("An artifact cannot be its own parent.")
            if edge.parent_artifact_id not in artifacts or edge.child_artifact_id not in artifacts:
                raise ManifestError("Lineage edge references an unknown artifact.")
            key = (edge.parent_artifact_id, edge.child_artifact_id, edge.relationship_type)
            if key in pairs:
                raise ManifestError("Duplicate lineage edge.")
            pairs.add(key)
            graph.setdefault(edge.child_artifact_id, set()).add(edge.parent_artifact_id)
        for artifact in artifacts:
            _assert_acyclic(artifact, graph, set(), set())


def _assert_acyclic(
    artifact: str,
    graph: dict[str, set[str]],
    visiting: set[str],
    visited: set[str],
) -> None:
    if artifact in visiting:
        raise ManifestError("Lineage relationship contains a cycle.")
    if artifact in visited:
        return
    visiting.add(artifact)
    for parent in graph.get(artifact, set()):
        _assert_acyclic(parent, graph, visiting, visited)
    visiting.remove(artifact)
    visited.add(artifact)


def _graph_has_cycle(graph: dict[str, set[str]]) -> bool:
    try:
        visited: set[str] = set()
        for artifact in graph:
            _assert_acyclic(artifact, graph, set(), visited)
    except ManifestError:
        return True
    return False


def _event_checksum(value: dict[str, object]) -> str:
    payload = {key: item for key, item in value.items() if key != "event_checksum"}
    return hashlib.sha256(canonical_json_bytes(payload)).hexdigest()


def _validate_lifecycle(events: tuple[LifecycleEvent, ...]) -> None:
    if not events:
        return
    invariant_fields = (
        "dataset_id",
        "artifact_id",
        "run_id",
        "registration_id",
        "manifest_revision_id",
        "validation_report_id",
        "lineage_document_id",
        "configuration_snapshot_id",
        "catalog_identity",
        "code_commit",
        "configuration_hash",
    )
    first = events[0]
    if first.sequence != 1 or first.prior_event_id is not None or first.prior_state is not None:
        raise ManifestError("Lifecycle must begin at sequence 1 without a predecessor.")
    if first.new_state is not LifecycleState.CREATED:
        raise ManifestError("Lifecycle must begin in CREATED state.")
    seen = {first.event_id}
    previous = first
    for event in events[1:]:
        if event.event_id in seen:
            raise ManifestError("Duplicate lifecycle event ID.")
        if event.sequence != previous.sequence + 1:
            raise ManifestError("Lifecycle sequence is not contiguous.")
        if event.prior_event_id != previous.event_id or event.prior_state is not previous.new_state:
            raise ManifestError("Lifecycle predecessor is missing or inconsistent.")
        if (event.prior_state, event.new_state) not in ALLOWED_TRANSITIONS:
            raise ManifestError(
                f"Invalid lifecycle transition {event.prior_state} -> {event.new_state}."
            )
        for field_name in invariant_fields:
            if getattr(event, field_name) != getattr(first, field_name):
                raise ManifestError(f"Lifecycle mixes {field_name} identities.")
        if event.event_timestamp < previous.event_timestamp:
            raise ManifestError("Lifecycle timestamps are out of order.")
        seen.add(event.event_id)
        previous = event
