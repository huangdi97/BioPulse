"""患者教育路由。"""

from fastapi import APIRouter, Depends, Query

from shared.auth_scope import require_scope
from shared.base import success

from .services.education_service import (
    get_education_content,
    get_recommended_content,
    push_content,
)

router = APIRouter(prefix="/api/education")


@router.get("/content", tags=["患者"])
async def content(
    disease: str = Query(..., description="疾病名称"),
):
    """获取疾病教育内容。基于知识图谱和论文数据。"""
    result = await get_education_content(disease)
    return success(data=result)


@router.get("/recommended", tags=["患者"])
async def recommended(
    patient_id: str = Query(..., description="患者标识"),
):
    """个性化推荐内容。根据患者病情和治疗阶段匹配。"""
    result = await get_recommended_content(patient_id)
    return success(data=result)


@router.post("/push", tags=["患者"])
async def push(body: dict, _: dict = Depends(require_scope("visit"))):
    """推送内容。将教育内容推送给指定患者群体。"""
    result = await push_content(
        body.get("content_id", ""),
        body.get("patient_ids", []),
    )
    return success(data=result)
