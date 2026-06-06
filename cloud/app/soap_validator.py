"""SOAP 数据校验模型。"""

from typing import Optional

from pydantic import BaseModel


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
