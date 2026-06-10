"""制药情报服务主应用入口。"""

import time

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from pharma_intel.app.competitor_router import router as competitor_router
from pharma_intel.app.conference_router import router as conference_router
from pharma_intel.app.intel_router import router as intel_router
from pharma_intel.app.kol_router import router as kol_router
from pharma_intel.app.pipeline_router import router as pipeline_router
from pharma_intel.app.routers.competitor_landscape_router import router as competitor_landscape_router
from pharma_intel.app.routers.competitor_panel_router import router as competitor_panel_router
from pharma_intel.app.routers.target_pipeline_router import router as target_pipeline_router
from pharma_intel.app.target_router import router as target_router
from shared.app_settings import settings
from shared.auth import get_current_user
from shared.exception_handlers import register_exception_handlers
from shared.health import router as health_router
from shared.middleware import RequestIDMiddleware
from shared.structured_logging import setup_logging

START_TIME = time.time()

setup_logging("pharma_intel")

app = FastAPI(
    title="制药情报服务 · Pharma Intel",
    version=settings.version,
    description="KOL学术影响力追踪、靶点研究监控、管线竞争分析、竞品情报聚合、学术会议追踪",
    openapi_tags=[
        {"name": "靶点", "description": "靶点研究监控、趋势分析"},
        {"name": "管线", "description": "管线竞争分析、适应症追踪"},
        {"name": "竞争格局", "description": "竞品情报聚合、新闻追踪"},
        {"name": "情报源", "description": "综合情报查询、学术会议追踪"},
        {"name": "KOL", "description": "KOL学术影响力追踪"},
    ],
)
_cors_origins = settings.cors_origins
app.add_middleware(CORSMiddleware, allow_origins=_cors_origins, allow_credentials=_cors_origins != ["*"], allow_methods=["*"], allow_headers=["*"])
app.add_middleware(RequestIDMiddleware)
register_exception_handlers(app)


@app.on_event("startup")
def startup():
    from pharma_intel.app.database import init_cache_db

    init_cache_db()


app.include_router(health_router)
app.include_router(intel_router, dependencies=[Depends(get_current_user)])
app.include_router(kol_router, prefix="/api/v1", dependencies=[Depends(get_current_user)])
app.include_router(pipeline_router, prefix="/api/v1", dependencies=[Depends(get_current_user)])
app.include_router(target_router, prefix="/api/v1", dependencies=[Depends(get_current_user)])
app.include_router(competitor_router, prefix="/api/v1", dependencies=[Depends(get_current_user)])
app.include_router(target_pipeline_router, dependencies=[Depends(get_current_user)])
app.include_router(competitor_landscape_router, dependencies=[Depends(get_current_user)])
app.include_router(competitor_panel_router, dependencies=[Depends(get_current_user)])
app.include_router(conference_router, dependencies=[Depends(get_current_user)])

try:
    app.mount("/static", StaticFiles(directory="pharma_intel/app/static"), name="static")
except RuntimeError:
    pass
