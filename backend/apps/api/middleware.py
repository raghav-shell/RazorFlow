"""HTTP middleware for request tracing, request ID generation, and latency metrics."""

import time
import uuid
from typing import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from packages.common.context import set_request_id


class RequestTracingMiddleware(BaseHTTPMiddleware):
    """
    Extracts or generates X-Request-ID, sets ContextVar, and adds timing headers.
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Extract or generate unique request ID
        request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
        set_request_id(request_id)

        start_time = time.perf_counter()

        response: Response = await call_next(request)

        duration_ms = (time.perf_counter() - start_time) * 1000.0

        # Attach tracing headers to response
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Response-Time-MS"] = f"{duration_ms:.2f}"

        return response


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Injects OWASP recommended security headers on all outgoing HTTP responses.
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        response: Response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
        return response
