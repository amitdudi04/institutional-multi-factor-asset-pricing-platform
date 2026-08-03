"""Atomic, canonical persistence helpers for authoritative Phase 1 evidence."""

import json
import os
import tempfile
from pathlib import Path
from typing import Any

from institutional_factor_platform.exceptions import ManifestError


def canonical_json_bytes(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), default=str).encode()


def pretty_json_bytes(value: Any) -> bytes:
    return (json.dumps(value, sort_keys=True, indent=2, default=str) + "\n").encode()


def atomic_write_bytes(path: Path, content: bytes, *, immutable: bool = True) -> None:
    """Durably publish bytes through a same-directory temporary and atomic replace."""
    if path.exists():
        if immutable and path.read_bytes() != content:
            raise ManifestError(f"Refusing to overwrite immutable evidence: {path}")
        if immutable:
            return
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(dir=path.parent, prefix=f".{path.name}-")
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
        _fsync_directory(path.parent)
    finally:
        temporary.unlink(missing_ok=True)


def atomic_write_json(path: Path, value: Any, *, immutable: bool = True) -> None:
    content = pretty_json_bytes(value)
    json.loads(content)
    atomic_write_bytes(path, content, immutable=immutable)


def resolve_project_path(value: str, project_root: Path) -> Path:
    root = project_root.resolve()
    candidate = Path(value)
    resolved = candidate.resolve() if candidate.is_absolute() else (root / candidate).resolve()
    if root not in (resolved, *resolved.parents):
        raise ManifestError(f"Evidence path escapes project root: {value}")
    return resolved


def _fsync_directory(path: Path) -> None:
    try:
        descriptor = os.open(path, os.O_RDONLY)
    except OSError:
        return
    try:
        os.fsync(descriptor)
    except OSError:
        pass
    finally:
        os.close(descriptor)
