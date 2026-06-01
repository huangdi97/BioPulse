from typing import Any, Optional

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from starlette import status

from cloud.app.services.interaction_service import InteractionService
from shared.auth_scope import require_scope
from shared.base import success

router = APIRouter(prefix="", tags=["interactions"])


class InteractionCreate(BaseModel):
    type: str = "visit"
    summary: str = ""
    outcome: str = ""
    conducted_by: Optional[int] = None
    conducted_at: Optional[str] = None


class InteractionUpdate(BaseModel):
    type: Optional[str] = None
    summary: Optional[str] = None
    outcome: Optional[str] = None
    conducted_by: Optional[int] = None
    conducted_at: Optional[str] = None


@router.post(
    "/customers/{customer_id}/interactions", status_code=status.HTTP_201_CREATED
)
def create_interaction(
    customer_id: int,
    body: InteractionCreate,
    current_user: dict = Depends(require_scope("visit")),
    service: InteractionService = Depends(),
) -> Any:
    user_id = int(current_user["sub"])
    result = service.create_interaction(
        customer_id=customer_id,
        type_=body.type,
        summary=body.summary,
        outcome=body.outcome,
        conducted_by=body.conducted_by,
        conducted_at=body.conducted_at,
        user_id=user_id,
    )
    return success(data=result)


@router.get("/customers/{customer_id}/interactions")
def list_customer_interactions(
    customer_id: int,
    current_user: dict = Depends(require_scope("visit")),
    service: InteractionService = Depends(),
) -> Any:
    rows = service.list_customer_interactions(customer_id)
    return success(data=rows)


@router.get("/interactions")
def list_interactions(
    type: str = Query(None),
    conducted_by: int = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: dict = Depends(require_scope("visit")),
    service: InteractionService = Depends(),
) -> Any:
    result = service.list_interactions(
        type_=type,
        conducted_by=conducted_by,
        page=page,
        page_size=page_size,
    )
    return success(data=result)


@router.patch("/interactions/{interaction_id}")
def update_interaction(
    interaction_id: int,
    body: InteractionUpdate,
    current_user: dict = Depends(require_scope("visit")),
    service: InteractionService = Depends(),
) -> Any:
    updates = {
        k: v
        for k, v in {
            "type": body.type,
            "summary": body.summary,
            "outcome": body.outcome,
            "conducted_by": body.conducted_by,
            "conducted_at": body.conducted_at,
        }.items()
        if v is not None
    }
    result = service.update_interaction(interaction_id, updates)
    return success(data=result)


@router.delete("/interactions/{interaction_id}")
def delete_interaction(
    interaction_id: int,
    current_user: dict = Depends(require_scope("visit")),
    service: InteractionService = Depends(),
) -> Any:
    service.delete_interaction(interaction_id)
    return success()
