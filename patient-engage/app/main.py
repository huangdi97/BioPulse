"""PatientEngage · 患者服务 — FastAPI 入口。"""

import time

from fastapi import FastAPI

from patient_engage.app.education_router import router as education_router
from patient_engage.app.followup_router import router as followup_router
from patient_engage.app.reminder_router import router as reminder_router
from shared.middleware import RequestIDMiddleware
from shared.structured_logging import setup_logging

START_TIME = time.time()

setup_logging("patient-engage")

app = FastAPI(
    title="PatientEngage · 患者服务",
    version="1.0.0",
    description="患者教育、用药提醒、随访管理",
)
app.add_middleware(RequestIDMiddleware)


@app.on_event("startup")
def startup():
    from patient_engage.app.database import init_cache_db

    init_cache_db()


@app.get("/health")
def health():
    return {
        "status": "ok",
        "uptime": int(time.time() - START_TIME),
        "service": "patient-engage",
    }


app.include_router(education_router)
app.include_router(reminder_router)
app.include_router(followup_router)
