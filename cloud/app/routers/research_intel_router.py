"""Consolidated research intel router module — aggregates all sub-routers."""

from fastapi import APIRouter

from cloud.app.routers.research_audit_router import audit_router
from cloud.app.routers.research_enforcer_router import enforcer_router
from cloud.app.routers.research_export_router import export_router
from cloud.app.routers.research_route_router import route_router
from cloud.app.routers.research_trajectory_router import trajectory_router

router = APIRouter()

router.include_router(audit_router)
router.include_router(enforcer_router)
router.include_router(export_router)
router.include_router(route_router)
router.include_router(trajectory_router)

__all__ = [
    "router",
    "audit_router",
    "enforcer_router",
    "export_router",
    "route_router",
    "trajectory_router",
]
