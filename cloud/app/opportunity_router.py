from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from starlette import status

from cloud.app.services.opportunity_service import OpportunityService
from shared.auth import get_current_user
from shared.base import success

router = APIRouter(prefix="/opportunities", tags=["商机"])


class OpportunityCreate(BaseModel):
    customer_id: int
    name: str = Field(..., min_length=1, max_length=200)
    description: str = ""
    stage: str = "lead"
    estimated_value: float = 0.0
    actual_value: float = 0.0
    assigned_to: Optional[int] = None
    close_date: Optional[str] = None
    notes: str = ""


class OpportunityUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    stage: Optional[str] = None
    estimated_value: Optional[float] = None
    actual_value: Optional[float] = None
    assigned_to: Optional[int] = None
    close_date: Optional[str] = None
    notes: Optional[str] = None


class StageTransition(BaseModel):
    stage: str
    actual_value: Optional[float] = None


@router.post("/", status_code=status.HTTP_201_CREATED)
def create_opportunity(
    body: OpportunityCreate,
    current_user: dict = Depends(get_current_user),
    service: OpportunityService = Depends(),
) -> Any:
    user_id = int(current_user["sub"])
    row = service.create_opportunity(
        customer_id=body.customer_id, name=body.name,
        description=body.description, stage=body.stage,
        estimated_value=body.estimated_value, actual_value=body.actual_value,
        assigned_to=body.assigned_to, close_date=body.close_date,
        notes=body.notes, user_id=user_id,
    )
    return success(data=row)


@router.get("/")
def list_opportunities(
    stage: str = Query(None),
    assigned_to: int = Query(None),
    customer_id: int = Query(None),
    search: str = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: dict = Depends(get_current_user),
    service: OpportunityService = Depends(),
) -> Any:
    result = service.list_opportunities(
        stage=stage, assigned_to=assigned_to, customer_id=customer_id,
        search=search, page=page, page_size=page_size,
    )
    return success(data=result)


@router.get("/pipeline")
def get_pipeline(
    current_user: dict = Depends(get_current_user),
    service: OpportunityService = Depends(),
) -> Any:
    result = service.get_pipeline()
    return success(data=result)


@router.get("/{opp_id}")
def get_opportunity(
    opp_id: int,
    current_user: dict = Depends(get_current_user),
    service: OpportunityService = Depends(),
) -> Any:
    row = service.get_opportunity(opp_id)
    return success(data=row)


@router.patch("/{opp_id}")
def update_opportunity(
    opp_id: int,
    body: OpportunityUpdate,
    current_user: dict = Depends(get_current_user),
    service: OpportunityService = Depends(),
) -> Any:
    row = service.update_opportunity(
        opp_id=opp_id, name=body.name, description=body.description,
        stage=body.stage, estimated_value=body.estimated_value,
        actual_value=body.actual_value, assigned_to=body.assigned_to,
        close_date=body.close_date, notes=body.notes,
    )
    return success(data=row)


@router.delete("/{opp_id}")
def delete_opportunity(
    opp_id: int,
    current_user: dict = Depends(get_current_user),
    service: OpportunityService = Depends(),
) -> Any:
    service.delete_opportunity(opp_id)
    return success()


@router.patch("/{opp_id}/stage")
def transition_stage(
    opp_id: int,
    body: StageTransition,
    current_user: dict = Depends(get_current_user),
    service: OpportunityService = Depends(),
) -> Any:
    row = service.transition_stage(
        opp_id=opp_id, stage=body.stage,
        actual_value=body.actual_value,
    )
    return success(data=row)
