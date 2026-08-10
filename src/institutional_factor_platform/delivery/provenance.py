"""Identifier, path-confinement, and evidence formatting controls."""

import hashlib
import json
import re
from pathlib import Path
from typing import Any

from institutional_factor_platform.exceptions import EvidenceIntegrityError

ID_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{2,127}$")


def validate_identifier(value: str) -> str:
    if not ID_PATTERN.fullmatch(value):
        raise EvidenceIntegrityError("Invalid publication identifier")
    return value


def confined_path(root: Path, filename: str) -> Path:
    if not ID_PATTERN.fullmatch(Path(filename).stem) or Path(filename).name != filename:
        raise EvidenceIntegrityError("Unsafe confined filename")
    destination = (root.resolve() / filename).resolve()
    try:
        destination.relative_to(root.resolve())
    except ValueError as exc:
        raise EvidenceIntegrityError("Path escapes configured delivery root") from exc
    return destination


def canonical_bytes(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), default=str).encode()


def checksum(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()
