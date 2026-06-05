from fastapi import APIRouter, Depends

from cloud.app.services.compliance_service import ComplianceService
from cloud.app.services.dashboard_service import DashboardService

router = APIRouter(prefix="/api/demo", tags=["demo"])


@router.get("/dashboard")
def dashboard_overview(service: DashboardService = Depends()):
    return service.get_overview()


@router.get("/dashboard/users")
def dashboard_users(service: DashboardService = Depends()):
    return service.get_user_stats()


@router.get("/dashboard/compliance")
def dashboard_compliance(service: DashboardService = Depends()):
    return service.get_compliance_stats()


@router.get("/compliance/summary")
def compliance_summary(service: ComplianceService = Depends()):
    return service.dashboard_summary()
