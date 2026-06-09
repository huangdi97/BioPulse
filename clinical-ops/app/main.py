"""ClinicalOps · 临床试验运营 — FastAPI 入口。"""

import time

from fastapi import FastAPI

from shared.middleware import RequestIDMiddleware

from .database import init_cache_db
from .monitoring_router import router as monitoring_router
from .recruitment_router import router as recruitment_router
from .routers.milestone_tracker_router import router as milestone_tracker_router
from .routers.monitor_task_router import router as monitor_task_router
from .site_router import router as site_router

START_TIME = time.time()

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
app.add_middleware(RequestIDMiddleware)


@app.on_event("startup")
def startup():
    init_cache_db()


@app.get("/health")
def health():
    return {
        "status": "ok",
        "uptime": int(time.time() - START_TIME),
        "service": "clinical-ops",
    }


app.include_router(site_router)
app.include_router(recruitment_router)
app.include_router(monitoring_router)
app.include_router(milestone_tracker_router)
app.include_router(monitor_task_router)
