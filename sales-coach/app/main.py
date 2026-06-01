import sqlite3
import time

from fastapi import FastAPI
from starlette import status

from sales_coach.app.assessment_router import router as assessment_router
from sales_coach.app.database import DB_PATH, init_db
from sales_coach.app.module_router import router as module_router
from sales_coach.app.reflection_router import router as reflection_router
from sales_coach.app.scenario_router import router as scenario_router
from sales_coach.app.session_router import router as session_router
from sales_coach.app.stats_router import router as stats_router
from shared.exception_handlers import register_exception_handlers
from shared.middleware import RequestIDMiddleware
from shared.rate_limiter import RateLimiterMiddleware

START_TIME = time.time()

app = FastAPI(title="Sales Coach Service", version="1.0.0")

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


app.include_router(module_router)
app.include_router(session_router)
app.include_router(scenario_router)
app.include_router(stats_router)
app.include_router(assessment_router)
app.include_router(reflection_router)
