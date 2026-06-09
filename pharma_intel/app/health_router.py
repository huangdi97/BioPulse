"""健康检查路由。"""

from fastapi import APIRouter

router = APIRouter(tags=["健康检查"])


@router.get("/health", tags=["情报源"])
def health():
    return {"status": "ok", "service": "pharma-intel", "version": "1.0.0"}
