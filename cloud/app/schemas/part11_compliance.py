"""21 CFR Part 11 compliance schemas."""

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class AuditEventType(str, Enum):
    DOCUMENT_SIGNED = "document_signed"
    SIGNATURE_VERIFIED = "signature_verified"
    SIGNATURE_REJECTED = "signature_rejected"


class SignatureStatus(str, Enum):
    SIGNED = "signed"
    VERIFIED = "verified"
    INVALID = "invalid"


class ElectronicSignature(BaseModel):
    id: str
    user_id: str
    document_id: str
    signature_hash: str
    signing_time: datetime
    signed_data: dict[str, Any]
    verification_token: str


class AuditTrail(BaseModel):
    id: str
    event_type: AuditEventType
    user_id: str
    document_id: str
    timestamp: datetime
    changes_diff: dict[str, Any]
    ip_address: str = "127.0.0.1"


class SignedDocument(BaseModel):
    id: str
    document_id: str
    status: SignatureStatus
    content_hash: str
    signature_id: str
    signed_at: datetime


class SignDocumentRequest(BaseModel):
    user_id: str = Field(..., min_length=1)
    document_id: str = Field(..., min_length=1)
    password: str = Field(..., min_length=1)


class SignatureVerificationResult(BaseModel):
    signature_id: str
    valid: bool
    reason: str
    signature: ElectronicSignature | None = None
