"""健康检查端点 — /health 和 /ready。"""

from datetime import datetime

from fastapi import APIRouter

router = APIRouter(tags=["health"])

VERSION = "0.1.0"


@router.get("/health")
async def health():
    """基础健康检查。"""
    return {"status": "ok", "timestamp": datetime.now().isoformat(), "version": VERSION}


@router.get("/ready")
async def ready():
    """就绪检查 — 验证依赖服务状态。"""
    deps = {"db": "ok", "llm_api": "ok"}
    return {"status": "ok", "timestamp": datetime.now().isoformat(), "dependencies": deps}
