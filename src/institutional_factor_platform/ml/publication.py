"""Immutable checksum-bound Phase 5 research publication and trusted model loading."""

import hashlib
import json
import os
import tempfile
from datetime import UTC, datetime
from pathlib import Path
from typing import Literal, cast

import pyarrow as pa
import pyarrow.parquet as pq
from pydantic import Field

from institutional_factor_platform.data.evidence import (
    atomic_write_json,
    canonical_json_bytes,
    resolve_project_path,
)
from institutional_factor_platform.exceptions import (
    EvidenceIntegrityError,
    PublicationConflictError,
)
from institutional_factor_platform.ml.contracts import FrozenModel
from institutional_factor_platform.ml.models import ResearchModel


class MLArtifact(FrozenModel):
    name: str
    path: str
    checksum: str = Field(pattern=r"^[a-f0-9]{64}$")
    byte_size: int = Field(gt=0)
    media_type: Literal[
        "application/json", "application/vnd.apache.parquet", "application/x-joblib"
    ]
    columns: tuple[str, ...] = ()


class MLManifest(FrozenModel):
    schema_version: Literal["1.0.0"]
    publication_id: str
    created_at: datetime
    phase2_publication_id: str
    phase2_manifest_hash: str = Field(pattern=r"^[a-f0-9]{64}$")
    phase3_publication_id: str
    phase3_manifest_hash: str = Field(pattern=r"^[a-f0-9]{64}$")
    phase4_publication_id: str | None = None
    phase4_manifest_hash: str | None = Field(default=None, pattern=r"^[a-f0-9]{64}$")
    configuration_hash: str = Field(pattern=r"^[a-f0-9]{64}$")
    git_commit: str
    model_id: str
    feature_schema_hash: str = Field(pattern=r"^[a-f0-9]{64}$")
    target_hash: str = Field(pattern=r"^[a-f0-9]{64}$")
    preprocessor_hash: str = Field(pattern=r"^[a-f0-9]{64}$")
    random_seed: int
    dependency_versions: dict[str, str]
    artifacts: tuple[MLArtifact, ...]
    validation_status: Literal["PASS", "PASS_WITH_WARNINGS"]


class MLPublication(FrozenModel):
    schema_version: Literal["1.0.0"]
    publication_id: str
    manifest_path: str
    manifest_hash: str = Field(pattern=r"^[a-f0-9]{64}$")
    configuration_hash: str = Field(pattern=r"^[a-f0-9]{64}$")
    git_commit: str


REQUIRED_ARTIFACTS = frozenset(
    {
        "feature_matrix",
        "targets",
        "splits",
        "preprocessor",
        "model",
        "hyperparameter_trials",
        "predictions",
        "evaluation",
        "calibration",
        "explanations",
        "drift",
        "comparison",
        "economic_evaluation",
        "model_card",
        "configuration",
        "lineage",
        "validation",
    }
)


class MLRepository:
    def __init__(self, root: Path, manifest_root: Path) -> None:
        self.root = root.resolve()
        self.manifest_root = manifest_root.resolve()

    def authenticate(self, publication_id: str) -> MLManifest:
        pointer = self.manifest_root / publication_id / "ml-publication.json"
        try:
            publication = MLPublication.model_validate_json(pointer.read_text("utf-8"))
            manifest = MLManifest.model_validate_json(
                resolve_project_path(publication.manifest_path, self.root).read_text("utf-8")
            )
        except (OSError, ValueError) as exc:
            raise EvidenceIntegrityError(f"Invalid ML publication evidence: {exc}") from exc
        if (
            publication.publication_id != publication_id
            or publication.publication_id != manifest.publication_id
            or publication.manifest_hash != manifest.content_hash()
            or publication.configuration_hash != manifest.configuration_hash
            or publication.git_commit != manifest.git_commit
        ):
            raise EvidenceIntegrityError("ML publication does not bind its manifest")
        names = set()
        for artifact in manifest.artifacts:
            if artifact.name in names:
                raise EvidenceIntegrityError("Duplicate ML artifact name")
            names.add(artifact.name)
            content = resolve_project_path(artifact.path, self.root).read_bytes()
            if (
                len(content) != artifact.byte_size
                or hashlib.sha256(content).hexdigest() != artifact.checksum
            ):
                raise EvidenceIntegrityError(f"ML artifact changed: {artifact.name}")
            if artifact.media_type == "application/vnd.apache.parquet":
                schema = pq.read_schema(pa.BufferReader(content))
                if tuple(schema.names) != artifact.columns:
                    raise EvidenceIntegrityError(f"ML artifact schema changed: {artifact.name}")
            elif artifact.media_type == "application/json":
                try:
                    value = json.loads(content)
                except (UnicodeDecodeError, json.JSONDecodeError) as exc:
                    raise EvidenceIntegrityError(f"Invalid ML JSON: {artifact.name}") from exc
                if isinstance(value, dict) and value.get("publication_id") not in {
                    None,
                    publication_id,
                }:
                    raise EvidenceIntegrityError(f"ML JSON identity differs: {artifact.name}")
        if names != REQUIRED_ARTIFACTS:
            raise EvidenceIntegrityError("ML artifact inventory is incomplete or unexpected")
        return manifest

    def list_authenticated(self) -> tuple[str, ...]:
        result = []
        for path in sorted(self.manifest_root.glob("*/ml-publication.json")):
            try:
                result.append(self.authenticate(path.parent.name).publication_id)
            except (EvidenceIntegrityError, OSError):
                continue
        return tuple(result)

    def load_model(self, publication_id: str) -> ResearchModel:
        manifest = self.authenticate(publication_id)
        artifact = next(x for x in manifest.artifacts if x.name == "model")
        content = resolve_project_path(artifact.path, self.root).read_bytes()
        model = ResearchModel.load_trusted(content, artifact.checksum)
        if (
            model.model_id != manifest.model_id
            or model.preprocessor_hash != manifest.preprocessor_hash
            or model.target_hash != manifest.target_hash
        ):
            raise EvidenceIntegrityError("Model identity differs from manifest")
        return model


