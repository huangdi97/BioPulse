import asyncio
import logging
import time

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

logger = logging.getLogger("rate_limiter")
if not logger.handlers:
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter("%(message)s"))
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)

WHITELIST_PATHS = {"/health", "/docs", "/openapi.json"}
AUTH_PATHS = {"/auth/login", "/auth/register"}
AUTH_RATE = 20
CLEANUP_INTERVAL = 300


class RateLimiterMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, default_rate: int = 100, window: int = 60):
        super().__init__(app)
        self.default_rate = default_rate
        self.window = window
        self.buckets: dict[str, tuple[float, float]] = {}
        self._last_cleanup = time.time()
        self._lock = asyncio.Lock()

    def _rate_for_path(self, path: str) -> int:
        if path in AUTH_PATHS:
            return AUTH_RATE
        return self.default_rate

    def _refill(self, ip: str, now: float, rate: int) -> float:
        entry = self.buckets.get(ip)
        if entry is None:
            return float(rate - 1)
        tokens, last = entry
        elapsed = now - last
        refill_amount = elapsed * (rate / self.window)
        tokens = min(float(rate), tokens + refill_amount)
        return tokens - 1

    def _cleanup_stale(self, now: float) -> None:
        if now - self._last_cleanup < CLEANUP_INTERVAL:
            return
        self._last_cleanup = now
        stale_ips = []
        for ip, (tokens, last) in self.buckets.items():
            if now - last > self.window * 2:
                stale_ips.append(ip)
        for ip in stale_ips:
            del self.buckets[ip]
        if stale_ips:
            logger.info(f"Rate limiter cleanup: removed {len(stale_ips)} stale entries")

    async def dispatch(self, request: Request, call_next):
        path = request.url.path

        if path in WHITELIST_PATHS or path.startswith("/docs") or path.startswith("/openapi.json"):
            return await call_next(request)

        client_ip = request.client.host if request.client else "127.0.0.1"
        rate = self._rate_for_path(path)
        now = time.time()

        async with self._lock:
            self._cleanup_stale(now)
            new_tokens = self._refill(client_ip, now, rate)
            self.buckets[client_ip] = (new_tokens, now)

            if new_tokens < 0:
                return JSONResponse(
                    status_code=429,
                    content={
                        "code": 429,
                        "message": "Too many requests, please try again later",
                        "request_id": getattr(request.state, "request_id", ""),
                    },
                    headers={"Retry-After": str(self.window)},
                )

        return await call_next(request)
