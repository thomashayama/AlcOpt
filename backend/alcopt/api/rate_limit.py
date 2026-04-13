"""Simple in-process rate limiting middleware.

Uses a sliding-window counter per client IP. Good enough for a single-process
deployment; swap for Redis-backed limits if you scale to multiple workers.
"""

import time
from collections import defaultdict

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse


class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, requests_per_minute: int = 60):
        super().__init__(app)
        self.rpm = requests_per_minute
        self.window = 60.0
        self._hits: dict[str, list[float]] = defaultdict(list)

    async def dispatch(self, request: Request, call_next):
        client_ip = request.client.host if request.client else "unknown"
        now = time.monotonic()
        cutoff = now - self.window

        # Prune old entries
        hits = self._hits[client_ip]
        self._hits[client_ip] = hits = [t for t in hits if t > cutoff]

        if len(hits) >= self.rpm:
            return JSONResponse(
                {"detail": "Rate limit exceeded. Try again later."},
                status_code=429,
            )

        hits.append(now)
        return await call_next(request)
