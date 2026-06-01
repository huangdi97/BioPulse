from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from starlette import status

from cloud.app.services.quotations_service import (
    QUOTATION_TEMPLATES,
    generate_quotation,
)
from shared.auth import get_current_user
from shared.auth_scope import require_scope

router = APIRouter(
    prefix="/api/research/quotations",
    tags=["科研线"],
    dependencies=[Depends(require_scope("research"))],
)


class GenerateQuotationRequest(BaseModel):
    template_id: str
    items: list[dict]
    customer_info: Optional[dict] = None


@router.get("/templates")
def list_templates(
    current_user: dict = Depends(get_current_user),
):
    return {
        "code": 0,
        "data": list(QUOTATION_TEMPLATES.values()),
        "message": "success",
    }


@router.post("/generate")
def create_quotation(
    body: GenerateQuotationRequest,
    current_user: dict = Depends(get_current_user),
):
    try:
        result = generate_quotation(body.template_id, body.items)
        if body.customer_info:
            result["customer_info"] = body.customer_info
        return {"code": 0, "data": result, "message": "success"}
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
