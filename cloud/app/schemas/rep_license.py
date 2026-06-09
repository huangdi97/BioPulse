"""Medical representative license schemas."""

from enum import Enum

from pydantic import BaseModel, Field


class LicenseStatus(str, Enum):
    ACTIVE = "active"
    EXPIRING = "expiring"
    EXPIRED = "expired"
    INVALID = "invalid"


class RepLicense(BaseModel):
    id: str
    rep_id: str
    nmpa_registration_no: str
    name: str
    company: str
    status: LicenseStatus
    valid_from: str
    valid_until: str
    verification_date: str


class VerificationResult(BaseModel):
    registration_no: str
    valid: bool
    status: LicenseStatus
    rep_license: RepLicense | None = None
    message: str
    evidence: str = "nmpa-registration-check"


class LicenseVerifyRequest(BaseModel):
    registration_no: str = Field(..., min_length=4)
    rep_id: str | None = None
    name: str | None = None
    company: str | None = None
