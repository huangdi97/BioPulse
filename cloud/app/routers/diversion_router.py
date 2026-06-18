"""窜货检测路由。"""

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel

from cloud.app.database import get_db
from cloud.app.services.diversion_service import DiversionDetectionService
from shared.base import success

router = APIRouter(prefix="/diversion", tags=["窜货检测"])


class CheckDistributionRequest(BaseModel):
    product: str
    region: str
    quantity: int = 0
    dealer_id: str = ""
    rep_id: str = ""


class BatchCheckRequest(BaseModel):
    distributions: list[CheckDistributionRequest]


@router.post("/check", summary="检测窜货", description="检测产品流向是否存在窜货风险")
def check_distribution(
    body: CheckDistributionRequest,
    db=Depends(get_db),
):
    service = DiversionDetectionService(db)
    return success(data=service.check_distribution(body.model_dump()))


@router.post("/run-batch", summary="批量检测窜货", description="批量检测多笔产品流向，每笔均经三角稽核引擎验证")
def run_batch(
    body: BatchCheckRequest,
    db=Depends(get_db),
):
    service = DiversionDetectionService(db)
    results = []
    for dist in body.distributions:
        check_result = service.check_distribution(dist.model_dump())
        triangulation = service.run_triangulation_check(dist.model_dump())
        results.append(
            {
                "product": dist.product,
                "region": dist.region,
                "check": check_result,
                "triangulation": triangulation,
            }
        )
    return success(data=results)


@router.get("/records/{rep_id}", summary="查询窜货记录", description="查询代表在指定天数内的窜货记录")
def get_records(
    rep_id: str,
    days: int = Query(30, ge=1, le=365),
    db=Depends(get_db),
):
    service = DiversionDetectionService(db)
    return success(data=service.get_diversion_records(rep_id, days))
