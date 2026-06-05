from fastapi import APIRouter

from cloud.app.analysis_handler import analysis_router
from cloud.app.reporting_handler import reporting_router

router = APIRouter(prefix="/decision-intel", tags=["Decision Intelligence"])
router.include_router(analysis_router)
router.include_router(reporting_router)
