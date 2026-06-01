import time
from fastapi import FastAPI
from shared.request_id_middleware import RequestIDMiddleware
from shared.structured_logging import setup_logging

START_TIME = time.time()

setup_logging("management")

app = FastAPI(
    title="管理端 · Management Portal",
    version="1.0.0",
    description=(
        "管理端 / 后台管理系统提供三层视图：\n"
        "1. 总裁视图 – 全局概览、合规总览、团队排行、趋势报告\n"
        "2. 经理视图 – 团队统计、成员管理、团队合规、团队绩效\n"
        "3. 员工视图 – 个人资料、任务列表、个人合规、个人绩效、个人趋势"
    ),
)
app.add_middleware(RequestIDMiddleware)


@app.on_event("startup")
def startup():
    from management.app.database import init_cache_db

    init_cache_db()


@app.get("/health")
def health():
    return {
        "status": "ok",
        "uptime": int(time.time() - START_TIME),
        "service": "management",
    }


from management.app.president_router import router as president_router
from management.app.manager_router import router as manager_router
from management.app.employee_router import router as employee_router

app.include_router(president_router, prefix="/api/v1")
app.include_router(manager_router, prefix="/api/v1")
app.include_router(employee_router, prefix="/api/v1")
