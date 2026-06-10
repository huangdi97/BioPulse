"""Compatibility re-export for cloud.app.routers.research_pi_router."""

from cloud.app.routers.research_matching_router import PiCreate
from cloud.app.routers.research_matching_router import pi_router as router

__all__ = ["router", "PiCreate"]
