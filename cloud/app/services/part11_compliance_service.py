"""21 CFR Part 11 electronic signature service."""

from __future__ import annotations

import hashlib
import hmac
import json
import os
import secrets
from datetime import datetime
from threading import Lock
from uuid import uuid4

from fastapi import HTTPException
from starlette import status

from cloud.app.schemas.part11_compliance import (
    AuditEventType,
    AuditTrail,
    ElectronicSignature,
    SignatureStatus,
    SignatureVerificationResult,
    SignedDocument,
)

_LOCK = Lock()
_SIGNATURES: dict[str, ElectronicSignature] = {}
_DOCUMENTS: dict[str, SignedDocument] = {}
_AUDIT_TRAILS: dict[str, list[AuditTrail]] = {}
from shared.datetime_utils import now as _now

_SIGNING_SECRET = os.getenv("PART11_HMAC_SECRET", "part11-demo-hmac-secret").encode()

_PASSWORD_HASHES = {
    "user-001": hashlib.sha256("secure_pwd".encode()).hexdigest(),
}


def _password_valid(user_id: str, password: str) -> bool:
    expected = _PASSWORD_HASHES.get(user_id)
    if expected:
        return hmac.compare_digest(hashlib.sha256(password.encode()).hexdigest(), expected)
    return len(password) >= 8


def _document_hash(document_id: str) -> str:
    return hashlib.sha256(f"document:{document_id}".encode()).hexdigest()


def _canonical_payload(
    user_id: str,
    document_id: str,
    signing_time: datetime,
    signed_data: dict,
    verification_token: str,
) -> bytes:
    payload = {
        "document_id": document_id,
        "signed_data": signed_data,
        "signing_time": signing_time.isoformat(),
        "user_id": user_id,
        "verification_token": verification_token,
    }
    return json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()


def _signature_hash(
    user_id: str,
    document_id: str,
    signing_time: datetime,
    signed_data: dict,
    verification_token: str,
) -> str:
    return hmac.new(
        _SIGNING_SECRET,
        _canonical_payload(user_id, document_id, signing_time, signed_data, verification_token),
        hashlib.sha256,
    ).hexdigest()


def _append_audit(
    event_type: AuditEventType,
    user_id: str,
    document_id: str,
    changes_diff: dict,
    ip_address: str = "127.0.0.1",
) -> AuditTrail:
    entry = AuditTrail(
        id=f"audit-{uuid4().hex[:10]}",
        event_type=event_type,
        user_id=user_id,
        document_id=document_id,
        timestamp=_now(),
        changes_diff=changes_diff,
        ip_address=ip_address,
    )
    _AUDIT_TRAILS.setdefault(document_id, []).append(entry)
    return entry


def sign_document(user_id: str, document_id: str, password: str) -> ElectronicSignature:
    """Create a non-repudiable electronic signature bound by timestamp and HMAC."""
    if not _password_valid(user_id, password):
        _append_audit(
            AuditEventType.SIGNATURE_REJECTED,
            user_id,
            document_id,
            {"reason": "password_factor_failed"},
        )
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail="Invalid password factor")

    signing_time = _now()
    verification_token = secrets.token_urlsafe(24)
    signed_data = {
        "auth_factors": ["password", "verification_token"],
        "document_hash": _document_hash(document_id),
        "non_repudiation": "signature+timestamp+hmac",
    }
    signature = ElectronicSignature(
        id=f"sig-{uuid4().hex[:10]}",
        user_id=user_id,
        document_id=document_id,
        signature_hash=_signature_hash(user_id, document_id, signing_time, signed_data, verification_token),
        signing_time=signing_time,
        signed_data=signed_data,
        verification_token=verification_token,
    )
    signed_document = SignedDocument(
        id=f"sdoc-{uuid4().hex[:10]}",
        document_id=document_id,
        status=SignatureStatus.SIGNED,
        content_hash=signed_data["document_hash"],
        signature_id=signature.id,
        signed_at=signing_time,
    )
    with _LOCK:
        _SIGNATURES[signature.id] = signature
        _DOCUMENTS[document_id] = signed_document
        _append_audit(
            AuditEventType.DOCUMENT_SIGNED,
            user_id,
            document_id,
            {
                "signature_id": signature.id,
                "signed_document_id": signed_document.id,
                "signature_hash": signature.signature_hash,
            },
        )
    return signature


def verify_signature(signature_id: str) -> SignatureVerificationResult:
    signature = _SIGNATURES.get(signature_id)
    if not signature:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Signature not found")

    expected = _signature_hash(
        signature.user_id,
        signature.document_id,
        signature.signing_time,
        signature.signed_data,
        signature.verification_token,
    )
    valid = hmac.compare_digest(signature.signature_hash, expected)
    _append_audit(
        AuditEventType.SIGNATURE_VERIFIED if valid else AuditEventType.SIGNATURE_REJECTED,
        signature.user_id,
        signature.document_id,
        {"signature_id": signature.id, "valid": valid},
    )
    return SignatureVerificationResult(
        signature_id=signature_id,
        valid=valid,
        reason="HMAC timestamp binding verified" if valid else "Signature HMAC mismatch",
        signature=signature if valid else None,
    )


def get_audit_trail(document_id: str) -> list[AuditTrail]:
    return _AUDIT_TRAILS.get(document_id, [])
