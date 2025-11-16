"""FastAPI middleware for read-only mode enforcement.

Enforces read-only mode when CLI holds write lock, allowing observability
while preventing conflicting write operations.
"""

from typing import Callable

import structlog
from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

logger = structlog.get_logger(__name__)


class ReadOnlyMiddleware(BaseHTTPMiddleware):
    """Middleware to enforce read-only mode when CLI holds lock.

    Allows GET/HEAD/OPTIONS (observability) but rejects write operations
    (POST/PATCH/PUT/DELETE) with 423 Locked status when another interface
    holds write lock.
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request and enforce read-only mode if needed.

        Args:
            request: HTTP request
            call_next: Next middleware/endpoint

        Returns:
            HTTP response
        """
        # GET/HEAD/OPTIONS: always allowed (observability)
        if request.method in ["GET", "HEAD", "OPTIONS"]:
            return await call_next(request)

        # Write operations (POST/PATCH/PUT/DELETE): check lock
        session_lock = getattr(request.app.state, "session_lock", None)

        if session_lock is None:
            logger.warning("session_lock_not_initialized", path=request.url.path)
            # Allow request if lock not initialized (graceful degradation)
            return await call_next(request)

        # Check if another process holds write lock
        if session_lock.is_write_locked_by_other():
            lock_state = session_lock.get_lock_state()
            holder = lock_state.get("holder", "unknown")

            logger.warning(
                "write_operation_rejected",
                method=request.method,
                path=request.url.path,
                lock_holder=holder,
            )

            return JSONResponse(
                status_code=423,  # Locked
                content={
                    "error": f"Session locked by {holder.upper()}",
                    "mode": "read-only",
                    "message": f"Exit {holder.upper()} session to enable write operations",
                },
            )

        # Lock available or we hold it - allow write operation
        return await call_next(request)
