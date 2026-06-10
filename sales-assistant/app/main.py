"""销售助手应用入口：FastAPI应用组装、中间件与路由注册。"""

import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from sales_assistant.app import research_hcp_router, research_order_router, sales_assistant_research_quotation_router
from sales_assistant.app.anomaly_router import router as anomaly_router
from sales_assistant.app.coach_router import router as coach_router
from sales_assistant.app.content_router import content_root_router
from sales_assistant.app.content_router import router as content_router
from sales_assistant.app.database import init_db
from sales_assistant.app.funnel_router import router as funnel_router
from sales_assistant.app.note_router import router as note_router
from sales_assistant.app.objection_router import router as objection_router
from sales_assistant.app.precall_router import router as precall_router
from sales_assistant.app.routers.academic_meeting_router import router as academic_meeting_router
from sales_assistant.app.routers.competitor_quicklook_router import router as competitor_quicklook_router
from sales_assistant.app.routers.schedule_optimizer_router import router as schedule_optimizer_router
from sales_assistant.app.routers.voice_analysis_router import router as voice_analysis_router
from sales_assistant.app.sales_assistant_hcp_router import router as hcp_router
from sales_assistant.app.sales_assistant_strategy_router import router as strategy_router
from sales_assistant.app.sales_assistant_strategy_router import strategy_root_router
from sales_assistant.app.schedule_router import router as schedule_router
from shared.app_settings import settings
from shared.exception_handlers import register_exception_handlers
from shared.health import router as health_router
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


app = FastAPI(
    title="Sales Assistant Service",
    version=settings.version,
    openapi_tags=[
        {"name": "拜访", "description": "拜访计划、执行、记录、日程管理"},
        {"name": "HCP", "description": "HCP信息管理、关系图谱"},
        {"name": "科研PI", "description": "科研PI信息、询价报价、订单管理"},
        {"name": "合规检查", "description": "异常检测、合规风险检查与告警"},
        {"name": "任务", "description": "任务管理、异常跟进"},
        {"name": "产品", "description": "产品信息、资料与HCP产品关联"},
        {"name": "情报", "description": "预拜访策略、异议处理、漏斗分析"},
    ],
)

setup_logging("sales_assistant")

_cors_origins = settings.cors_origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
    allow_credentials=_cors_origins != ["*"],
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


app.include_router(health_router)
app.include_router(schedule_router)
app.include_router(note_router)
app.include_router(hcp_router, tags=["hcp", "products"])
app.include_router(research_hcp_router.router)
app.include_router(sales_assistant_research_quotation_router.router)
app.include_router(research_order_router.router)
app.include_router(precall_router)
app.include_router(objection_router)
app.include_router(funnel_router)
app.include_router(content_router)
app.include_router(coach_router)
app.include_router(anomaly_router)
app.include_router(strategy_router)
app.include_router(strategy_root_router)
app.include_router(content_root_router)
app.include_router(voice_analysis_router)
app.include_router(schedule_optimizer_router)
app.include_router(academic_meeting_router)
app.include_router(competitor_quicklook_router)
