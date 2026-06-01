import time

from fastapi import FastAPI

from shared.middleware import RequestIDMiddleware

START_TIME = time.time()
CLOUD_API_BASE = "http://localhost:8000"

app = FastAPI(
    title="制药情报服务 · Pharma Intel",
    version="1.0.0",
    description="KOL学术影响力追踪、靶点研究监控、管线竞争分析、竞品情报聚合、学术会议追踪",
)
app.add_middleware(RequestIDMiddleware)


@app.on_event("startup")
def startup():
    from pharma_intel.app.database import init_cache_db

    init_cache_db()


@app.get("/health")
def health():
    return {
        "status": "ok",
        "uptime": int(time.time() - START_TIME),
        "service": "pharma-intel",
    }


from pharma_intel.app.competitor_router import router as competitor_router
from pharma_intel.app.conference_router import router as conference_router
from pharma_intel.app.kol_router import router as kol_router
from pharma_intel.app.pipeline_router import router as pipeline_router
from pharma_intel.app.target_router import router as target_router

app.include_router(kol_router, prefix="/api/v1")
app.include_router(pipeline_router, prefix="/api/v1")
app.include_router(target_router, prefix="/api/v1")
app.include_router(competitor_router, prefix="/api/v1")
app.include_router(conference_router)
