from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from cloud.app.services.model_compression_service import ModelCompressionService
from shared.auth_scope import require_scope
from shared.base import success

router = APIRouter(prefix="/compression", tags=["模型压缩"])


class CompressRequest(BaseModel):
    """CompressRequest 服务类。"""

    model_name: str
    compression_type: str


@router.post("/compress", summary="Compress Model")
def compress_model(
    body: CompressRequest,
    current_user: dict = Depends(require_scope("visit")),
    service: ModelCompressionService = Depends(),
) -> Any:
    """compress_model 操作。

    Args:
        current_user: 描述
        service: 描述

    Returns:
        描述
    """
    result = service.compress(body.model_name, body.compression_type)
    return success(data=result)


@router.get("/jobs", summary="List all Jobs")
def list_jobs(
    status: Optional[str] = None,
    current_user: dict = Depends(require_scope("visit")),
    service: ModelCompressionService = Depends(),
) -> Any:
    """list_jobs 操作。

    Args:
        status: 描述
        current_user: 描述
        service: 描述

    Returns:
        描述
    """
    jobs = service.list_jobs(status)
    return success(data=jobs)


@router.get("/jobs/{job_id}", summary="Get Job by ID")
def get_job(
    job_id: str,
    current_user: dict = Depends(require_scope("visit")),
    service: ModelCompressionService = Depends(),
) -> Any:
    """get_job 操作。

    Args:
        job_id: 描述
        current_user: 描述
        service: 描述

    Returns:
        描述
    """
    job = service.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="压缩任务不存在")
    return success(data=job)


@router.delete("/jobs/{job_id}", summary="Delete Job")
def delete_job(
    job_id: str,
    current_user: dict = Depends(require_scope("visit")),
    service: ModelCompressionService = Depends(),
) -> Any:
    """delete_job 操作。

    Args:
        job_id: 描述
        current_user: 描述
        service: 描述

    Returns:
        描述
    """
    deleted = service.delete_job(job_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="压缩任务不存在")
    return success(data={"deleted": True})


@router.get("/types", summary="Get Available Types by ID")
def get_available_types(
    current_user: dict = Depends(require_scope("visit")),
    service: ModelCompressionService = Depends(),
) -> Any:
    """get_available_types 操作。

    Args:
        current_user: 描述
        service: 描述

    Returns:
        描述
    """
    types = service.get_available_types()
    return success(data=types)
