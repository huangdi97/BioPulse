import logging
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from starlette import status

logger = logging.getLogger("app")


def register_exception_handlers(app: FastAPI):
    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException):
        code_map = {401: 1, 403: 2, 404: 3, 409: 4, 422: 4, 429: 7}
        error_code = code_map.get(exc.status_code, 5)
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "code": error_code,
                "message": exc.detail,
                "data": None,
                "request_id": getattr(request.state, "request_id", ""),
            },
        )

    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        logger.error(
            "Unhandled exception",
            extra={"request_id": getattr(request.state, "request_id", "")},
            exc_info=True,
        )
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "code": 5,
                "message": "Internal server error",
                "data": None,
                "request_id": getattr(request.state, "request_id", ""),
            },
        )
