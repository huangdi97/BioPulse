import time
import sqlite3
from fastapi import FastAPI, Request, HTTPException
from starlette import status
from fastapi.responses import JSONResponse
from shared.middleware import RequestIDMiddleware
from shared.rate_limiter import RateLimiterMiddleware
import logging

from assistant.app.database import init_db, DB_PATH
from assistant.app.hcp_router import router as hcp_router
from assistant.app.visit_router import router as visit_router
from assistant.app.task_router import router as task_router
from assistant.app.qa_router import router as qa_router
from assistant.app.health_radar_router import router as health_radar_router
from assistant.app.surgery_router import router as surgery_router
from assistant.app.knowledge_router import router as knowledge_router
from assistant.app.knowledge_seed import seed_knowledge
from assistant.app.location_router import router as location_router
from assistant.app.ws_router import router as ws_router
from assistant.app.sync_router import router as sync_router
from assistant.app.voice_router import router as voice_router
from assistant.app.media_router import router as media_router
from assistant.app.reminder_scheduler import start_scheduler

START_TIME = time.time()

app = FastAPI(title="Assistant Service", version="1.0.0")

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
    """Initialize database tables and seed data on application startup."""
    init_db()
    seed_knowledge()
    start_scheduler()


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


app.include_router(hcp_router)
app.include_router(visit_router)
app.include_router(task_router)
app.include_router(qa_router)
app.include_router(health_radar_router)
app.include_router(surgery_router)
app.include_router(knowledge_router)
app.include_router(location_router)
app.include_router(ws_router)
app.include_router(sync_router)
app.include_router(voice_router)
app.include_router(media_router)
