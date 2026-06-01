"""MarketAccess · 准入策略服务 — FastAPI 入口。"""

import time
from fastapi import FastAPI
from shared.request_id_middleware import RequestIDMiddleware
from shared.structured_logging import setup_logging

START_TIME = time.time()

setup_logging("market-access")

app = FastAPI(
    title="MarketAccess · 准入策略服务",
    version="1.0.0",
    description="医保目录查询、准入策略分析、报销信息查询",
)
app.add_middleware(RequestIDMiddleware)


@app.on_event("startup")
def startup():
    from market_access.app.database import init_cache_db

    init_cache_db()


@app.get("/health")
def health():
    return {
        "status": "ok",
        "uptime": int(time.time() - START_TIME),
        "service": "market-access",
    }


from market_access.app.formulary_router import router as formulary_router
from market_access.app.bidding_router import router as bidding_router
from market_access.app.strategy_router import router as strategy_router

app.include_router(formulary_router)
app.include_router(bidding_router)
app.include_router(strategy_router)
