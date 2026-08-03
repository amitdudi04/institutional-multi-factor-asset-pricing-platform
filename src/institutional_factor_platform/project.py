"""Project location discovery without environment-specific absolute paths."""

from pathlib import Path

from institutional_factor_platform.exceptions import ProjectRootError


def find_project_root(start: Path | None = None) -> Path:
    """Find the nearest parent containing the project's ``pyproject.toml``.

    Args:
        start: File or directory from which to begin. Defaults to this module.

    Returns:
        The resolved repository root.

    Raises:
        ProjectRootError: If no matching project marker can be found.
    """
    candidate = (start or Path(__file__)).resolve()
    if candidate.is_file():
        candidate = candidate.parent

    for directory in (candidate, *candidate.parents):
        marker = directory / "pyproject.toml"
        if marker.is_file() and _is_this_project(marker):
            return directory

    raise ProjectRootError(
        f"Could not locate institutional-factor-platform from start path: {candidate}"
    )


def _is_this_project(marker: Path) -> bool:
    """Return whether a TOML marker identifies this project."""
    try:
        content = marker.read_text(encoding="utf-8")
    except OSError:
        return False
    return 'name = "institutional-factor-platform"' in content
