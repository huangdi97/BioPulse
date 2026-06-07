"""FastAPI 日志中间件：JSON 格式化、请求 ID 注入、访问日志记录。"""

import json
import logging
import time
import uuid

from fastapi import Request, Response

from cloud.app.middleware.json_formatter import JSONFormatter, request_id_var  # noqa: F401


async def logging_middleware(request: Request, call_next):
    request_id = request.headers.get("X-Request-ID")
    if not request_id:
        request_id = str(uuid.uuid4())[:8]

    start_time = time.time()

    request.state.request_id = request_id
    request_id_var.set(request_id)

    response: Response = await call_next(request)

    response.headers["X-Request-ID"] = request_id

    process_time_ms = round((time.time() - start_time) * 1000, 2)
    user_id = getattr(request.state, "user_id", None) or getattr(request.state, "user", None)
    if hasattr(user_id, "id"):
        user_id = user_id.id

    logger = logging.getLogger("access")
    extra = {"request_id": request_id}
    if user_id:
        extra["user_id"] = str(user_id)

    log_entry = {
        "method": request.method,
        "path": request.url.path,
        "status_code": response.status_code,
        "process_time_ms": process_time_ms,
    }
    if user_id:
        log_entry["user_id"] = str(user_id)

    logger.info(json.dumps(log_entry, ensure_ascii=False), extra=extra)
    return response


def get_logger(name: str, request_id: str = "") -> logging.LoggerAdapter:
    logger = logging.getLogger(name)
    extra = {"request_id": request_id} if request_id else {}
    return logging.LoggerAdapter(logger, extra)
