from typing import Any

from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel

from assistant.app.services.qa_service import QaService
from shared.auth import get_current_user
from shared.base import ApiResponse, success

router = APIRouter(prefix="", tags=["Medical Q&A"])


class QaRequest(BaseModel):
    """Medical Q&A request body."""

    question: str
    context: str | None = None


class QaData(BaseModel):
    """Medical Q&A response data."""

    question: str
    answer: str
    sources: list[str]


@router.post("/qa", response_model=ApiResponse[QaData])
def qa(
    request: Request,
    body: QaRequest,
    service: QaService = Depends(),
    current_user: dict = Depends(get_current_user),
) -> Any:
    """Answer a medical question using AI as a senior clinical pharmacist."""
    auth_header = request.headers.get("Authorization", "")
    data = service.answer_question(body, auth_header)
    return success(data=QaData(**data))
