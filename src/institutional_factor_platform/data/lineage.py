"""Persisted, deterministic Phase 1 artifact lineage."""

import json
from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum
from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field

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
    schema_version: str = Field(pattern=r"^\d+\.\d+\.\d+$")
    event_id: str
    dataset_id: str
    relationship_type: RelationshipType
    prior_state: str
    new_state: str
    catalog_identity: str
    run_id: str
    event_timestamp: datetime
    code_commit: str
    configuration_hash: str = Field(pattern=r"^[a-f0-9]{64}$")
    reason: str
    supporting_evidence_ids: tuple[str, ...]


class LifecycleEventStore:
    """Append-only immutable publication lifecycle journal."""

    def __init__(self, root: Path) -> None:
        self.root = root

    def persist(self, event: LifecycleEvent) -> Path:
        path = self.root / f"{event.event_id.replace(':', '_')}.json"
        content = json.dumps(event.model_dump(mode="json"), sort_keys=True, indent=2) + "\n"
        if path.exists() and path.read_text(encoding="utf-8") != content:
            raise ManifestError(f"Refusing to overwrite lifecycle event: {path}")
        path.parent.mkdir(parents=True, exist_ok=True)
        if not path.exists():
            path.write_text(content, encoding="utf-8")
        return path

    def load(self) -> tuple[LifecycleEvent, ...]:
        try:
            return tuple(
                LifecycleEvent.model_validate_json(path.read_text(encoding="utf-8"))
                for path in sorted(self.root.glob("*.json"))
            )
        except (OSError, ValueError) as exc:
            raise ManifestError(f"Invalid lifecycle journal {self.root}: {exc}") from exc


class LineageStore:
    def __init__(self, path: Path) -> None:
        self.path = path

    def persist(self, document: LineageDocument) -> None:
        self._validate(document)
        content = json.dumps(document.model_dump(mode="json"), sort_keys=True, indent=2) + "\n"
        if self.path.exists():
            if self.path.read_text(encoding="utf-8") != content:
                raise ManifestError(f"Refusing to overwrite persisted lineage: {self.path}")
            return
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(content, encoding="utf-8")

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
