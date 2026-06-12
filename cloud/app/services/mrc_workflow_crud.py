"""MRC workflow CRUD operations."""

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

from .mrc_workflow_state import (
    _COMPLIANCE_APPROVALS,
    _COMPLIANCE_SUBMISSIONS,
    _DISTRIBUTIONS,
    _MATERIALS,
    _METRICS,
    _MRC_REVIEWS,
    _get_material,
    _latest_compliance_approved,
    _latest_mrc_approved,
    _new_id,
    _require_status,
    _set_status,
)


def create_material(body: MaterialCreate) -> MRCMaterial:
    material = MRCMaterial(id=_new_id("mrc"), title=body.title, content_type=body.content_type, content=body.content)
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
    review = MRCReview(id=_new_id("mrc-review"), material_id=material_id, reviewer=body.reviewer, approved=body.approved, comments=body.comments)
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
        id=_new_id("compliance"), material_id=material_id, approver=body.approver, approved=body.approved, comments=body.comments
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
