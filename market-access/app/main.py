"""MarketAccess · 准入策略服务 — FastAPI 入口。"""

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware

from shared.app_settings import settings as app_settings
from shared.auth import get_current_user
from shared.exception_handlers import register_exception_handlers
from shared.health import router as health_router
from shared.middleware import RequestIDMiddleware
from shared.structured_logging import setup_logging

from .database import init_cache_db
from .formulary_router import router as formulary_router
from .market_access_bidding_router import router as bidding_router
from .market_access_strategy_router import router as strategy_router
from .routers.price_alert_router import router as price_alert_router
from .routers.price_monitor_router import router as price_monitor_router

setup_logging("market-access")

app = FastAPI(
    title="MarketAccess · 准入策略服务",
    version="1.0.0",
    description="医保目录查询、准入策略分析、报销信息查询",
    openapi_tags=[
        {"name": "招标", "description": "招标信息监控、价格分析"},
        {"name": "价格", "description": "价格趋势、省市数据分析"},
        {"name": "集采", "description": "集采策略分析、医保目录查询"},
    ],
)
_cors_origins = app_settings.cors_origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
    allow_credentials=_cors_origins != ["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(RequestIDMiddleware)
register_exception_handlers(app)


@app.on_event("startup")
def startup():
    init_cache_db()


app.include_router(health_router)


app.include_router(formulary_router, dependencies=[Depends(get_current_user)])
app.include_router(bidding_router, dependencies=[Depends(get_current_user)])
app.include_router(strategy_router, dependencies=[Depends(get_current_user)])
app.include_router(price_monitor_router, dependencies=[Depends(get_current_user)])
app.include_router(price_alert_router, dependencies=[Depends(get_current_user)])
