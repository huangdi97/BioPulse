"""Agent Trace 路由聚合 — 注册 trace / context / failure 三个子路由。"""

from fastapi import APIRouter

from cloud.app.agent_runtime.trace_context_router import router as trace_context_router
from cloud.app.agent_runtime.trace_failure_router import router as trace_failure_router
from cloud.app.agent_runtime.trace_router import router as trace_router

router = APIRouter()
router.include_router(trace_router)
router.include_router(trace_context_router)
router.include_router(trace_failure_router)
