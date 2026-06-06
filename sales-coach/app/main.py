"""销售教练服务入口，创建FastAPI应用并注册路由和中间件。"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from sales_coach.app.assessment_router import router as assessment_router
from sales_coach.app.database import init_db
from sales_coach.app.digital_human_router import router as digital_human_router
from sales_coach.app.health_router import router as health_router
from sales_coach.app.module_router import router as module_router
from sales_coach.app.reflection_router import router as reflection_router
from sales_coach.app.scenario_router import router as scenario_router
from sales_coach.app.session_router import router as session_router
from sales_coach.app.stats_router import router as stats_router
from sales_coach.app.stats_router import stats_root_router
from shared.app_settings import settings
from shared.exception_handlers import register_exception_handlers
from shared.middleware import RequestIDMiddleware
from shared.rate_limiter import RateLimiterMiddleware
from shared.structured_logging import setup_logging

app = FastAPI(title="Sales Coach Service", version=settings.version)

setup_logging("sales_coach")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(RequestIDMiddleware)
app.add_middleware(RateLimiterMiddleware, default_rate=100, window=60)
register_exception_handlers(app)


@app.on_event("startup")
def on_startup() -> None:
    """Initialize database tables on application startup."""
    init_db()


app.include_router(health_router)
app.include_router(module_router)
app.include_router(session_router)
app.include_router(scenario_router)
app.include_router(stats_router)
app.include_router(stats_root_router)
app.include_router(assessment_router)
app.include_router(reflection_router)
app.include_router(digital_human_router)
