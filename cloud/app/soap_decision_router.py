from typing import Optional

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel

from cloud.app.services.soap_decision_service import SoapDecisionService
from shared.auth_scope import require_scope
from shared.base import success

router = APIRouter(prefix="/soap", tags=["SOAP Decision"])


class TemplateCreate(BaseModel):
    name: str
    category: str = "general"
    description: str = ""
    structure: dict = {}


class DecisionCreate(BaseModel):
    title: str
    template_id: Optional[int] = None
    subjective: str = ""
    objective: str = ""
    assessment: str = ""
    plan: str = ""
    priority: str = "medium"
    tags: list = []


class DecisionUpdate(BaseModel):
    subjective: Optional[str] = None
    objective: Optional[str] = None
    assessment: Optional[str] = None
    plan: Optional[str] = None
    priority: Optional[str] = None
    tags: Optional[list] = None


class OpinionCreate(BaseModel):
    opinion: str
    stance: str = "neutral"
    supporting_data: str = ""
    confidence: float = 0.5
    attachments: list = []


class FinalizeRequest(BaseModel):
    decision_summary: str


@router.post("/templates", status_code=201)
def create_template(
    body: TemplateCreate,
    cu=Depends(require_scope("visit")),
    service: SoapDecisionService = Depends(),
):
    return success(
        service.create_template(
            name=body.name,
            category=body.category,
            description=body.description,
            structure=body.structure,
            created_by=cu["user_id"],
        )
    )


@router.get("/templates")
def list_templates(
    category: Optional[str] = None,
    cu=Depends(require_scope("visit")),
    service: SoapDecisionService = Depends(),
):
    return success(service.list_templates(category=category))


@router.post("/decisions", status_code=201)
def create_decision(
    body: DecisionCreate,
    cu=Depends(require_scope("visit")),
    service: SoapDecisionService = Depends(),
):
    return success(
        service.create_decision(
            title=body.title,
            template_id=body.template_id,
            subjective=body.subjective,
            objective=body.objective,
            assessment=body.assessment,
            plan=body.plan,
            priority=body.priority,
            tags=body.tags,
            created_by=cu["user_id"],
        )
    )


@router.get("/decisions")
def list_decisions(
    status: Optional[str] = None,
    priority: Optional[str] = None,
    tag: Optional[str] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    cu=Depends(require_scope("visit")),
    service: SoapDecisionService = Depends(),
):
    return success(
        data=service.list_decisions(status=status, priority=priority, tag=tag, page=page, page_size=page_size)
    )


@router.get("/decisions/{decision_id}")
def get_decision(
    decision_id: int,
    cu=Depends(require_scope("visit")),
    service: SoapDecisionService = Depends(),
):
    return success(service.get_decision(decision_id))


@router.patch("/decisions/{decision_id}")
def update_decision(
    decision_id: int,
    body: DecisionUpdate,
    cu=Depends(require_scope("visit")),
    service: SoapDecisionService = Depends(),
):
    return success(
        service.update_decision(
            decision_id=decision_id,
            subjective=body.subjective,
            objective=body.objective,
            assessment=body.assessment,
            plan=body.plan,
            priority=body.priority,
            tags=body.tags,
        )
    )


@router.post("/decisions/{decision_id}/submit")
def submit_decision(
    decision_id: int,
    cu=Depends(require_scope("visit")),
    service: SoapDecisionService = Depends(),
):
    return success(service.submit_decision(decision_id))


@router.post("/decisions/{decision_id}/opinions")
def add_opinion(
    decision_id: int,
    body: OpinionCreate,
    cu=Depends(require_scope("visit")),
    service: SoapDecisionService = Depends(),
):
    return success(
        service.add_opinion(
            decision_id=decision_id,
            opinion=body.opinion,
            stance=body.stance,
            supporting_data=body.supporting_data,
            confidence=body.confidence,
            attachments=body.attachments,
            user_id=cu["user_id"],
            role=cu.get("role", ""),
        )
    )


@router.get("/decisions/{decision_id}/opinions")
def list_opinions(
    decision_id: int,
    cu=Depends(require_scope("visit")),
    service: SoapDecisionService = Depends(),
):
    return success(service.list_opinions(decision_id))


@router.post("/decisions/{decision_id}/finalize")
def finalize_decision(
    decision_id: int,
    body: FinalizeRequest,
    cu=Depends(require_scope("visit")),
    service: SoapDecisionService = Depends(),
):
    return success(
        service.finalize_decision(
            decision_id=decision_id,
            decision_summary=body.decision_summary,
            user_id=cu["user_id"],
        )
    )


@router.get("/dashboard")
def dashboard(cu=Depends(require_scope("visit")), service: SoapDecisionService = Depends()):
    return success(service.dashboard())
