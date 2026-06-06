"""HCP 沙箱路由，挂载管理与仿真子路由。"""

from fastapi import APIRouter

from cloud.app.sandbox_manager import manager_router
from cloud.app.sandbox_simulator import simulator_router

router = APIRouter(prefix="/hcp-sandbox", tags=["HCP Sandbox"])
router.include_router(manager_router)
router.include_router(simulator_router)
