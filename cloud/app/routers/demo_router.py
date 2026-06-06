"""演示仪表板路由：概览、用户统计、合规统计、拜访趋势等。"""

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


@router.get("/visit-trends")
def visit_trends(service: DashboardService = Depends()):
    return service.get_visit_trends()


@router.get("/team-ranks")
def team_ranks(service: DashboardService = Depends()):
    return service.get_team_ranks()


@router.get("/violations")
def violations(service: DashboardService = Depends()):
    return service.get_violations()


@router.get("/research-kpis")
def research_kpis(service: DashboardService = Depends()):
    return service.get_research_kpis()


@router.get("/pi-sources")
def pi_sources(service: DashboardService = Depends()):
    return service.get_pi_sources()


@router.get("/product-match-stats")
def product_match_stats(service: DashboardService = Depends()):
    return service.get_product_match_stats()
