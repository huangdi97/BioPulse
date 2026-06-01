import time
import sqlite3
from fastapi import FastAPI, Request, HTTPException
from starlette import status
from fastapi.responses import JSONResponse
from shared.middleware import RequestIDMiddleware
from shared.rate_limiter import RateLimiterMiddleware
import logging

from sales_coach.app.database import init_db, DB_PATH
from sales_coach.app.module_router import router as module_router
from sales_coach.app.scenario_router import router as scenario_router
from sales_coach.app.session_router import router as session_router
from sales_coach.app.stats_router import router as stats_router
from sales_coach.app.assessment_router import router as assessment_router
from sales_coach.app.reflection_router import router as reflection_router

START_TIME = time.time()

app = FastAPI(title="Sales Coach Service", version="1.0.0")

app.add_middleware(RequestIDMiddleware)
app.add_middleware(RateLimiterMiddleware, default_rate=100, window=60)

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    code_map = {401: 1, 403: 2, 404: 3, 409: 4, 422: 4, 429: 7}
    error_code = code_map.get(exc.status_code, 5)
    return JSONResponse(
        status_code=exc.status_code,
        content={'code': error_code, 'message': exc.detail, 'data': None}
    )


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={'code': 5, 'message': 'Internal server error', 'data': None}
    )


@app.on_event("startup")
def on_startup() -> None:
    """Initialize database tables on application startup."""
    init_db()


@app.get("/health", status_code=status.HTTP_200_OK)
def health_check() -> dict:
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.execute("SELECT 1")
        conn.close()
        db_status = "connected"
    except Exception:
        db_status = "disconnected"
    return {
        "status": "ok",
        "db": db_status,
        "uptime": int(time.time() - START_TIME),
        "version": "0.1.0",
    }


app.include_router(module_router)
app.include_router(session_router)
app.include_router(scenario_router)
app.include_router(stats_router)
app.include_router(assessment_router)
app.include_router(reflection_router)
