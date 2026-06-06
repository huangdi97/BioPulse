"""患者教育路由。"""

from fastapi import APIRouter, Query

from patient_engage.app.services.education_service import (
    get_education_content,
    get_recommended_content,
    push_content,
)
from shared.base import success

router = APIRouter(prefix="/api/education", tags=["患者教育"])


@router.get("/content")
async def content(
    disease: str = Query(..., description="疾病名称"),
):
    """获取疾病教育内容。基于知识图谱和论文数据。"""
    result = await get_education_content(disease)
    return success(data=result)


@router.get("/recommended")
async def recommended(
    patient_id: str = Query(..., description="患者标识"),
):
    """个性化推荐内容。根据患者病情和治疗阶段匹配。"""
    result = await get_recommended_content(patient_id)
    return success(data=result)


@router.post("/push")
async def push(body: dict):
    """推送内容。将教育内容推送给指定患者群体。"""
    result = await push_content(
        body.get("content_id", ""),
        body.get("patient_ids", []),
    )
    return success(data=result)
