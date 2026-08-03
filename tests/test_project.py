from pathlib import Path

import pytest

from institutional_factor_platform.exceptions import ProjectRootError
from institutional_factor_platform.project import find_project_root


def test_finds_repository_root_from_nested_path() -> None:
    root = find_project_root(Path(__file__))
    assert (root / "pyproject.toml").is_file()
    assert (root / "config" / "base.yaml").is_file()


def test_rejects_directory_without_project_marker(tmp_path: Path) -> None:
    with pytest.raises(ProjectRootError, match="Could not locate"):
        find_project_root(tmp_path)
