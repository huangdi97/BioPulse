"""Shared health check router for service apps."""

import sqlite3
import time
from urllib.request import Request, urlopen

from fastapi import APIRouter

from shared.app_settings import settings

router = APIRouter(tags=["health"])
_START_TIME = time.time()

_DB_PATHS = [
    "data/cloud.db",
    "data/assistant.db",
    "data/opportunity.db",
    "data/sales_assistant.db",
    "data/sales_coach.db",
    "data/management.db",
    "data/clinical_ops_cache.db",
    "data/patient_engage_cache.db",
    "data/market_access_cache.db",
    "data/pharma_intel_cache.db",
]


def _check_db() -> str:
    for path in _DB_PATHS:
        try:
            conn = sqlite3.connect(path)
            conn.execute("SELECT 1")
            conn.close()
            return "connected"
        except Exception:
            continue
    return "disconnected"


def _check_ai() -> str:
    endpoint = settings.ai_local_endpoint or "http://localhost:11434"
    try:
        req = Request(endpoint, method="GET")
        urlopen(req, timeout=5)
        return "reachable"
    except Exception:
        return "unreachable"


@router.get("/health", summary="健康检查")
def health():
    return {
        "status": "ok",
        "db": _check_db(),
        "ai_api": _check_ai(),
        "uptime": int(time.time() - _START_TIME),
        "version": settings.version,
    }
