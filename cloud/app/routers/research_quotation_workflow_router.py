"""Compatibility re-export for cloud.app.routers.research_quotation_workflow_router."""

from cloud.app.routers.cloud_research_quotation_router import RejectRequest
from cloud.app.routers.cloud_research_quotation_router import quotation_workflow_router as router

__all__ = ["router", "RejectRequest"]
