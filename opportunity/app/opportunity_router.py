from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from starlette import status

from shared.auth import get_current_user
from shared.base import ApiResponse, PaginatedResponse, success
from opportunity.app.services.opportunity_service import OpportunityService

router = APIRouter(prefix="/opportunities", tags=["opportunities"])


class OpportunityCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    hcp_name: Optional[str] = None
    hospital: Optional[str] = None
    department: Optional[str] = None
    product: Optional[str] = None
    estimated_value: Optional[float] = None
    stage: Optional[str] = "lead"
    probability: Optional[int] = 10
    expected_close_date: Optional[str] = None
    notes: Optional[str] = None


class OpportunityUpdate(BaseModel):
    name: Optional[str] = None
    hcp_name: Optional[str] = None
    hospital: Optional[str] = None
    department: Optional[str] = None
    product: Optional[str] = None
    estimated_value: Optional[float] = None
    stage: Optional[str] = None
    probability: Optional[int] = None
    expected_close_date: Optional[str] = None
    notes: Optional[str] = None
    is_active: Optional[int] = None


class OpportunityOut(BaseModel):
    id: int
    name: str
    hcp_name: Optional[str] = None
    hospital: Optional[str] = None
    department: Optional[str] = None
    product: Optional[str] = None
    estimated_value: Optional[float] = None
    stage: str
    probability: int
    expected_close_date: Optional[str] = None
    notes: Optional[str] = None
    is_active: int
    created_by: Optional[int] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


@router.post("")
def create_opportunity(
    body: OpportunityCreate,
    service: OpportunityService = Depends(),
    current_user: dict = Depends(get_current_user),
) -> JSONResponse:
    user_id = int(current_user["sub"])
    id = service.create_opportunity(body, user_id)
    return JSONResponse(
        content=success(data={"id": id}).model_dump(),
        status_code=status.HTTP_201_CREATED,
    )


@router.get("")
def list_opportunities(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    stage: Optional[str] = Query(None),
    product: Optional[str] = Query(None),
    hcp_name: Optional[str] = Query(None),
    service: OpportunityService = Depends(),
    current_user: dict = Depends(get_current_user),
) -> ApiResponse[PaginatedResponse[OpportunityOut]]:
    total, total_pages, rows = service.list_opportunities(
        page=page, page_size=page_size,
        stage=stage, product=product, hcp_name=hcp_name,
    )
    items = [OpportunityOut(**dict(r)) for r in rows]
    return success(
        data=PaginatedResponse(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        )
    )


@router.get("/{opportunity_id}")
def get_opportunity(
    opportunity_id: int,
    service: OpportunityService = Depends(),
    current_user: dict = Depends(get_current_user),
) -> ApiResponse[OpportunityOut]:
    row = service.get_opportunity(opportunity_id)
    return success(data=OpportunityOut(**row))


@router.patch("/{opportunity_id}")
def update_opportunity(
    opportunity_id: int,
    body: OpportunityUpdate,
    service: OpportunityService = Depends(),
    current_user: dict = Depends(get_current_user),
) -> ApiResponse[OpportunityOut]:
    updated = service.update_opportunity(opportunity_id, body)
    return success(data=OpportunityOut(**updated))


@router.delete("/{opportunity_id}")
def delete_opportunity(
    opportunity_id: int,
    service: OpportunityService = Depends(),
    current_user: dict = Depends(get_current_user),
) -> ApiResponse:
    service.delete_opportunity(opportunity_id)
    return success(message="deleted")
