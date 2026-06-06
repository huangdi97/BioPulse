"""健康检查路由。"""

from fastapi import APIRouter

router = APIRouter(tags=["health"])


@router.get("/health", summary="健康检查", description="检查管理服务的运行状态和版本信息")
def health():
    return {"status": "ok", "service": "management", "version": "1.0.0"}
