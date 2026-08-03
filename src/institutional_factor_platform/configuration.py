"""Strict configuration loading for repository-controlled YAML files."""

import os
import re
from collections.abc import Mapping
from pathlib import Path
from typing import Any

import yaml

from institutional_factor_platform.exceptions import ConfigurationError
from institutional_factor_platform.project import find_project_root

_ENVIRONMENT_REFERENCE = re.compile(r"\$\{([A-Z][A-Z0-9_]*)\}")


def load_configuration(path: Path | None = None) -> dict[str, Any]:
    """Load YAML configuration, resolving explicit environment references.

    Missing files, invalid YAML, non-mapping roots, and unresolved environment
    references fail loudly. Values are never invented or silently defaulted.
    """
    config_path = (path or find_project_root() / "config" / "base.yaml").resolve()
    if not config_path.is_file():
        raise ConfigurationError(
            f"Configuration file does not exist: {config_path}. Provide a valid YAML file."
        )

    try:
        raw = config_path.read_text(encoding="utf-8")
        parsed = yaml.safe_load(_expand_environment(raw, config_path))
    except yaml.YAMLError as exc:
        raise ConfigurationError(
            f"Invalid YAML in configuration file {config_path}: {exc}"
        ) from exc
    except OSError as exc:
        raise ConfigurationError(f"Could not read configuration file {config_path}: {exc}") from exc

    if not isinstance(parsed, Mapping):
        raise ConfigurationError(
            f"Configuration root must be a mapping in {config_path}; got {type(parsed).__name__}."
        )

    return dict(parsed)


def _expand_environment(content: str, path: Path) -> str:
    """Resolve allow-listed environment-reference syntax without loading .env files."""
    missing: set[str] = set()

    def replace(match: re.Match[str]) -> str:
        variable = match.group(1)
        value = os.environ.get(variable)
        if value is None:
            missing.add(variable)
            return match.group(0)
        return value

    expanded = _ENVIRONMENT_REFERENCE.sub(replace, content)
    if missing:
        names = ", ".join(sorted(missing))
        raise ConfigurationError(
            f"Configuration {path} references unset environment variable(s): {names}."
        )
    return expanded
