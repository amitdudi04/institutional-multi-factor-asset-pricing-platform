"""Request authentication, limits, correlation, headers, and throttling."""

import secrets
import time
import uuid
from collections import defaultdict, deque
from collections.abc import Awaitable, Callable
from threading import Lock

from fastapi import Request
from starlette.responses import JSONResponse, Response

from institutional_factor_platform import __version__
from institutional_factor_platform.delivery.config import APIConfig
from institutional_factor_platform.observability.metrics import OperationalMetrics

Handler = Callable[[Request], Awaitable[Response]]


class RequestPolicy:
    def __init__(self, config: APIConfig, metrics: OperationalMetrics) -> None:
        self.config = config
        self.metrics = metrics
        self._requests: dict[str, deque[float]] = defaultdict(deque)
        self._lock = Lock()

    async def __call__(self, request: Request, call_next: Handler) -> Response:
        started = time.monotonic()
        correlation_id = request.headers.get("x-correlation-id") or str(uuid.uuid4())
        if len(correlation_id) > 128 or any(ord(char) < 32 for char in correlation_id):
            return self._error(400, "invalid_request", "Invalid correlation ID", correlation_id)
        limited = self._check_rate(request)
        if limited:
            return self._error(429, "rate_limited", "Request limit exceeded", correlation_id)
        length = request.headers.get("content-length")
        if length is not None and (
            not length.isdigit() or int(length) > self.config.maximum_request_bytes
        ):
            return self._error(
                413, "request_too_large", "Request body exceeds limit", correlation_id
            )
        if request.method in {"POST", "PUT", "PATCH"}:
            if request.headers.get("content-type", "").split(";", 1)[0] != "application/json":
                return self._error(
                    415, "unsupported_media_type", "JSON content is required", correlation_id
                )
            body = await request.body()
            if len(body) > self.config.maximum_request_bytes:
                return self._error(
                    413, "request_too_large", "Request body exceeds limit", correlation_id
                )
        auth_error = self._authorize(request)
        if auth_error:
            return self._error(401, "unauthorized", auth_error, correlation_id)
        try:
            response = await call_next(request)
        except Exception:
            self.metrics.increment("unhandled_errors")
            response = self._error(
                500, "internal_error", "Request could not be completed", correlation_id
            )
        self.metrics.increment("requests")
        if response.status_code >= 400:
            self.metrics.increment("errors")
        response.headers["x-correlation-id"] = correlation_id
        response.headers["x-application-version"] = __version__
        response.headers["x-content-type-options"] = "nosniff"
        response.headers["x-frame-options"] = "DENY"
        response.headers["referrer-policy"] = "no-referrer"
        response.headers["content-security-policy"] = "default-src 'none'; frame-ancestors 'none'"
        response.headers["cache-control"] = "no-store"
        response.headers["x-response-time-ms"] = f"{(time.monotonic() - started) * 1000:.3f}"
        return response

    def _authorize(self, request: Request) -> str | None:
        if request.url.path.endswith("/health"):
            return None
        token = self.config.token()
        protected = self.config.authentication == "required" or (
            self.config.authentication == "optional" and token is not None
        )
        if not protected:
            return None
        if token is None:
            return "Bearer protection is not configured"
        scheme, _, supplied = request.headers.get("authorization", "").partition(" ")
        if (
            scheme.lower() != "bearer"
            or not supplied
            or not secrets.compare_digest(supplied, token)
        ):
            return "Valid bearer authentication is required"
        return None

    def _check_rate(self, request: Request) -> bool:
        client = request.client.host if request.client else "unknown"
        now = time.monotonic()
        with self._lock:
            values = self._requests[client]
            while values and values[0] <= now - 60:
                values.popleft()
            if len(values) >= self.config.requests_per_minute:
                return True
            values.append(now)
        return False

    @staticmethod
    def _error(status: int, code: str, message: str, correlation_id: str) -> JSONResponse:
        return JSONResponse(
            status_code=status,
            content={"error": {"code": code, "message": message}, "correlation_id": correlation_id},
            headers={"x-correlation-id": correlation_id},
        )
