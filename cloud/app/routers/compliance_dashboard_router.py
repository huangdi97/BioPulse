from fastapi import APIRouter, Depends

from cloud.app.services.compliance_service import ComplianceService
from shared.auth import get_current_user

router = APIRouter(prefix="/api/compliance/dashboard", tags=["合规"])


@router.get("/summary")
def dashboard_summary(
    current_user: dict = Depends(get_current_user),
    service: ComplianceService = Depends(),
):
    return service.dashboard_summary()


@router.get("/reps/{rep_id}")
def rep_violations(
    rep_id: int,
    current_user: dict = Depends(get_current_user),
    service: ComplianceService = Depends(),
):
    return service.rep_violations(rep_id)
