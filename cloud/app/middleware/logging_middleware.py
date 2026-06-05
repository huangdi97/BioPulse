import json
import logging
import time
import uuid
from contextvars import ContextVar
from datetime import datetime, timezone

from fastapi import Request, Response

request_id_var: ContextVar[str] = ContextVar("request_id", default="")


class JSONFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        log_entry = {
            "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
            "level": record.levelname,
            "logger": record.name,
            "service": getattr(record, "service", "cloud"),
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        rid = getattr(record, "request_id", None) or request_id_var.get()
        if rid:
            log_entry["request_id"] = rid
        if hasattr(record, "user_id") and record.user_id:
            log_entry["user_id"] = record.user_id
        if record.exc_info and record.exc_info[0]:
            log_entry["exception"] = self.formatException(record.exc_info)
        return json.dumps(log_entry, ensure_ascii=False)


async def logging_middleware(request: Request, call_next):
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


def get_logger(name: str, request_id: str = "") -> logging.LoggerAdapter:
    logger = logging.getLogger(name)
    extra = {"request_id": request_id} if request_id else {}
    return logging.LoggerAdapter(logger, extra)
