"""MRC content workflow schemas."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Literal

from pydantic import BaseModel, Field

ContentType = Literal["slide", "script", "social", "video"]
MaterialStatus = Literal["draft", "mrc_review", "compliance_approve", "published", "rejected"]


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class MRCMaterial(BaseModel):
    id: str
    title: str
    content_type: ContentType
    content: str
    status: MaterialStatus = "draft"
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)


class MRCReview(BaseModel):
    id: str
    material_id: str
    reviewer: str
    approved: bool
    comments: str = ""
    reviewed_at: datetime = Field(default_factory=utc_now)


class ComplianceApproval(BaseModel):
    id: str
    material_id: str
    approver: str
    approved: bool
    comments: str = ""
    approved_at: datetime = Field(default_factory=utc_now)


class DistributionChannel(BaseModel):
    id: str
    material_id: str
    channel: str
    status: Literal["queued", "sent"] = "sent"
    distributed_at: datetime = Field(default_factory=utc_now)


class EffectivenessMetrics(BaseModel):
    material_id: str
    impressions: int = 0
    clicks: int = 0
    conversions: int = 0
    engagement_rate: float = 0.0
    channel_count: int = 0
    tracked_at: datetime = Field(default_factory=utc_now)


class MaterialCreate(BaseModel):
    title: str
    content_type: ContentType
    content: str


class MRCDecisionRequest(BaseModel):
    approved: bool = True
    reviewer: str = "mrc-reviewer"
    comments: str = ""


class ComplianceApproveRequest(BaseModel):
    approved: bool = True
    approver: str = "compliance-officer"
    comments: str = ""


class DistributionRequest(BaseModel):
    channels: list[str] = Field(default_factory=lambda: ["sales_assistant"])


class MRCWorkflowDetail(BaseModel):
    material: MRCMaterial
    mrc_reviews: list[MRCReview] = Field(default_factory=list)
    compliance_approvals: list[ComplianceApproval] = Field(default_factory=list)
    distribution_channels: list[DistributionChannel] = Field(default_factory=list)
    effectiveness: EffectivenessMetrics | None = None
