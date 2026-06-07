"""应用入口，注册路由和中间件。"""

import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from opportunity.app.bidding_agent_router import (
    router as bidding_agent_router,
)
from opportunity.app.bidding_agent_router import (
    start_bidding_scheduler,
)
from opportunity.app.bidding_router import router as bidding_router
from opportunity.app.bookmark_router import router as bookmark_router
from opportunity.app.contact_router import router as contact_router
from opportunity.app.database import init_db
from opportunity.app.health_router import router as health_router
from opportunity.app.opportunity_router import router as opportunity_router
from opportunity.app.pubpeer_router import router as pubpeer_router
from opportunity.app.research_router import router as research_router
from opportunity.app.scoring_router import router as scoring_router
from opportunity.app.stats_router import router as stats_router
from opportunity.app.trend_router import router as trend_router
from shared.app_settings import settings
from shared.exception_handlers import register_exception_handlers
from shared.l1_cache import cache_rules, init_l1_cache, load_l1_rules
from shared.middleware import RequestIDMiddleware
from shared.rate_limiter import RateLimiterMiddleware
from shared.structured_logging import setup_logging

_BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def _init_l1_cache(category: str) -> None:
    l1_db_path = os.path.join(_BASE_DIR, "data", "l1_cache.db")
    conn = init_l1_cache(l1_db_path)
    rules = load_l1_rules(category)
    cache_rules(conn, rules, category)
    conn.close()


setup_logging("opportunity")

app = FastAPI(title="Opportunity Service", version=settings.version)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(RequestIDMiddleware)
app.add_middleware(RateLimiterMiddleware, default_rate=100, window=60)
register_exception_handlers(app)


@app.on_event("startup")
def on_startup() -> None:
    """Initialize database tables and L1 rule cache on startup."""
    init_db()
    _init_l1_cache("pharma")
    _init_l1_cache("research")
    start_bidding_scheduler()


app.include_router(health_router)
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
