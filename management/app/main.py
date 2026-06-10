"""管理端主应用入口。"""

import os

from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from fastapi.staticfiles import StaticFiles

from shared.app_settings import settings
from shared.auth import get_current_user
from shared.exception_handlers import register_exception_handlers
from shared.middleware import RequestIDMiddleware
from shared.structured_logging import setup_logging

setup_logging("management")

app = FastAPI(
    title="管理端 · Management Portal",
    version=settings.version,
    openapi_tags=[
        {"name": "看板", "description": "总裁/经理/员工三级看板数据"},
        {"name": "团队", "description": "员工管理、团队统计"},
        {"name": "合规", "description": "合规检测、审计管理"},
        {"name": "审计", "description": "操作审计、合规审计与追踪"},
        {"name": "配置", "description": "系统配置、个性化设置"},
    ],
)

app.add_middleware(RequestIDMiddleware)
register_exception_handlers(app)
_cors_origins = settings.cors_origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
    allow_credentials=_cors_origins != ["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def startup():
    from management.app.database import init_db

    init_db()


from management.app.employee_router import router as employee_router
from management.app.management_dashboard_router import router as dashboard_router
from management.app.manager_router import router as manager_router
from management.app.president_router import router as president_router
from management.app.routers.competitor_dashboard_router import router as competitor_dashboard_router
from management.app.routers.kpi_comparison_router import router as kpi_comparison_router
from management.app.routers.trend_analysis_router import router as trend_analysis_router
from shared.health import router as health_router

app.include_router(health_router)
app.include_router(dashboard_router, dependencies=[Depends(get_current_user)])
app.include_router(employee_router, dependencies=[Depends(get_current_user)])
app.include_router(manager_router, dependencies=[Depends(get_current_user)])
app.include_router(president_router, dependencies=[Depends(get_current_user)])
app.include_router(competitor_dashboard_router, dependencies=[Depends(get_current_user)])
app.include_router(kpi_comparison_router, dependencies=[Depends(get_current_user)])
app.include_router(trend_analysis_router, dependencies=[Depends(get_current_user)])

STATIC_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")
if os.path.isdir(STATIC_DIR):
    app.mount(
        "/assets",
        StaticFiles(directory=os.path.join(STATIC_DIR, "assets")),
        name="assets",
    )

    @app.api_route("/{path_name:path}", methods=["GET"])
    async def catch_all(path_name: str):
        if path_name.startswith("api/") or path_name.startswith("assets/"):
            raise HTTPException(status_code=404)
        with open(os.path.join(STATIC_DIR, "index.html"), "rb") as f:
            content = f.read()
        return Response(
            content=content,
            media_type="text/html",
        )
