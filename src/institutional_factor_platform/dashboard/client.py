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


class DashboardClient:
    def __init__(self, config: DeliveryConfig) -> None:
        self.config = config
        self.base_url = config.dashboard.api_url.rstrip("/")

    def get(self, path: str) -> Any:
        safe = self._safe_path(path)
        with httpx.Client(timeout=self.config.api.timeout_seconds) as client:
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
