from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel
from starlette import status

from cloud.app.services.training_coach_service import TrainingCoachService
from shared.auth_scope import require_scope
from shared.base import success, PaginatedResponse

router = APIRouter(prefix="/training-coach", tags=["Training Coach"])


class ModuleCreate(BaseModel):
    title: str
    category: str = "compliance"
    difficulty: str = "medium"
    content: str = ""
    prerequisites: list = []
    passing_score: float = 0.7
    estimated_minutes: int = 15


class SessionCreate(BaseModel):
    user_id: int
    module_id: int
    score: float = 0.0
    passed: int = 0
    time_spent_seconds: int = 0
    answers: list = []
    feedback: str = ""
    difficulty_used: str = "medium"


class AttributionCreate(BaseModel):
    user_id: int
    metric_name: str
    metric_before: float = 0.0
    metric_after: float = 0.0
    period_days: int = 30


@router.post("/modules", status_code=201)
def create_module(
    body: ModuleCreate,
    cu=Depends(require_scope("visit")),
    service: TrainingCoachService = Depends(),
) -> Any:
    row = service.create_module(
        title=body.title,
        category=body.category,
        difficulty=body.difficulty,
        content=body.content,
        prerequisites=body.prerequisites,
        passing_score=body.passing_score,
        estimated_minutes=body.estimated_minutes,
        created_by=cu["user_id"],
    )
    return success(row)


@router.get("/modules")
def list_modules(
    category: Optional[str] = None,
    difficulty: Optional[str] = None,
    cu=Depends(require_scope("visit")),
    service: TrainingCoachService = Depends(),
) -> Any:
    rows = service.list_modules(category=category, difficulty=difficulty)
    return success(rows)


@router.post("/sessions")
def create_session(
    body: SessionCreate,
    cu=Depends(require_scope("visit")),
    service: TrainingCoachService = Depends(),
) -> Any:
    row = service.create_session(
        user_id=body.user_id,
        module_id=body.module_id,
        score=body.score,
        passed=body.passed,
        time_spent_seconds=body.time_spent_seconds,
        answers=body.answers,
        feedback=body.feedback,
        difficulty_used=body.difficulty_used,
    )
    return success(row)


@router.get("/sessions")
def list_sessions(
    user_id: Optional[int] = None,
    module_id: Optional[int] = None,
    page: int = 1,
    page_size: int = 20,
    cu=Depends(require_scope("visit")),
    service: TrainingCoachService = Depends(),
) -> Any:
    result = service.list_sessions(
        user_id=user_id, module_id=module_id, page=page, page_size=page_size,
    )
    return success(data=PaginatedResponse(**result))


@router.get("/sessions/{session_id}")
def get_session(
    session_id: int,
    cu=Depends(require_scope("visit")),
    service: TrainingCoachService = Depends(),
) -> Any:
    row = service.get_session(session_id)
    return success(row)


@router.post("/recommend")
def recommend(
    body: Request,
    cu=Depends(require_scope("visit")),
    service: TrainingCoachService = Depends(),
) -> Any:
    result = service.recommend(cu["user_id"])
    return success(result)


@router.post("/attributions")
def create_attribution(
    body: AttributionCreate,
    cu=Depends(require_scope("visit")),
    service: TrainingCoachService = Depends(),
) -> Any:
    row = service.create_attribution(
        user_id=body.user_id,
        metric_name=body.metric_name,
        metric_before=body.metric_before,
        metric_after=body.metric_after,
        period_days=body.period_days,
    )
    return success(row)


@router.get("/attributions")
def list_attributions(
    user_id: Optional[int] = None,
    metric_name: Optional[str] = None,
    cu=Depends(require_scope("visit")),
    service: TrainingCoachService = Depends(),
) -> Any:
    rows = service.list_attributions(user_id=user_id, metric_name=metric_name)
    return success(rows)


@router.post("/attributions/{att_id}/analyze")
def analyze_attribution(
    att_id: int,
    cu=Depends(require_scope("visit")),
    service: TrainingCoachService = Depends(),
) -> Any:
    row = service.analyze_attribution(att_id)
    return success(row)


@router.get("/dashboard")
def dashboard(
    cu=Depends(require_scope("visit")),
    service: TrainingCoachService = Depends(),
) -> Any:
    result = service.dashboard()
    return success(result)
