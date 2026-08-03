from pathlib import Path

import pytest

from institutional_factor_platform.configuration import load_configuration
from institutional_factor_platform.exceptions import ConfigurationError


def test_loads_repository_base_configuration() -> None:
    config = load_configuration()
    assert config["project"]["environment"] == "research"
    assert config["logging"] == {"level": "INFO", "format": "json"}


def test_missing_configuration_fails_actionably(tmp_path: Path) -> None:
    with pytest.raises(ConfigurationError, match="does not exist"):
        load_configuration(tmp_path / "missing.yaml")


def test_non_mapping_configuration_is_rejected(tmp_path: Path) -> None:
    path = tmp_path / "invalid.yaml"
    path.write_text("- not\n- a\n- mapping\n", encoding="utf-8")
    with pytest.raises(ConfigurationError, match="root must be a mapping"):
        load_configuration(path)


def test_invalid_yaml_is_rejected(tmp_path: Path) -> None:
    path = tmp_path / "invalid.yaml"
    path.write_text("key: [unterminated", encoding="utf-8")
    with pytest.raises(ConfigurationError, match="Invalid YAML"):
        load_configuration(path)


def test_environment_reference_requires_explicit_value(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.delenv("PLATFORM_TEST_TOKEN", raising=False)
    path = tmp_path / "environment.yaml"
    path.write_text("token: ${PLATFORM_TEST_TOKEN}\n", encoding="utf-8")
    with pytest.raises(ConfigurationError, match="PLATFORM_TEST_TOKEN"):
        load_configuration(path)


def test_environment_reference_is_resolved(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("PLATFORM_TEST_VALUE", "safe-placeholder")
    path = tmp_path / "environment.yaml"
    path.write_text("value: ${PLATFORM_TEST_VALUE}\n", encoding="utf-8")
    assert load_configuration(path) == {"value": "safe-placeholder"}
