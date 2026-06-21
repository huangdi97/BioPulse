"""Rate limiter — SQLite-backed sliding window with in-memory fallback."""

import asyncio
import logging
import math
import os
import sqlite3
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
WINDOW_SECONDS = 60

DB_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
DB_PATH = os.path.join(DB_DIR, "ratelimit.db")


def _get_sqlite_conn() -> sqlite3.Connection | None:
    """获取 SQLite 连接，失败返回 None。"""
    try:
        os.makedirs(DB_DIR, exist_ok=True)
        conn = sqlite3.connect(DB_PATH, timeout=5, check_same_thread=False)
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute(
            "CREATE TABLE IF NOT EXISTS ratelimit_counters ("
            "ip TEXT NOT NULL, "
            "window_start INTEGER NOT NULL, "
            "count INTEGER NOT NULL DEFAULT 0, "
            "PRIMARY KEY (ip, window_start)"
            ")"
        )
        conn.commit()
        return conn
    except Exception:
        logger.warning("SQLite rate limiter unavailable, falling back to in-memory")
        return None


class RateLimiterMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, default_rate: int = 100, window: int = 60):
        super().__init__(app)
        self.default_rate = default_rate
        self.window = window
        self._sqlite_conn = _get_sqlite_conn()
        self.buckets: dict[str, tuple[float, float]] = {}
        self._last_cleanup = time.time()
        self._lock = asyncio.Lock()

    def _rate_for_path(self, path: str) -> int:
        if path in AUTH_PATHS:
            return AUTH_RATE
        return self.default_rate

    def _window_start(self, now: float) -> int:
        return math.floor(now / WINDOW_SECONDS) * WINDOW_SECONDS

    def _check_sqlite(self, ip: str, now: float, rate: int) -> bool:
        """检查是否超出限流，返回 True 表示允许通过。"""
        ws = self._window_start(now)
        try:
            with self._sqlite_conn:
                row = self._sqlite_conn.execute(
                    "SELECT count FROM ratelimit_counters WHERE ip = ? AND window_start = ?",
                    (ip, ws),
                ).fetchone()
                current = row[0] if row else 0
                if current >= rate:
                    return False
                if row:
                    self._sqlite_conn.execute(
                        "UPDATE ratelimit_counters SET count = count + 1 WHERE ip = ? AND window_start = ?",
                        (ip, ws),
                    )
                else:
                    self._sqlite_conn.execute(
                        "INSERT INTO ratelimit_counters (ip, window_start, count) VALUES (?, ?, 1)",
                        (ip, ws),
                    )
            return True
        except Exception:
            logger.warning("SQLite rate limiter query failed, falling back to in-memory")
            return None

    def _cleanup_sqlite(self, now: float) -> None:
        """清理过期窗口数据。"""
        try:
            cutoff = self._window_start(now) - WINDOW_SECONDS * 2
            with self._sqlite_conn:
                self._sqlite_conn.execute("DELETE FROM ratelimit_counters WHERE window_start < ?", (cutoff,))
        except Exception:
            pass

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

    async def dispatch(self, request: Request, call_next):
        DISABLE = os.environ.get("RATE_LIMIT_DISABLE")
        if DISABLE == "1":
            return await call_next(request)

        path = request.url.path

        if path in WHITELIST_PATHS or path.startswith("/docs") or path.startswith("/openapi.json"):
            return await call_next(request)

        client_ip = request.client.host if request.client else "127.0.0.1"
        rate = self._rate_for_path(path)
        now = time.time()

        if self._sqlite_conn:
            self._cleanup_sqlite(now)
            allowed = self._check_sqlite(client_ip, now, rate)
            if allowed is False:
                return JSONResponse(
                    status_code=429,
                    content={
                        "code": 429,
                        "message": "Too many requests, please try again later",
                        "request_id": getattr(request.state, "request_id", ""),
                    },
                    headers={"Retry-After": str(self.window)},
                )
            if allowed is True:
                return await call_next(request)

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
