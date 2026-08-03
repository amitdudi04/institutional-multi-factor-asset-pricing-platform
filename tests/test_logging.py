import json
import logging

import pytest

from institutional_factor_platform.exceptions import ConfigurationError
from institutional_factor_platform.logging import JsonFormatter, configure_logging


def test_json_formatter_emits_required_fields() -> None:
    record = logging.LogRecord("platform.test", logging.INFO, __file__, 1, "ready", (), None)
    payload = json.loads(JsonFormatter().format(record))
    assert payload["severity"] == "INFO"
    assert payload["logger"] == "platform.test"
    assert payload["message"] == "ready"
    assert "timestamp" in payload


def test_configure_logging_sets_root_level() -> None:
    configure_logging("WARNING", "text")
    assert logging.getLogger().level == logging.WARNING


@pytest.mark.parametrize("level", ["NOT_A_LEVEL", ""])
def test_invalid_logging_level_is_rejected(level: str) -> None:
    with pytest.raises(ConfigurationError, match="Unsupported logging level"):
        configure_logging(level)


def test_invalid_logging_format_is_rejected() -> None:
    with pytest.raises(ConfigurationError, match="Unsupported logging format"):
        configure_logging("INFO", "xml")
