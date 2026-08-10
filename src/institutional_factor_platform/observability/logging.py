"""Structured, redacted application logging."""

import json
import logging
import re
from typing import Any

SECRET = re.compile(r"(?i)(bearer\s+)[A-Za-z0-9._~-]+|((?:token|secret|password)[=:]\s*)[^\s,]+")


def redact(value: str) -> str:
    return SECRET.sub(lambda match: (match.group(1) or match.group(2) or "") + "[REDACTED]", value)


def operational_log(logger: logging.Logger, level: int, event: str, **fields: Any) -> None:
    safe = {key: redact(str(value)) for key, value in fields.items()}
    logger.log(level, json.dumps({"event": event, **safe}, sort_keys=True))
