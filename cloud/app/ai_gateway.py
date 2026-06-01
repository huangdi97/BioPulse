from typing import Any

from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel, Field

from shared.auth import get_current_user
from shared.base import ApiResponse, success
from cloud.app.services.ai_gateway_service import AiGatewayService

router = APIRouter(prefix="/ai", tags=["AI Gateway"])


class ChatRequest(BaseModel):
    messages: list[dict[str, str]]
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    max_tokens: int = Field(default=2048, ge=1, le=8192)


class ChatResponse(BaseModel):
    reply: str
    usage: dict[str, Any]


@router.post("/chat", response_model=ApiResponse[ChatResponse])
def chat(
    request: Request,
    body: ChatRequest,
    current_user: dict = Depends(get_current_user),
    service: AiGatewayService = Depends(),
) -> Any:
    result = service.chat(body.messages, body.temperature, body.max_tokens)
    return success(ChatResponse(reply=result["reply"], usage=result["usage"]))
