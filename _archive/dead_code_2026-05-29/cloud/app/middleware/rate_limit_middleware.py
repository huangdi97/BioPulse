import os
import threading
import time
from collections import OrderedDict

from fastapi import Request
from starlette.responses import JSONResponse


class RateLimitMiddleware:
    def __init__(self, app, max_requests=100, window_seconds=60):
        self.app = app
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.storage: OrderedDict[str, dict] = OrderedDict()
        self.lock = threading.Lock()

    def _get_ip(self, request: Request) -> str:
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            return forwarded.split(",")[0].strip()
        if request.client:
            return request.client.host
        return "127.0.0.1"

    def process_request(self, request: Request) -> bool:
        ip = self._get_ip(request)
        now = time.time()

        with self.lock:
            if ip in self.storage:
                entry = self.storage[ip]
                if now - entry["window_start"] > self.window_seconds:
                    entry["count"] = 1
                    entry["window_start"] = now
                else:
                    entry["count"] += 1
            else:
                self.storage[ip] = {"count": 1, "window_start": now}

            entry = self.storage[ip]
            if entry["count"] > self.max_requests:
                return False
            return True

    def _get_rate_limit_headers(self, ip: str) -> dict:
        with self.lock:
            entry = self.storage.get(ip, {"count": 0, "window_start": time.time()})
        remaining = max(0, self.max_requests - entry["count"])
        reset = int(entry["window_start"] + self.window_seconds)
        return {
            "X-RateLimit-Limit": str(self.max_requests),
            "X-RateLimit-Remaining": str(remaining),
            "X-RateLimit-Reset": str(reset),
        }

    async def __call__(self, scope, receive, send):
        if os.environ.get("RATE_LIMIT_DISABLE") == "1":
            await self.app(scope, receive, send)
            return

        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        request = Request(scope, receive)
        ip = self._get_ip(request)
        allowed = self.process_request(request)

        if not allowed:
            headers = self._get_rate_limit_headers(ip)
            retry_after = max(1, int(headers["X-RateLimit-Reset"]) - int(time.time()))
            headers["Retry-After"] = str(retry_after)

            response = JSONResponse(
                status_code=429,
                content={"detail": "Too Many Requests"},
                headers=headers,
            )
            await response(scope, receive, send)
            return

        rate_limit_headers = self._get_rate_limit_headers(ip)

        async def send_wrapper(message):
            if message["type"] == "http.response.start":
                headers = list(message.get("headers", []))
                for key, value in rate_limit_headers.items():
                    headers.append((key.lower().encode(), value.encode()))
                message["headers"] = headers
            await send(message)

        await self.app(scope, receive, send_wrapper)
