"""ClinicalOps · 临床试验运营 — FastAPI 入口。"""

import time

from fastapi import FastAPI

from clinical_ops.app.monitoring_router import router as monitoring_router
from clinical_ops.app.recruitment_router import router as recruitment_router
from clinical_ops.app.site_router import router as site_router
from shared.middleware import RequestIDMiddleware

START_TIME = time.time()

app = FastAPI(
    title="ClinicalOps · 临床试验运营",
    version="1.0.0",
    description="中心筛选、患者招募、监察报告管理",
)
app.add_middleware(RequestIDMiddleware)


@app.on_event("startup")
def startup():
    from clinical_ops.app.database import init_cache_db

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