def write_artifact(path: Path, content: bytes) -> tuple[str, int]:
    path.parent.mkdir(parents=True, exist_ok=True)
    handle, name = tempfile.mkstemp(dir=path.parent, prefix=f".{path.name}-", suffix=".tmp")
    os.close(handle)
    temporary = Path(name)
    try:
        temporary.write_bytes(content)
        checksum = hashlib.sha256(content).hexdigest()
        if path.exists():
            if hashlib.sha256(path.read_bytes()).hexdigest() != checksum:
                raise PublicationConflictError(f"ML artifact identity collision: {path}")
        else:
            os.replace(temporary, path)
        return checksum, path.stat().st_size
    finally:
        temporary.unlink(missing_ok=True)


def publication_identity(values: dict[str, object]) -> str:
    return "ml-" + hashlib.sha256(canonical_json_bytes(values)).hexdigest()[:32]


def publish_bundle(
    root: Path,
    output_root: Path,
    manifest_root: Path,
    manifest_values: dict[str, object],
    contents: dict[str, tuple[bytes, str, tuple[str, ...]]],
) -> MLManifest:
    if set(contents) != REQUIRED_ARTIFACTS:
        raise EvidenceIntegrityError("Cannot publish an incomplete ML artifact bundle")
    project = root.resolve()
    publication_id = publication_identity(manifest_values)
    destination = (project / output_root / publication_id).resolve()
    authority = (project / manifest_root / publication_id).resolve()
    for path in (destination, authority):
        try:
            path.relative_to(project)
        except ValueError as exc:
            raise EvidenceIntegrityError("ML publication path escapes project root") from exc
    existing_pointer = authority / "ml-publication.json"
    if existing_pointer.is_file():
        existing = MLRepository(project, project / manifest_root).authenticate(publication_id)
        existing_by_name = {item.name: item for item in existing.artifacts}
        for name, (content, _, _) in contents.items():
            if existing_by_name[name].checksum != hashlib.sha256(content).hexdigest():
                raise PublicationConflictError(
                    f"ML publication identity collision for supplied artifact: {name}"
                )
        return existing
    artifacts: list[MLArtifact] = []
    suffixes = {
        "application/json": ".json",
        "application/vnd.apache.parquet": ".parquet",
        "application/x-joblib": ".joblib",
    }
    for name in sorted(contents):
        content, media_type, columns = contents[name]
        suffix = suffixes.get(media_type)
        if suffix is None:
            raise EvidenceIntegrityError("Unsupported ML artifact media type")
        path = destination / f"{name}{suffix}"
        checksum, size = write_artifact(path, content)
        media = cast(
            Literal["application/json", "application/vnd.apache.parquet", "application/x-joblib"],
            media_type,
        )
        artifacts.append(
            MLArtifact(
                name=name,
                path=path.relative_to(project).as_posix(),
                checksum=checksum,
                byte_size=size,
                media_type=media,
                columns=columns,
            )
        )
    manifest = MLManifest.model_validate(
        {
            "schema_version": "1.0.0",
            "publication_id": publication_id,
            "created_at": datetime.now(UTC),
            "artifacts": tuple(artifacts),
            **manifest_values,
        }
    )
    manifest_path = authority / "ml-manifest.json"
    atomic_write_json(manifest_path, manifest.model_dump(mode="json"))
    pointer = MLPublication(
        schema_version="1.0.0",
        publication_id=publication_id,
        manifest_path=manifest_path.relative_to(project).as_posix(),
        manifest_hash=manifest.content_hash(),
        configuration_hash=manifest.configuration_hash,
        git_commit=manifest.git_commit,
    )
    atomic_write_json(authority / "ml-publication.json", pointer.model_dump(mode="json"))
    return MLRepository(project, project / manifest_root).authenticate(publication_id)
