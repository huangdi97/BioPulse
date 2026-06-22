"""Consolidated research intel router module — aggregates all sub-routers."""

from fastapi import APIRouter

from cloud.app.routers.cloud_research_quotation_router import RejectRequest, quotation_workflow_router
from cloud.app.routers.research_matching_router import PiCreate, pi_router, product_router
from cloud.app.routers.research_misc_router import (
    audit_router,
    enforcer_router,
    export_router,
    route_router,
)
from cloud.app.routers.research_trajectory_router import trajectory_router

router = APIRouter()

router.include_router(audit_router)
router.include_router(enforcer_router)
router.include_router(export_router)
router.include_router(product_router)
router.include_router(pi_router)
router.include_router(quotation_workflow_router)
router.include_router(route_router)
router.include_router(trajectory_router)

__all__ = [
    "router",
    "audit_router",
    "enforcer_router",
    "export_router",
    "PiCreate",
    "pi_router",
    "product_router",
    "quotation_workflow_router",
    "RejectRequest",
    "route_router",
    "trajectory_router",
]
