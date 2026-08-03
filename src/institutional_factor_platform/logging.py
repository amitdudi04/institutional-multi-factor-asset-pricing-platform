"""Minimal reusable structured logging initialization."""

import json
import logging
import logging.config
from datetime import UTC, datetime
from typing import Any

from institutional_factor_platform.exceptions import ConfigurationError


class JsonFormatter(logging.Formatter):
    """Render stable machine-readable log records without sensitive payloads."""

    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "timestamp": datetime.fromtimestamp(record.created, tz=UTC).isoformat(),
            "severity": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)
        return json.dumps(payload, ensure_ascii=False)


def configure_logging(level: str = "INFO", output_format: str = "json") -> None:
    """Configure process logging using validated level and output format."""
    normalized_level = level.upper()
    if normalized_level not in logging.getLevelNamesMapping():
        raise ConfigurationError(f"Unsupported logging level: {level!r}.")
    if output_format not in {"json", "text"}:
        raise ConfigurationError(f"Unsupported logging format: {output_format!r}.")

    formatter = (
        {"()": "institutional_factor_platform.logging.JsonFormatter"}
        if output_format == "json"
        else {"format": "%(asctime)s %(levelname)s %(name)s %(message)s"}
    )
    logging.config.dictConfig(
        {
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": {"standard": formatter},
            "handlers": {
                "console": {
                    "class": "logging.StreamHandler",
                    "formatter": "standard",
                    "level": normalized_level,
                }
            },
            "root": {"handlers": ["console"], "level": normalized_level},
        }
    )
