import json
import logging
import time
import uuid
from contextvars import ContextVar
from datetime import datetime, timezone

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

request_id_var: ContextVar[str] = ContextVar("request_id", default="")


class JSONFormatter(logging.Formatter):
    """JSON结构化日志格式化器"""

    def format(self, record: logging.LogRecord) -> str:
        log_entry = {
            "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        if hasattr(record, "request_id"):
            log_entry["request_id"] = record.request_id
        elif request_id_var.get():
            log_entry["request_id"] = request_id_var.get()
        if record.exc_info and record.exc_info[0]:
            log_entry["exception"] = self.formatException(record.exc_info)
        return json.dumps(log_entry, ensure_ascii=False)


def setup_json_logging(name: str = "app") -> logging.Logger:
    """配置JSON结构化日志，返回logger实例"""
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)

    handler = logging.StreamHandler()
    handler.setFormatter(JSONFormatter())

    # 避免重复添加handler
    if not logger.handlers:
        logger.addHandler(handler)

    return logger


class RequestIDMiddleware(BaseHTTPMiddleware):
    """为每个请求注入request_id的中间件"""

    async def dispatch(self, request: Request, call_next):
        request_id = request.headers.get("X-Request-ID")
        if not request_id:
            request_id = str(uuid.uuid4())[:8]

        start_time = time.time()

        request.state.request_id = request_id
        request_id_var.set(request_id)

        response: Response = await call_next(request)

        response.headers["X-Request-ID"] = request_id

        process_time = time.time() - start_time
        logger = logging.getLogger("access")
        extra = {"request_id": request_id}
        logger.info(
            f"{request.method} {request.url.path} {response.status_code} {process_time:.3f}s",
            extra=extra,
        )

        return response


# 初始化默认logger
app_logger = setup_json_logging("app")
access_logger = logging.getLogger("access")
access_logger.setLevel(logging.INFO)
if not access_logger.handlers:
    handler = logging.StreamHandler()
    handler.setFormatter(JSONFormatter())
    access_logger.addHandler(handler)
