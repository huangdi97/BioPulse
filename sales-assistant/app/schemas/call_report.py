"""Call report three-stage data models."""

from pydantic import BaseModel, Field


class PreCallBrief(BaseModel):
    target_hcp: str = ""
    visit_goal: str = ""
    key_messages: list[str] = Field(default_factory=list)
    prep_materials: list[str] = Field(default_factory=list)
    hcp_background: str = ""


class VisitExecution(BaseModel):
    start_time: str = ""
    end_time: str = ""
    content_tags: list[str] = Field(default_factory=list)
    followup_tasks: list[str] = Field(default_factory=list)
    compliance_check: str = "pending"


class PostCallSummary(BaseModel):
    key_conclusions: list[str] = Field(default_factory=list)
    next_steps: list[str] = Field(default_factory=list)
    hcp_feedback: str = ""
    engagement_score: int = Field(default=0, ge=0, le=100)


class CallReport(BaseModel):
    visit_id: str
    precall: PreCallBrief
    execution: VisitExecution
    summary: PostCallSummary
