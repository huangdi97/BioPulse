"""ClinicalOps · 临床试验运营 — FastAPI 入口。"""

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware

from shared.auth import get_current_user
from shared.exception_handlers import register_exception_handlers
from shared.health import router as health_router
from shared.middleware import RequestIDMiddleware
from shared.structured_logging import setup_logging

from .database import init_cache_db
from .monitoring_router import router as monitoring_router
from .recruitment_router import router as recruitment_router
from .routers.milestone_tracker_router import router as milestone_tracker_router
from .routers.monitor_task_router import router as monitor_task_router
from .site_router import router as site_router

setup_logging("clinical-ops")

app = FastAPI(
    title="ClinicalOps · 临床试验运营",
    version="1.0.0",
    description="中心筛选、患者招募、监察报告管理",
    openapi_tags=[
        {"name": "里程碑", "description": "试验里程碑跟踪"},
        {"name": "监查", "description": "监察报告、进度追踪"},
        {"name": "中心管理", "description": "中心筛选、患者招募管理"},
    ],
)
_cors_origins = ["*"]
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


app.include_router(site_router, dependencies=[Depends(get_current_user)])
app.include_router(recruitment_router, dependencies=[Depends(get_current_user)])
app.include_router(monitoring_router, dependencies=[Depends(get_current_user)])
app.include_router(milestone_tracker_router, dependencies=[Depends(get_current_user)])
app.include_router(monitor_task_router, dependencies=[Depends(get_current_user)])
