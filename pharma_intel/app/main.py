"""制药情报服务主应用入口。"""

import time

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from pharma_intel.app.competitor_router import router as competitor_router
from pharma_intel.app.conference_router import router as conference_router
from pharma_intel.app.health_router import router as health_router
from pharma_intel.app.intel_router import router as intel_router
from pharma_intel.app.kol_router import router as kol_router
from pharma_intel.app.pipeline_router import router as pipeline_router
from pharma_intel.app.target_router import router as target_router
from shared.app_settings import settings
from shared.exception_handlers import register_exception_handlers
from shared.middleware import RequestIDMiddleware
from shared.structured_logging import setup_logging

START_TIME = time.time()

setup_logging("pharma_intel")

app = FastAPI(
    title=settings.app_name,
    version=settings.version,
    description="KOL学术影响力追踪、靶点研究监控、管线竞争分析、竞品情报聚合、学术会议追踪",
)
app.add_middleware(CORSMiddleware, allow_origins=settings.cors_origins, allow_methods=["*"], allow_headers=["*"])
app.add_middleware(RequestIDMiddleware)
register_exception_handlers(app)


@app.on_event("startup")
def startup():
    from pharma_intel.app.database import init_cache_db

    init_cache_db()


app.include_router(health_router)
app.include_router(intel_router)
app.include_router(kol_router, prefix="/api/v1")
app.include_router(pipeline_router, prefix="/api/v1")
app.include_router(target_router, prefix="/api/v1")
app.include_router(competitor_router, prefix="/api/v1")
app.include_router(conference_router)

try:
    app.mount("/static", StaticFiles(directory="pharma_intel/app/static"), name="static")
except RuntimeError:
    pass
