import logging
import uuid

from fastapi import Request

from shared.json_formatter import JSONFormatter, StructuredLogging, request_id_var  # noqa: F401


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
