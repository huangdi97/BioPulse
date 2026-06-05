"""Research product matching API endpoints.

Matches research products against PI profiles (by research area)
or free-text method descriptions using keyword overlap scoring.
"""

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from cloud.app.research_database import get_research_db, log_research_audit
from cloud.app.services.product_matching_service import (
    match_products_by_method,
    match_products_for_pi,
)
from shared.auth import get_current_user
from shared.auth_scope import require_scope

router = APIRouter(
    prefix="/api/research/matching",
    tags=["科研线"],
    dependencies=[Depends(require_scope("research"))],
)


class PiMatchRequest(BaseModel):
    """Request body: match products for a specific PI."""

    pi_id: int


class MethodMatchRequest(BaseModel):
    """Request body: match products by a free-text method description."""

    method_description: str


@router.post("/for-pi")
def match_for_pi(
    body: PiMatchRequest,
    current_user: dict = Depends(get_current_user),
):
    """Return top 3 product recommendations for a given PI profile."""
    db = get_research_db()
    try:
        results = match_products_for_pi(body.pi_id, top_k=3, research_db=db)
        log_research_audit(
            event_type="create",
            entity_type="matching",
            entity_id=body.pi_id,
            new_value=str(results),
            operator=current_user.get("username", ""),
        )
        return {"code": 0, "data": results, "message": "success"}
    finally:
        db.close()


@router.post("/by-method")
def match_by_method(
    body: MethodMatchRequest,
    current_user: dict = Depends(get_current_user),
):
    """Return top 3 product recommendations matching a method description."""
    db = get_research_db()
    try:
        results = match_products_by_method(body.method_description, top_k=3, research_db=db)
        log_research_audit(
            event_type="create",
            entity_type="matching",
            entity_id=0,
            new_value=f"method={body.method_description[:100]}",
            operator=current_user.get("username", ""),
        )
        return {"code": 0, "data": results, "message": "success"}
    finally:
        db.close()
