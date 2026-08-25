"""Constrained API client; arbitrary URLs and filesystem paths are not accepted."""

import os
from typing import Any

import httpx

from institutional_factor_platform.delivery.config import DeliveryConfig
from institutional_factor_platform.exceptions import EvidenceIntegrityError

ALLOWED_ROOTS = frozenset(
    {
        "health",
        "ready",
        "version",
        "governance",
        "limitations",
        "publications",
        "data",
        "factors",
        "asset-pricing",
        "portfolios",
        "ml",
        "reports",
    }
)
AUTHENTICATED_DISCOVERY_TIMEOUT_SECONDS = 600


class DashboardClient:
    def __init__(self, config: DeliveryConfig) -> None:
        self.config = config
        self.base_url = config.dashboard.api_url.rstrip("/")

    def get(self, path: str) -> Any:
        safe = self._safe_path(path)
        timeout = self.config.api.timeout_seconds
        if safe == "ready" or safe.split("?", 1)[0].endswith("publications"):
            timeout = max(timeout, AUTHENTICATED_DISCOVERY_TIMEOUT_SECONDS)
        with httpx.Client(timeout=timeout) as client:
            response = client.get(f"{self.base_url}/{safe}", headers=self._headers())
            response.raise_for_status()
            return response.json()

    def post_report(self, payload: dict[str, Any]) -> Any:
        with httpx.Client(timeout=self.config.api.timeout_seconds) as client:
            response = client.post(
                f"{self.base_url}/reports", json=payload, headers=self._headers()
            )
            response.raise_for_status()
            return response.json()

    @staticmethod
    def safe_error(exc: Exception) -> str:
        prefix = "Authenticated delivery evidence is unavailable."
        if isinstance(exc, httpx.TimeoutException):
            return f"{prefix} API authentication timed out."
        if isinstance(exc, httpx.ConnectError):
            return f"{prefix} API is unreachable."
        if isinstance(exc, httpx.HTTPStatusError):
            status = exc.response.status_code
            if status in {401, 403}:
                return f"{prefix} API authorization failed ({status})."
            if status == 404:
                return f"{prefix} Publication query was not found (404)."
            if status == 500:
                return f"{prefix} Authenticated catalog is not ready (500)."
            return f"{prefix} API request failed ({status})."
        return f"{prefix} Local delivery error ({type(exc).__name__}); review local logs."

    @staticmethod
    def _safe_path(path: str) -> str:
        if path.startswith(("/", ".")) or ".." in path or ":" in path or "\\" in path:
            raise EvidenceIntegrityError("Unsafe dashboard API path")
        root = path.split("/", 1)[0]
        if root not in ALLOWED_ROOTS:
            raise EvidenceIntegrityError("Unsupported dashboard API path")
        return path

    def _headers(self) -> dict[str, str]:
        token = os.environ.get(self.config.api.token_environment_variable)
        return {"authorization": f"Bearer {token}"} if token else {}
