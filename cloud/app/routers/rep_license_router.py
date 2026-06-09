"""Medical representative license APIs."""

from fastapi import APIRouter, HTTPException, Query
from starlette import status

from cloud.app.schemas.rep_license import LicenseVerifyRequest, RepLicense, VerificationResult
from cloud.app.services.rep_license_service import check_expiry, get_rep_license, verify_license

router = APIRouter(prefix="/api/rep/license", tags=["医药代表备案"])


@router.post("/verify", response_model=VerificationResult, tags=["医药代表备案"])
def rep_license_verify(body: LicenseVerifyRequest) -> VerificationResult:
    return verify_license(body.registration_no)


@router.get("/expiring", response_model=list[RepLicense], tags=["医药代表备案"])
def rep_license_expiring(days: int = Query(60, ge=1, le=365)) -> list[RepLicense]:
    return check_expiry(days=days)


@router.get("/{rep_id}", response_model=RepLicense, tags=["医药代表备案"])
def rep_license_get(rep_id: str) -> RepLicense:
    license_ = get_rep_license(rep_id)
    if not license_:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Representative license not found")
    return license_
