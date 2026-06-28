"""FastAPI 中间件配置。"""

import os

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from cloud.app.middleware.audit_middleware import audit_log_middleware
from cloud.app.middleware.logging_middleware import logging_middleware
from cloud.app.middleware.request_id import RequestIDMiddleware
from shared.exception_handlers import register_exception_handlers
from shared.rate_limiter import RateLimiterMiddleware


def _resolve_cors_origins() -> list[str]:
    env = os.environ.get("ENV", "development").lower()
    cors_env = os.environ.get("CORS_ORIGINS", "")
    if cors_env:
        return [o.strip() for o in cors_env.split(",") if o.strip()]
    if env == "production":
        raise RuntimeError("CORS_ORIGINS must be explicitly set in production. Set CORS_ORIGINS to comma-separated allowed origins.")
    return ["*"]


def register_middleware(app: FastAPI) -> None:
    app.add_middleware(RequestIDMiddleware)

    @app.middleware("http")
    async def api_path_rewrite(request: Request, call_next):
        path = request.scope["path"]
        if path.startswith("/api/cloud/"):
            new_path = "/" + path[len("/api/cloud/") :]
            request.scope["path"] = new_path
            if "raw_path" in request.scope:
                request.scope["raw_path"] = new_path.encode()
        return await call_next(request)

    app.middleware("http")(logging_middleware)
    app.middleware("http")(audit_log_middleware)
    register_exception_handlers(app)

    _cors_origins = _resolve_cors_origins()
    app.add_middleware(
        CORSMiddleware,
        allow_origins=_cors_origins,
        allow_credentials=_cors_origins != ["*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.add_middleware(RateLimiterMiddleware, default_rate=100, window=60)
