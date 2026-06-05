from fastapi import APIRouter

router = APIRouter(tags=["健康检查"])


@router.get("/health")
def health():
    return {"status": "ok", "service": "pharma-intel", "version": "1.0.0"}
