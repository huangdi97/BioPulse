import json
import logging
import uuid
from datetime import datetime
from typing import Optional

from fastapi import Request


class JSONFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        log_entry = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "service": getattr(record, "service", "unknown"),
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        if hasattr(record, "request_id") and record.request_id:
            log_entry["request_id"] = record.request_id
        if hasattr(record, "user_id") and record.user_id:
            log_entry["user_id"] = record.user_id
        if record.exc_info and record.exc_info[0]:
            log_entry["exception"] = self.formatException(record.exc_info)
        return json.dumps(log_entry, ensure_ascii=False)


def setup_logging(service_name: str = "cloud") -> logging.Logger:
    logger = logging.getLogger(service_name)
    logger.setLevel(logging.INFO)
    handler = logging.StreamHandler()
    handler.setFormatter(JSONFormatter())
    if not logger.handlers:
        logger.addHandler(handler)
    return logger


def get_request_logger(request: Request, service: str = "cloud") -> logging.LoggerAdapter:
    logger = logging.getLogger(service)
    request_id = getattr(request.state, "request_id", None)
    if not request_id:
        request_id = str(uuid.uuid4())[:8]
    user_id = getattr(request.state, "user_id", None) or "anonymous"
    extra = {
        "request_id": request_id,
        "user_id": user_id,
    }
    return logging.LoggerAdapter(logger, extra)
