"""健康检查路由模块，提供服务状态和数据库连接检查接口。"""

import time

from fastapi import APIRouter
from sales_coach.app.database import DB_PATH

router = APIRouter(tags=["health"])
_start_time = time.time()


@router.get("/health", summary="健康检查", description="检查服务运行状态和数据库连接", tags=["场景"])
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
