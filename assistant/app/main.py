"""应用入口模块，创建 FastAPI 实例，注册中间件与路由。"""

import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from assistant.app.database import init_db
from assistant.app.hcp_router import hcp_alias_router
from assistant.app.hcp_router import router as hcp_router
from assistant.app.health_radar_router import router as health_radar_router
from assistant.app.health_router import router as health_router
from assistant.app.knowledge_router import router as knowledge_router
from assistant.app.knowledge_seed import seed_knowledge
from assistant.app.location_router import router as location_router
from assistant.app.media_router import router as media_router
from assistant.app.offline_router import router as offline_router
from assistant.app.qa_router import router as qa_router
from assistant.app.reminder_scheduler import start_scheduler
from assistant.app.routers.inventory_warning_router import router as inventory_warning_router
from assistant.app.routers.route_optimization_router import router as route_optimization_router
from assistant.app.surgery_router import router as surgery_router
from assistant.app.sync_router import router as sync_router
from assistant.app.task_router import router as task_router
from assistant.app.visit_router import router as visit_router
from assistant.app.visit_router import visit_alias_router
from assistant.app.voice_router import router as voice_router
from assistant.app.ws_router import router as ws_router
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


app = FastAPI(
    title="Assistant Service",
    version=settings.version,
    openapi_tags=[
        {"name": "设备", "description": "设备信息查询与管理"},
        {"name": "库存", "description": "库存查询、知识库管理"},
        {"name": "手术记录", "description": "手术提醒、手术记录管理"},
        {"name": "路径优化", "description": "位置服务、路径规划"},
        {"name": "离线同步", "description": "离线数据同步、WebSocket实时通信"},
    ],
)

setup_logging("assistant")

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
    """Initialize database tables, L1 rule cache, and seed data on startup."""
    init_db()
    _init_l1_cache("pharma")
    seed_knowledge()
    start_scheduler()


app.include_router(health_router)
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
app.include_router(offline_router)
app.include_router(visit_alias_router)
app.include_router(hcp_alias_router)
app.include_router(inventory_warning_router)
app.include_router(route_optimization_router)
