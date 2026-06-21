"""审计日志中间件 — 自动记录每个 HTTP 请求。"""

import logging
import sqlite3
import time

from fastapi import Request, Response

from cloud.app.database import DB_PATH

EXCLUDED_PATHS = {"/health", "/metrics", "/favicon.ico"}
logger = logging.getLogger("cloud")


async def audit_log_middleware(request: Request, call_next):
    path = request.url.path
    if path in EXCLUDED_PATHS or path.startswith("/assets/") or path.startswith("/uploads/"):
        return await call_next(request)

    start_time = time.time()
    response: Response = await call_next(request)
    duration_ms = round((time.time() - start_time) * 1000, 2)

    try:
        user_id = getattr(request.state, "user_id", None) or getattr(request.state, "user", None)
        if hasattr(user_id, "id"):
            user_id = user_id.id
        if user_id is None:
            user_id = 0
        user_id = int(user_id) if user_id else 0

        detail = f"{request.method} {path} {response.status_code} {duration_ms}ms"
        ip = request.client.host if request.client else ""

        conn = sqlite3.connect(DB_PATH)
        conn.execute(
            "INSERT INTO audit_logs (user_id, action, entity_type, entity_id, detail, source_end, ip_address) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (user_id, request.method, "http_request", None, detail, "cloud-api", ip),
        )
        conn.commit()
        conn.close()
    except Exception:
        logger.exception("审计日志记录失败")

    return response
