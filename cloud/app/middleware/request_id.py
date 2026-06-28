"""ASGI middleware: inject X-Request-ID from header or generate UUID, propagate to logging context."""

import uuid

from cloud.app.middleware.json_formatter import request_id_var


class RequestIDMiddleware:
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        headers = dict(scope.get("headers", []))
        req_id = headers.get(b"x-request-id", b"").decode()
        if not req_id:
            req_id = str(uuid.uuid4())
        scope["request_id"] = req_id
        token = request_id_var.set(req_id)
        try:
            await self.app(scope, receive, send)
        finally:
            request_id_var.reset(token)
