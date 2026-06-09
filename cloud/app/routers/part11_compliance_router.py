"""21 CFR Part 11 compliance APIs."""

from fastapi import APIRouter

from cloud.app.schemas.part11_compliance import (
    AuditTrail,
    ElectronicSignature,
    SignatureVerificationResult,
    SignDocumentRequest,
)
from cloud.app.services.part11_compliance_service import (
    get_audit_trail,
    sign_document,
    verify_signature,
)

router = APIRouter(prefix="/api/part11", tags=["21 CFR Part 11"])


@router.post("/sign", response_model=ElectronicSignature, tags=["21 CFR Part 11"])
def part11_sign(body: SignDocumentRequest) -> ElectronicSignature:
    return sign_document(body.user_id, body.document_id, body.password)


@router.get("/audit/{document_id}", response_model=list[AuditTrail], tags=["21 CFR Part 11"])
def part11_audit(document_id: str) -> list[AuditTrail]:
    return get_audit_trail(document_id)


@router.get("/verify/{signature_id}", response_model=SignatureVerificationResult, tags=["21 CFR Part 11"])
def part11_verify(signature_id: str) -> SignatureVerificationResult:
    return verify_signature(signature_id)
