import time
import uuid

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

from core.logging import get_logger

logger = get_logger(__name__)


class RequestContextMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
        request.state.request_id = request_id
        start = time.perf_counter()
        response = await call_next(request)
        elapsed_ms = round((time.perf_counter() - start) * 1000, 2)
        response.headers["X-Request-ID"] = request_id
        logger.info(
            "request_completed",
            extra={
                "request_id": request_id,
                "extra_fields": {
                    "path": str(request.url.path),
                    "method": request.method,
                    "status_code": response.status_code,
                    "duration_ms": elapsed_ms,
                },
            },
        )
        return response
