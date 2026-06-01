from typing import Optional

from fastapi import APIRouter, Depends, Query, Request
from pydantic import BaseModel

from cloud.app.services.decision_intel_service import DecisionIntelService
from shared.auth_scope import require_scope
from shared.base import PaginatedResponse, success

router = APIRouter(prefix="/decision-intel", tags=["Decision Intelligence"])


class CaseCreate(BaseModel):
    name: str
    pipeline_run_id: Optional[int] = None
    description: str = ""
    outcome: str = ""
    outcome_score: float = 0.0
    context: dict = {}
    tags: list = []


class CaseUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    outcome: Optional[str] = None
    outcome_score: Optional[float] = None
    context: Optional[dict] = None
    tags: Optional[list] = None


class AnalyzeRequest(BaseModel):
    custom_question: str = ""


class ReflectRequest(BaseModel):
    filter_tags: list = []
    max_cases: int = 10


class InsightUpdate(BaseModel):
    title: Optional[str] = None
    summary: Optional[str] = None
    confidence: Optional[float] = None
    applicability: Optional[str] = None


@router.post("/cases", status_code=201)
def create_case(
    body: CaseCreate,
    request: Request,
    current_user=Depends(require_scope("visit")),
    service: DecisionIntelService = Depends(),
):
    uid = int(current_user["sub"])
    row = service.create_case(
        name=body.name,
        pipeline_run_id=body.pipeline_run_id,
        description=body.description,
        outcome=body.outcome,
        outcome_score=body.outcome_score,
        context=body.context,
        tags=body.tags,
        uid=uid,
    )
    return success(data=row)


@router.get("/cases")
def list_cases(
    outcome_score_min: Optional[float] = Query(None),
    outcome_score_max: Optional[float] = Query(None),
    tag: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user=Depends(require_scope("visit")),
    service: DecisionIntelService = Depends(),
):
    result = service.list_cases(
        outcome_score_min=outcome_score_min,
        outcome_score_max=outcome_score_max,
        tag=tag,
        search=search,
        page=page,
        page_size=page_size,
    )
    return success(
        data=PaginatedResponse(
            items=result["items"],
            total=result["total"],
            page=result["page"],
            page_size=result["page_size"],
            total_pages=result["total_pages"],
        )
    )


@router.get("/cases/{case_id}")
def get_case(
    case_id: int,
    current_user=Depends(require_scope("visit")),
    service: DecisionIntelService = Depends(),
):
    row = service.get_case(case_id)
    return success(data=row)


@router.patch("/cases/{case_id}")
def update_case(
    case_id: int,
    body: CaseUpdate,
    current_user=Depends(require_scope("visit")),
    service: DecisionIntelService = Depends(),
):
    row = service.update_case(
        case_id=case_id,
        name=body.name,
        description=body.description,
        outcome=body.outcome,
        outcome_score=body.outcome_score,
        context=body.context,
        tags=body.tags,
    )
    return success(data=row)


@router.delete("/cases/{case_id}")
def delete_case(
    case_id: int,
    current_user=Depends(require_scope("visit")),
    service: DecisionIntelService = Depends(),
):
    service.delete_case(case_id)
    return success(message="deleted")


@router.post("/cases/{case_id}/analyze")
def analyze_case(
    case_id: int,
    body: AnalyzeRequest,
    request: Request,
    current_user=Depends(require_scope("visit")),
    service: DecisionIntelService = Depends(),
):
    auth_header = request.headers.get("Authorization", "")
    result = service.analyze_case(
        case_id=case_id,
        custom_question=body.custom_question,
        auth_header=auth_header,
    )
    return success(data=result)


@router.get("/cases/{case_id}/analyses")
def list_analyses(
    case_id: int,
    current_user=Depends(require_scope("visit")),
    service: DecisionIntelService = Depends(),
):
    rows = service.list_analyses(case_id)
    return success(data=rows)


@router.get("/analyses/{analysis_id}")
def get_analysis(
    analysis_id: int,
    current_user=Depends(require_scope("visit")),
    service: DecisionIntelService = Depends(),
):
    row = service.get_analysis(analysis_id)
    return success(data=row)


@router.post("/reflect")
def reflect(
    body: ReflectRequest,
    request: Request,
    current_user=Depends(require_scope("visit")),
    service: DecisionIntelService = Depends(),
):
    auth_header = request.headers.get("Authorization", "")
    result = service.reflect(
        filter_tags=body.filter_tags,
        max_cases=body.max_cases,
        auth_header=auth_header,
    )
    return success(data=result)


@router.get("/insights")
def list_insights(
    insight_type: Optional[str] = Query(None),
    confidence_min: Optional[float] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user=Depends(require_scope("visit")),
    service: DecisionIntelService = Depends(),
):
    result = service.list_insights(
        insight_type=insight_type,
        confidence_min=confidence_min,
        page=page,
        page_size=page_size,
    )
    return success(
        data=PaginatedResponse(
            items=result["items"],
            total=result["total"],
            page=result["page"],
            page_size=result["page_size"],
            total_pages=result["total_pages"],
        )
    )


@router.get("/insights/{insight_id}")
def get_insight(
    insight_id: int,
    current_user=Depends(require_scope("visit")),
    service: DecisionIntelService = Depends(),
):
    row = service.get_insight(insight_id)
    return success(data=row)


@router.patch("/insights/{insight_id}")
def update_insight(
    insight_id: int,
    body: InsightUpdate,
    current_user=Depends(require_scope("visit")),
    service: DecisionIntelService = Depends(),
):
    row = service.update_insight(
        insight_id=insight_id,
        title=body.title,
        summary=body.summary,
        confidence=body.confidence,
        applicability=body.applicability,
    )
    return success(data=row)


@router.get("/dashboard")
def dashboard(
    current_user=Depends(require_scope("visit")),
    service: DecisionIntelService = Depends(),
):
    result = service.dashboard()
    return success(data=result)
