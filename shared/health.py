"""Shared health check router for service apps."""

import time

from fastapi import APIRouter

from shared.app_settings import settings

router = APIRouter(tags=["health"])
_START_TIME = time.time()


@router.get("/health", summary="健康检查")
def health():
    return {
        "status": "ok",
        "uptime": int(time.time() - _START_TIME),
        "version": settings.version,
    }
