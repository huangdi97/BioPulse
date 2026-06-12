"""MRC workflow state machine — state transitions and validations."""

from uuid import uuid4

from fastapi import HTTPException
from starlette import status

from cloud.app.schemas.mrc_workflow import ComplianceApproval, DistributionChannel, EffectivenessMetrics, MRCMaterial, MRCReview, utc_now

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
        raise HTTPException(status.HTTP_409_CONFLICT, detail=f"{action} requires status '{expected}', current status is '{material.status}'")


def _latest_mrc_approved(material_id: str) -> bool:
    reviews = _MRC_REVIEWS.get(material_id, [])
    return bool(reviews and reviews[-1].approved)


def _latest_compliance_approved(material_id: str) -> bool:
    approvals = _COMPLIANCE_APPROVALS.get(material_id, [])
    return bool(approvals and approvals[-1].approved)
