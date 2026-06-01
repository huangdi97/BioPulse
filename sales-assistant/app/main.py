import time
import sqlite3
from fastapi import FastAPI
from starlette import status
from shared.middleware import RequestIDMiddleware
from shared.rate_limiter import RateLimiterMiddleware
from shared.exception_handlers import register_exception_handlers

from sales_assistant.app.database import init_db, DB_PATH
from sales_assistant.app.schedule_router import router as schedule_router
from sales_assistant.app.note_router import router as note_router
from sales_assistant.app.hcp_router import router as hcp_router
from sales_assistant.app.precall_router import router as precall_router
from sales_assistant.app.objection_router import router as objection_router
from sales_assistant.app.funnel_router import router as funnel_router
from sales_assistant.app.content_router import router as content_router
from sales_assistant.app.coach_router import router as coach_router
from sales_assistant.app.anomaly_router import router as anomaly_router
from sales_assistant.app.strategy_router import router as strategy_router

START_TIME = time.time()

app = FastAPI(title="Sales Assistant Service", version="1.0.0")

app.add_middleware(RequestIDMiddleware)
app.add_middleware(RateLimiterMiddleware, default_rate=100, window=60)
register_exception_handlers(app)


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


app.include_router(schedule_router)
app.include_router(note_router)
app.include_router(hcp_router, tags=["hcp", "products"])
app.include_router(precall_router)
app.include_router(objection_router)
app.include_router(funnel_router)
app.include_router(content_router)
app.include_router(coach_router)
app.include_router(anomaly_router)
app.include_router(strategy_router)
