"""Verify optional subordinate artifacts bound by an authenticated diagnostics file."""

import hashlib
from pathlib import Path
from typing import Any

from institutional_factor_platform.exceptions import EvidenceIntegrityError


def authenticate_supplementary(value: dict[str, Any], root: Path) -> None:
    seen: set[Path] = set()
    for item in value.get("bound_supplementary_artifacts", []):
        try:
            path = (root / item["path"]).resolve()
            if not path.is_relative_to(root.resolve()) or path in seen:
                raise ValueError("Unsafe or duplicate path")
            seen.add(path)
            content = path.read_bytes()
            if (
                len(content) != item["bytes"]
                or hashlib.sha256(content).hexdigest() != item["sha256"]
            ):
                raise ValueError("Content differs")
        except (OSError, KeyError, TypeError, ValueError) as exc:
            raise EvidenceIntegrityError("Bound supplementary evidence missing or changed") from exc
