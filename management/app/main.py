"""管理端主应用入口。"""

import os

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from fastapi.staticfiles import StaticFiles

from shared.app_settings import settings
from shared.exception_handlers import register_exception_handlers
from shared.middleware import RequestIDMiddleware
from shared.structured_logging import setup_logging

setup_logging("management")

app = FastAPI(title=settings.app_name, version=settings.version)

app.add_middleware(RequestIDMiddleware)
register_exception_handlers(app)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def startup():
    from management.app.database import init_db

    init_db()


from management.app.dashboard_router import router as dashboard_router
from management.app.employee_router import router as employee_router
from management.app.health_router import router as health_router
from management.app.manager_router import router as manager_router
from management.app.president_router import router as president_router

app.include_router(health_router)
app.include_router(dashboard_router)
app.include_router(employee_router)
app.include_router(manager_router)
app.include_router(president_router)

STATIC_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")
if os.path.isdir(STATIC_DIR):
    app.mount(
        "/assets",
        StaticFiles(directory=os.path.join(STATIC_DIR, "assets")),
        name="assets",
    )

    @app.api_route("/{path_name:path}", methods=["GET"])
    async def catch_all(path_name: str):
        if path_name.startswith("api/") or path_name.startswith("assets/"):
            raise HTTPException(status_code=404)
        return Response(
            content=open(os.path.join(STATIC_DIR, "index.html"), "rb").read(),
            media_type="text/html",
        )
