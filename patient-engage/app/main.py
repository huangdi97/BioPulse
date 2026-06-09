"""PatientEngage · 患者服务 — FastAPI 入口。"""

import time

from fastapi import FastAPI

from shared.middleware import RequestIDMiddleware
from shared.structured_logging import setup_logging

from .database import init_cache_db
from .education_router import router as education_router
from .followup_router import router as followup_router
from .reminder_router import router as reminder_router
from .routers.gamification_router import router as gamification_router
from .routers.patient_weapp_router import router as patient_weapp_router

START_TIME = time.time()

setup_logging("patient-engage")

app = FastAPI(
    title="PatientEngage · 患者服务",
    version="1.0.0",
    description="患者教育、用药提醒、随访管理",
    openapi_tags=[
        {"name": "患者", "description": "患者教育内容管理"},
        {"name": "用药提醒", "description": "用药提醒创建、状态查询、依从性分析"},
        {"name": "依从性", "description": "随访管理、依从性追踪"},
        {"name": "患者小程序", "description": "微信小程序用药提醒与打卡"},
        {"name": "游戏化激励", "description": "患者积分、奖励与排行榜"},
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
        "service": "patient-engage",
    }


app.include_router(education_router)
app.include_router(reminder_router)
app.include_router(followup_router)
app.include_router(patient_weapp_router)
app.include_router(gamification_router)
