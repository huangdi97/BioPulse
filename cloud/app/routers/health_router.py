"""健康检查端点 — /health 和 /ready。"""

import sqlite3
import urllib.request
from datetime import datetime

from fastapi import APIRouter

from cloud.app.database import DATABASE_URL, DB_PATH
from shared.config import settings

router = APIRouter(tags=["health"])

VERSION = "0.1.0"


def _check_db() -> bool:
    """执行 SELECT 1 确认数据库可达。"""
    try:
        if DATABASE_URL.startswith(("postgresql://", "postgres://")):
            import psycopg

            from shared.db import PGCompatConnection

            conn = PGCompatConnection(psycopg.connect(DATABASE_URL))
            conn.execute("SELECT 1")
            conn.close()
        else:
            conn = sqlite3.connect(DB_PATH)
            conn.execute("SELECT 1")
            conn.close()
        return True
    except Exception:
        return False


def _check_llm_api() -> bool:
    """对配置的 AI 端点发 HEAD 请求确认可达。"""
    try:
        req = urllib.request.Request(
            settings.deepseek_api_url,
            method="HEAD",
        )
        urllib.request.urlopen(req, timeout=5)
        return True
    except Exception:
        return False


@router.get("/health")
async def health():
    """基础健康检查。"""
    return {"status": "ok", "timestamp": datetime.now().isoformat(), "version": VERSION}


@router.get("/ready")
async def ready():
    """就绪检查 — 验证依赖服务状态。"""
    db_ok = _check_db()
    llm_ok = _check_llm_api()
    deps = {
        "db": "ok" if db_ok else "unreachable",
        "llm_api": "ok" if llm_ok else "unreachable",
    }
    status = "ok" if db_ok and llm_ok else "degraded"
    return {
        "status": status,
        "timestamp": datetime.now().isoformat(),
        "dependencies": deps,
    }
