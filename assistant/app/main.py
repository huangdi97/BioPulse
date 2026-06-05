from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from assistant.app.database import init_db
from assistant.app.hcp_router import router as hcp_router
from assistant.app.health_radar_router import router as health_radar_router
from assistant.app.health_router import router as health_router
from assistant.app.knowledge_router import router as knowledge_router
from assistant.app.knowledge_seed import seed_knowledge
from assistant.app.location_router import router as location_router
from assistant.app.media_router import router as media_router
from assistant.app.offline_router import router as offline_router
from assistant.app.qa_router import router as qa_router
from assistant.app.reminder_scheduler import start_scheduler
from assistant.app.surgery_router import router as surgery_router
from assistant.app.sync_router import router as sync_router
from assistant.app.task_router import router as task_router
from assistant.app.visit_router import router as visit_router
from assistant.app.voice_router import router as voice_router
from assistant.app.ws_router import router as ws_router
from shared.exception_handlers import register_exception_handlers
from shared.middleware import RequestIDMiddleware
from shared.rate_limiter import RateLimiterMiddleware
from shared.structured_logging import setup_logging

app = FastAPI(title="Assistant Service", version="1.0.0")

setup_logging("assistant")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(RequestIDMiddleware)
app.add_middleware(RateLimiterMiddleware, default_rate=100, window=60)
register_exception_handlers(app)


@app.on_event("startup")
def on_startup() -> None:
    """Initialize database tables and seed data on application startup."""
    init_db()
    seed_knowledge()
    start_scheduler()


app.include_router(health_router)
app.include_router(hcp_router)
app.include_router(visit_router)
app.include_router(task_router)
app.include_router(qa_router)
app.include_router(health_radar_router)
app.include_router(surgery_router)
app.include_router(knowledge_router)
app.include_router(location_router)
app.include_router(ws_router)
app.include_router(sync_router)
app.include_router(voice_router)
app.include_router(media_router)
app.include_router(offline_router)
