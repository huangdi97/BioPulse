from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from starlette import status

from shared.auth import get_current_user
from shared.base import ApiResponse, PaginatedResponse, success
from sales_coach.app.database import get_db
from sales_coach.app.services.assessment_service import (
    AssessmentService,
    DEFAULT_WEIGHTS,
)
from sales_coach.app.services.reflection_service import generate_reflection_report
from sales_coach.app.services.session_service import SessionService

router = APIRouter(prefix="/assessments", tags=["assessments"])


class AssessmentCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    trainee_name: str
    assessment_date: Optional[str] = None
    current_level: Optional[str] = "beginner"
    target_level: Optional[str] = "intermediate"
    strengths: Optional[str] = None
    weaknesses: Optional[str] = None
    recommended_modules: Optional[str] = None
    notes: Optional[str] = None


class AssessmentUpdate(BaseModel):
    trainee_name: Optional[str] = None
    assessment_date: Optional[str] = None
    current_level: Optional[str] = None
    target_level: Optional[str] = None
    strengths: Optional[str] = None
    weaknesses: Optional[str] = None
    recommended_modules: Optional[str] = None
    notes: Optional[str] = None
    is_active: Optional[int] = None


class WeightConfig(BaseModel):
    product_knowledge: float = Field(0.3, ge=0, le=1)
    communication: float = Field(0.25, ge=0, le=1)
    compliance: float = Field(0.25, ge=0, le=1)
    objection_handling: float = Field(0.2, ge=0, le=1)


class AssessmentOut(BaseModel):
    id: int
    trainee_name: str
    assessment_date: Optional[str] = None
    current_level: str
    target_level: str
    strengths: Optional[str] = None
    weaknesses: Optional[str] = None
    recommended_modules: Optional[str] = None
    notes: Optional[str] = None
    is_active: int
    created_by: Optional[int] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


@router.post("")
def create_assessment(
    body: AssessmentCreate,
    service: AssessmentService = Depends(),
    current_user: dict = Depends(get_current_user),
) -> JSONResponse:
    """Create a new education assessment."""
    user_id = int(current_user["sub"])
    result = service.create(body, user_id)
    return JSONResponse(
        content=success(data=result).model_dump(),
        status_code=status.HTTP_201_CREATED,
    )


@router.get("")
def list_assessments(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    trainee_name: Optional[str] = Query(None),
    current_level: Optional[str] = Query(None),
    target_level: Optional[str] = Query(None),
    service: AssessmentService = Depends(),
    current_user: dict = Depends(get_current_user),
) -> ApiResponse[PaginatedResponse[AssessmentOut]]:
    """List assessments with pagination and filtering."""
    total, total_pages, rows = service.list(
        page,
        page_size,
        trainee_name,
        current_level,
        target_level,
    )
    items = [AssessmentOut(**dict(r)) for r in rows]
    return success(
        data=PaginatedResponse(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        )
    )


@router.get("/stats")
def get_assessment_stats(
    service: AssessmentService = Depends(),
    current_user: dict = Depends(get_current_user),
) -> ApiResponse[dict]:
    """Get aggregate statistics for assessments."""
    data = service.get_stats()
    return success(data=data)


@router.get("/{assessment_id}")
def get_assessment(
    assessment_id: int,
    service: AssessmentService = Depends(),
    current_user: dict = Depends(get_current_user),
) -> ApiResponse[AssessmentOut]:
    """Get a single assessment by ID."""
    row = service.get(assessment_id)
    return success(data=AssessmentOut(**row))


@router.patch("/{assessment_id}")
def update_assessment(
    assessment_id: int,
    body: AssessmentUpdate,
    service: AssessmentService = Depends(),
    current_user: dict = Depends(get_current_user),
) -> ApiResponse[AssessmentOut]:
    """Update an assessment."""
    updated = service.update(assessment_id, body)
    return success(data=AssessmentOut(**updated))


@router.delete("/{assessment_id}")
def delete_assessment(
    assessment_id: int,
    service: AssessmentService = Depends(),
    current_user: dict = Depends(get_current_user),
) -> ApiResponse:
    """Soft-delete an assessment by setting is_active to 0."""
    service.delete(assessment_id)
    return success(message="deleted")


@router.post("/{assessment_id}/reflect")
def reflect_on_assessment(
    assessment_id: int,
    service: AssessmentService = Depends(),
    session_service: SessionService = Depends(),
    db=Depends(get_db),
    current_user: dict = Depends(get_current_user),
) -> ApiResponse:
    """生成反思报告并关联到评分记录。"""
    assessment = service.get(assessment_id)
    if not assessment:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Assessment not found")
    sessions = db.execute(
        "SELECT id, dialogue_log, compliance_violations, scenario_id "
        "FROM coach_session WHERE trainee_name = ? "
        "ORDER BY id DESC LIMIT 1",
        (assessment.get("trainee_name", ""),),
    ).fetchone()
    if not sessions:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND, detail="No session found for trainee"
        )
    dialogue_log = json.loads(sessions["dialogue_log"] or "[]")
    violations = sessions["compliance_violations"] or 0
    reflection = generate_reflection_report(
        session_id=sessions["id"],
        dialogue_log=dialogue_log,
        compliance_violations=violations,
    )
    updated = service.update_assessment_with_reflection(assessment_id, reflection)
    return success(data={"assessment": updated, "reflection": reflection})


@router.get("/trend/{user_id}")
def get_assessment_trend(
    user_id: int,
    limit: int = Query(10, ge=1, le=100),
    service: AssessmentService = Depends(),
    current_user: dict = Depends(get_current_user),
) -> ApiResponse:
    """获取指定用户的评分趋势。"""
    trend = service.get_trend(user_id, limit=limit)
    return success(data={"user_id": user_id, "trend": trend})


@router.get("/weights")
def get_weights(
    current_user: dict = Depends(get_current_user),
) -> ApiResponse:
    """获取当前评分权重配置。"""
    return success(data=DEFAULT_WEIGHTS)


@router.put("/weights")
def update_weights(
    body: WeightConfig,
    current_user: dict = Depends(get_current_user),
) -> ApiResponse:
    """更新评分权重配置。"""
    total = (
        body.product_knowledge
        + body.communication
        + body.compliance
        + body.objection_handling
    )
    if abs(total - 1.0) > 0.01:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Weights must sum to 1.0"
        )
    DEFAULT_WEIGHTS.update(body.model_dump())
    return success(data=DEFAULT_WEIGHTS, message="Weights updated")
