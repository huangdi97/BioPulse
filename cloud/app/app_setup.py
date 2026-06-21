"""FastAPI 路由注册与启动事件。"""

from importlib import import_module
from pkgutil import iter_modules

from fastapi import APIRouter, FastAPI

from cloud.app import routers as router_package
from cloud.app.agent_database import init_agent_db
from cloud.app.database import init_db
from cloud.app.research_database import init_research_db as init_research
from cloud.app.routers.cloud_opportunity_router import opportunity_v2_router
from cloud.app.services.tenant_isolation_service import router as tenant_isolation_router
from cloud.app.soap_route import router as soap_decision_router

ROUTER_MODULE_BLACKLIST: frozenset[str] = frozenset()
MANUAL_ROUTERS = (opportunity_v2_router, soap_decision_router, tenant_isolation_router)


def _iter_auto_routers():
    modules = sorted(iter_modules(router_package.__path__), key=lambda module: module.name)
    for module in modules:
        if module.ispkg or module.name in ROUTER_MODULE_BLACKLIST:
            continue
        router = getattr(import_module(f"{router_package.__name__}.{module.name}"), "router", None)
        if isinstance(router, APIRouter):
            yield router


def register_routers(app: FastAPI) -> None:
    for router in (*_iter_auto_routers(), *MANUAL_ROUTERS):
        app.include_router(router)


def register_startup_events(app: FastAPI) -> None:
    @app.on_event("startup")
    def startup():
        init_agent_db()
        init_db()
        init_research()
        from cloud.app.agent_runtime.agent_registry import AgentRegistry

        AgentRegistry.load()

        from cloud.app.agent_runtime.namespace_event_bus import get_namespace_event_bus
        from cloud.app.agent_runtime.shared_state import get_shared_state
        from cloud.app.agent_runtime.world_model import get_world_model

        get_namespace_event_bus().start(get_shared_state())
        get_world_model().start()
