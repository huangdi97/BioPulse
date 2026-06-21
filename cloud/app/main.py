"""FastAPI 应用入口，注册所有路由与中间件。"""

import logging
import os
from logging.handlers import RotatingFileHandler

from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles

from cloud.app.app_setup import register_routers, register_startup_events
from cloud.app.middleware.logging_middleware import JSONFormatter
from cloud.app.middleware.metrics import setup_metrics
from cloud.app.middleware_setup import register_middleware
from shared.app_settings import settings
from shared.health import router as health_router

_logger = logging.getLogger("cloud")
_logger.setLevel(getattr(logging, settings.log_level.upper(), logging.INFO))

os.makedirs("logs", exist_ok=True)
_stream_handler = logging.StreamHandler()
_stream_handler.setFormatter(JSONFormatter())
_file_handler = RotatingFileHandler("logs/biopulse.log", maxBytes=100 * 1024 * 1024, backupCount=5)
_file_handler.setFormatter(JSONFormatter())
if not _logger.handlers:
    _logger.addHandler(_stream_handler)
    _logger.addHandler(_file_handler)

app = FastAPI(
    title="BioPulse · Cloud API",
    description="面向医药+生物双主线的智能CRM SaaS。包含认证、合规、商机、Agent、记忆系统、知识图谱、MDT会诊、因果推理、合规规则引擎等核心模块。",
    version=settings.version,
    contact={"name": "BioPulse", "url": "https://biopulse.ai"},
    license_info={"name": "Proprietary", "identifier": "Proprietary"},
    terms_of_service="https://biopulse.ai/terms",
    swagger_ui_parameters={"docExpansion": "list", "defaultModelsExpandDepth": -1},
    openapi_tags=[
        {"name": "认证", "description": "用户登录、注册、令牌刷新、JWT验证"},
        {"name": "合规", "description": "合规检测、规则管理、合规仪表板、合规证书"},
        {"name": "商机", "description": "商机管理、线索跟踪、客户管理"},
        {"name": "拜访", "description": "拜访计划、执行、记录"},
        {"name": "Agent系统", "description": "Agent角色、管道、执行、记忆"},
        {"name": "MDT会诊", "description": "多专家会诊、辩论引擎、决策树"},
        {"name": "知识图谱", "description": "知识图谱查询、关系分析"},
        {"name": "记忆系统", "description": "记忆门控、巩固、世界树、效用评估"},
        {"name": "❄️ 因果推理", "description": "因果分析、决策推理（冻结）"},
        {"name": "团队管理", "description": "团队、看板、任务分配"},
        {"name": "审计日志", "description": "操作审计、合规审计链"},
        {"name": "数据导出", "description": "报表导出、数据分析"},
        {"name": "科研线", "description": "PI管理、产品匹配、询价报价、科研合规"},
        {"name": "配置", "description": "系统配置、个性化设置"},
        {"name": "系统", "description": "健康检查、服务状态"},
        {"name": "Token 管理", "description": "Token 预算配置、用量监控、告警管理"},
    ],
)

register_middleware(app)
register_routers(app)
register_startup_events(app)

setup_metrics(app)
app.include_router(health_router)


app.mount("/assets", StaticFiles(directory="static/assets"), name="assets")
os.makedirs("uploads", exist_ok=True)
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")


@app.api_route("/{path_name:path}", methods=["GET"])
async def catch_all(path_name: str):
    if path_name.startswith("api/") or path_name.startswith("assets/"):
        from starlette import status

        raise HTTPException(status.HTTP_404_NOT_FOUND)
    from starlette.responses import Response

    headers = {"Cache-Control": "no-cache, no-store, must-revalidate"}
    with open("static/index.html", "rb") as f:
        content = f.read()
    return Response(
        content=content,
        media_type="text/html",
        headers=headers,
    )
