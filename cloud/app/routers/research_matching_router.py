"""Research product matching API endpoints.

Matches research products against PI profiles (by research area)
or free-text method descriptions using keyword overlap scoring.
"""

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from shared.auth import get_current_user
from shared.auth_scope import require_scope
from cloud.app.research_database import get_research_db
from cloud.app.services.product_matching_service import (
    match_products_for_pi,
    match_products_by_method,
)

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
    """Return top 3 product recommendations for a given PI profile.

    Matching is based on keyword overlap between the PI's research areas
    and product keywords/name tokens.
    """
    db = get_research_db()
    try:
        results = match_products_for_pi(body.pi_id, top_k=3, research_db=db)
        return {"code": 0, "data": results, "message": "success"}
    finally:
        db.close()


@router.post("/by-method")
def match_by_method(
    body: MethodMatchRequest,
    current_user: dict = Depends(get_current_user),
):
    """Return top 3 product recommendations matching a method description.

    The description is tokenized (with English stop-word filtering) and
    matched against product keywords and name tokens.
    """
    db = get_research_db()
    try:
        results = match_products_by_method(
            body.method_description, top_k=3, research_db=db
        )
        return {"code": 0, "data": results, "message": "success"}
    finally:
        db.close()
