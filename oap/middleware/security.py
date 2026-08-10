"""Security middleware for rate limiting and request correlation."""

from __future__ import annotations

from uuid import uuid4
import logging

from slowapi import Limiter
from slowapi.util import get_remote_address
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

logger = logging.getLogger("oap.security")

# Rate limiter instance
limiter = Limiter(key_func=get_remote_address)


class RequestCorrelationMiddleware(BaseHTTPMiddleware):
    """Add request correlation IDs for tracing and audit."""

    async def dispatch(self, request: Request, call_next) -> Response:
        # Generate or retrieve request ID
        request_id = request.headers.get("X-Request-ID", str(uuid4()))
        request.state.request_id = request_id

        # Call the next middleware/handler
        response = await call_next(request)

        # Add request ID to response headers
        response.headers["X-Request-ID"] = request_id

        # Log request with correlation ID
        client_ip = request.client.host if request.client else "unknown"
        logger.info(
            f"{request.method} {request.url.path}",
            extra={
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
                "status_code": response.status_code,
                "client_ip": client_ip,
            },
        )

        return response
