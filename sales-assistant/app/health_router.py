"""健康检查路由：服务状态、数据库连接与运行时长。"""

import time

from fastapi import APIRouter

from sales_assistant.app.database import DB_PATH

router = APIRouter(tags=["health"])
_start_time = time.time()


@router.get("/health", summary="健康检查", description="服务健康状态与数据库连接检查", tags=["任务"])
def health():
    db_status = "disconnected"
    try:
        import sqlite3

        conn = sqlite3.connect(DB_PATH)
        conn.execute("SELECT 1")
        conn.close()
        db_status = "connected"
    except Exception:
        db_status = "disconnected"
    return {
        "status": "ok",
        "db": db_status,
        "uptime": int(time.time() - _start_time),
        "version": "0.1.0",
    }
