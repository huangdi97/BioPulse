"""Medical representative license verification service."""

from datetime import datetime, timedelta
from threading import Lock
from uuid import uuid4

from cloud.app.schemas.rep_license import (
    LicenseStatus,
    LicenseVerifyRequest,
    RepLicense,
    VerificationResult,
)

_LOCK = Lock()
_LICENSES: dict[str, RepLicense] = {
    "rep-001": RepLicense(
        id="lic-rep-001",
        rep_id="rep-001",
        nmpa_registration_no="NMPA20250001",
        name="王强",
        company="云端医药有限公司",
        status=LicenseStatus.ACTIVE,
        valid_from="2025-01-01",
        valid_until="2027-12-31",
        verification_date="2026-06-01",
    ),
    "rep-002": RepLicense(
        id="lic-rep-002",
        rep_id="rep-002",
        nmpa_registration_no="NMPA20250002",
        name="陈静",
        company="云端医药有限公司",
        status=LicenseStatus.EXPIRING,
        valid_from="2024-07-01",
        valid_until="2026-07-10",
        verification_date="2026-06-01",
    ),
}


def _today() -> datetime:
    return datetime.now()


def _status(valid_until: str, registration_no: str) -> LicenseStatus:
    if not registration_no.startswith("NMPA"):
        return LicenseStatus.INVALID
    expiry = datetime.fromisoformat(valid_until)
    if expiry.date() < _today().date():
        return LicenseStatus.EXPIRED
    if expiry.date() <= (_today() + timedelta(days=60)).date():
        return LicenseStatus.EXPIRING
    return LicenseStatus.ACTIVE


def create_rep(rep_data: LicenseVerifyRequest) -> RepLicense:
    """Create a representative and verify the registration number automatically."""
    with _LOCK:
        existing = next(
            (license_ for license_ in _LICENSES.values() if license_.nmpa_registration_no == rep_data.registration_no),
            None,
        )
        if existing:
            return existing

        rep_id = rep_data.rep_id or f"rep-{uuid4().hex[:6]}"
        valid_until = "2027-12-31" if rep_data.registration_no.startswith("NMPA") else _today().date().isoformat()
        license_ = RepLicense(
            id=f"lic-{uuid4().hex[:8]}",
            rep_id=rep_id,
            nmpa_registration_no=rep_data.registration_no,
            name=rep_data.name or "待完善代表",
            company=rep_data.company or "待完善公司",
            status=_status(valid_until, rep_data.registration_no),
            valid_from=_today().date().isoformat(),
            valid_until=valid_until,
            verification_date=_today().date().isoformat(),
        )
        _LICENSES[rep_id] = license_
        return license_


def verify_license(no: str) -> VerificationResult:
    request = LicenseVerifyRequest(registration_no=no)
    license_ = create_rep(request)
    valid = license_.status in {LicenseStatus.ACTIVE, LicenseStatus.EXPIRING}
    return VerificationResult(
        registration_no=no,
        valid=valid,
        status=license_.status,
        rep_license=license_ if valid else None,
        message="备案号核验通过" if valid else "备案号无效或已过期",
    )


def get_rep_license(rep_id: str) -> RepLicense | None:
    return _LICENSES.get(rep_id)


def check_expiry(days: int = 60) -> list[RepLicense]:
    threshold = (_today() + timedelta(days=days)).date()
    expiring: list[RepLicense] = []
    for license_ in _LICENSES.values():
        expiry = datetime.fromisoformat(license_.valid_until).date()
        if _today().date() <= expiry <= threshold:
            expiring.append(license_.model_copy(update={"status": LicenseStatus.EXPIRING}))
    return expiring
