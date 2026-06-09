"""MRC content workflow state machine."""

from __future__ import annotations

from uuid import uuid4

from fastapi import HTTPException
from starlette import status

from cloud.app.schemas.mrc_workflow import (
    ComplianceApproval,
    ComplianceApproveRequest,
    DistributionChannel,
    DistributionRequest,
    EffectivenessMetrics,
    MaterialCreate,
    MRCDecisionRequest,
    MRCMaterial,
    MRCReview,
    MRCWorkflowDetail,
    utc_now,
)

_MATERIALS: dict[str, MRCMaterial] = {}
_MRC_REVIEWS: dict[str, list[MRCReview]] = {}
_COMPLIANCE_SUBMISSIONS: dict[str, object] = {}
_COMPLIANCE_APPROVALS: dict[str, list[ComplianceApproval]] = {}
_DISTRIBUTIONS: dict[str, list[DistributionChannel]] = {}
_METRICS: dict[str, EffectivenessMetrics] = {}


def _new_id(prefix: str) -> str:
    return f"{prefix}-{uuid4().hex[:8]}"


def _get_material(material_id: str) -> MRCMaterial:
    material = _MATERIALS.get(material_id)
    if material is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="MRC material not found")
    return material


def _set_status(material: MRCMaterial, next_status: str) -> MRCMaterial:
    material.status = next_status
    material.updated_at = utc_now()
    _MATERIALS[material.id] = material
    return material


def _require_status(material: MRCMaterial, expected: str, action: str) -> None:
    if material.status != expected:
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            detail=f"{action} requires status '{expected}', current status is '{material.status}'",
        )


def _latest_mrc_approved(material_id: str) -> bool:
    reviews = _MRC_REVIEWS.get(material_id, [])
    return bool(reviews and reviews[-1].approved)


def _latest_compliance_approved(material_id: str) -> bool:
    approvals = _COMPLIANCE_APPROVALS.get(material_id, [])
    return bool(approvals and approvals[-1].approved)


def create_material(body: MaterialCreate) -> MRCMaterial:
    material = MRCMaterial(
        id=_new_id("mrc"),
        title=body.title,
        content_type=body.content_type,
        content=body.content,
    )
    _MATERIALS[material.id] = material
    _MRC_REVIEWS[material.id] = []
    _COMPLIANCE_APPROVALS[material.id] = []
    _DISTRIBUTIONS[material.id] = []
    return material


def submit_mrc(material_id: str) -> MRCMaterial:
    material = _get_material(material_id)
    _require_status(material, "draft", "submit_mrc")
    return _set_status(material, "mrc_review")


def mrc_decision(material_id: str, body: MRCDecisionRequest) -> MRCWorkflowDetail:
    material = _get_material(material_id)
    _require_status(material, "mrc_review", "mrc_decision")
    review = MRCReview(
        id=_new_id("mrc-review"),
        material_id=material_id,
        reviewer=body.reviewer,
        approved=body.approved,
        comments=body.comments,
    )
    _MRC_REVIEWS.setdefault(material_id, []).append(review)
    _set_status(material, "compliance_approve" if body.approved else "rejected")
    return get_workflow_detail(material_id)


def submit_compliance(material_id: str) -> MRCMaterial:
    material = _get_material(material_id)
    _require_status(material, "compliance_approve", "submit_compliance")
    if not _latest_mrc_approved(material_id):
        raise HTTPException(status.HTTP_409_CONFLICT, detail="MRC approval is required before compliance submission")
    _COMPLIANCE_SUBMISSIONS[material_id] = utc_now()
    material.updated_at = utc_now()
    return material


def approve(material_id: str, body: ComplianceApproveRequest) -> MRCWorkflowDetail:
    material = _get_material(material_id)
    _require_status(material, "compliance_approve", "approve")
    if material_id not in _COMPLIANCE_SUBMISSIONS:
        raise HTTPException(status.HTTP_409_CONFLICT, detail="submit_compliance must run before approve")
    approval = ComplianceApproval(
        id=_new_id("compliance"),
        material_id=material_id,
        approver=body.approver,
        approved=body.approved,
        comments=body.comments,
    )
    _COMPLIANCE_APPROVALS.setdefault(material_id, []).append(approval)
    _set_status(material, "compliance_approve" if body.approved else "rejected")
    return get_workflow_detail(material_id)


def distribute(material_id: str, body: DistributionRequest) -> MRCWorkflowDetail:
    material = _get_material(material_id)
    _require_status(material, "compliance_approve", "distribute")
    if not _latest_compliance_approved(material_id):
        raise HTTPException(status.HTTP_409_CONFLICT, detail="Compliance approval is required before distribution")
    channels = [channel.strip() for channel in body.channels if channel.strip()]
    if not channels:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, detail="At least one distribution channel is required")
    _DISTRIBUTIONS[material_id] = [DistributionChannel(id=_new_id("channel"), material_id=material_id, channel=channel) for channel in channels]
    _set_status(material, "published")
    return get_workflow_detail(material_id)


def track(material_id: str) -> EffectivenessMetrics:
    material = _get_material(material_id)
    _require_status(material, "published", "track")
    channels = _DISTRIBUTIONS.get(material_id, [])
    impressions = max(120 * len(channels), 120)
    clicks = round(impressions * 0.18)
    conversions = round(clicks * 0.12)
    metrics = EffectivenessMetrics(
        material_id=material_id,
        impressions=impressions,
        clicks=clicks,
        conversions=conversions,
        engagement_rate=round(clicks / impressions, 4) if impressions else 0.0,
        channel_count=len(channels),
    )
    _METRICS[material_id] = metrics
    return metrics


def get_workflow_detail(material_id: str) -> MRCWorkflowDetail:
    material = _get_material(material_id)
    return MRCWorkflowDetail(
        material=material,
        mrc_reviews=_MRC_REVIEWS.get(material_id, []),
        compliance_approvals=_COMPLIANCE_APPROVALS.get(material_id, []),
        distribution_channels=_DISTRIBUTIONS.get(material_id, []),
        effectiveness=_METRICS.get(material_id),
    )
