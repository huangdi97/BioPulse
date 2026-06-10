"""合规培训 API。"""

from fastapi import APIRouter, Depends

from sales_coach.app.schemas.compliance_training import (
    ComplianceCheckResult,
    TrainingMaterial,
)
from sales_coach.app.services.compliance_training_service import (
    check_compliance,
    get_compliance_result,
    save_training_material,
)
from shared.auth_scope import require_scope
from shared.base import ApiResponse, success

router = APIRouter(prefix="/api/compliance", tags=["合规培训"])


@router.post("/check", summary="合规材料检查", description="检查培训材料中的合规风险", tags=["合规培训"])
def check_training_material(body: TrainingMaterial, _: dict = Depends(require_scope("visit"))) -> ApiResponse[ComplianceCheckResult]:
    save_training_material(body)
    return success(data=check_compliance(body.id))


@router.get("/result/{material_id}", summary="合规检查结果", description="获取材料最近一次检查结果", tags=["合规培训"])
def get_training_material_result(material_id: str, _: dict = Depends(require_scope("visit"))) -> ApiResponse[ComplianceCheckResult]:
    return success(data=get_compliance_result(material_id))
