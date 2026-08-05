"""Shared adapter contracts and bounded HTTP retry policy."""

import random
import time
from abc import ABC, abstractmethod
from collections.abc import Callable
from pathlib import Path
from typing import Generic, TypeVar

import httpx

from institutional_factor_platform.data.config import RuntimeSettings
from institutional_factor_platform.data.domain import DataSource, RetrievalRequest, RetrievalResult
from institutional_factor_platform.exceptions import RateLimitError, RetrievalError

T = TypeVar("T")


class SourceAdapter(ABC, Generic[T]):
    source: DataSource

    @abstractmethod
    def retrieve(self, request: RetrievalRequest) -> T:
        """Retrieve provider-native bytes or objects without silent fallback."""

    @abstractmethod
    def standardize(self, payload: T, request: RetrievalRequest) -> tuple[dict[str, object], ...]:
        """Convert a provider payload into its source-specific contract."""

    def mapping_authority_path(self) -> Path | None:
        """Return the persisted identity authority used by this adapter, if any."""
        return None


class HttpTransport:
    def __init__(
        self,
        runtime: RuntimeSettings,
        client: httpx.Client | None = None,
        sleeper: Callable[[float], None] = time.sleep,
    ) -> None:
        self.runtime = runtime
        self.client = client or httpx.Client(timeout=runtime.timeout_seconds, follow_redirects=True)
        self.sleeper = sleeper

    def get(self, url: str, *, headers: dict[str, str] | None = None) -> bytes:
        last_error: Exception | None = None
        for attempt in range(self.runtime.max_retries + 1):
            try:
                response = self.client.get(url, headers=headers)
                if response.status_code == 429:
                    raise RateLimitError(f"Provider rate limit for {url}")
                if 400 <= response.status_code < 500:
                    raise RetrievalError(f"Non-retryable HTTP {response.status_code} for {url}")
                response.raise_for_status()
                return response.content
            except RateLimitError:
                raise
            except RetrievalError:
                raise
            except (httpx.TimeoutException, httpx.NetworkError, httpx.HTTPStatusError) as exc:
                last_error = exc
                if attempt == self.runtime.max_retries:
                    break
                delay = self.runtime.backoff_seconds * (2**attempt)
                delay += random.uniform(0, self.runtime.jitter_seconds)
                self.sleeper(delay)
        raise RetrievalError(f"Retrieval failed after bounded retries for {url}: {last_error}")


def completed_result(result: RetrievalResult) -> RetrievalResult:
    """Identity helper used by services to make result handling explicit."""
    return result
