import time

from fastapi import APIRouter

from sales_coach.app.database import DB_PATH

router = APIRouter(tags=["health"])
_start_time = time.time()


@router.get("/health")
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
