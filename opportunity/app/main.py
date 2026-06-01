import time
import sqlite3
from fastapi import FastAPI, Request, HTTPException
from starlette import status
from fastapi.responses import JSONResponse
from shared.middleware import RequestIDMiddleware
from shared.rate_limiter import RateLimiterMiddleware
import logging

from opportunity.app.database import init_db, DB_PATH
from opportunity.app.stats_router import router as stats_router
from opportunity.app.opportunity_router import router as opportunity_router
from opportunity.app.contact_router import router as contact_router
from opportunity.app.bidding_router import router as bidding_router
from opportunity.app.research_router import router as research_router
from opportunity.app.scoring_router import router as scoring_router
from opportunity.app.bookmark_router import router as bookmark_router
from opportunity.app.pubpeer_router import router as pubpeer_router
from opportunity.app.trend_router import router as trend_router
from opportunity.app.bidding_agent_router import router as bidding_agent_router, start_bidding_scheduler

START_TIME = time.time()

app = FastAPI(title="Opportunity Service", version="1.0.0")

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
    start_bidding_scheduler()


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


app.include_router(stats_router)
app.include_router(opportunity_router)
app.include_router(contact_router)
app.include_router(bidding_router)
app.include_router(research_router)
app.include_router(scoring_router)
app.include_router(bookmark_router)
app.include_router(pubpeer_router)
app.include_router(trend_router)
app.include_router(bidding_agent_router)
