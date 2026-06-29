"""Config module — loads .env based on ENV environment variable."""

import logging
import os

from pydantic_settings import BaseSettings, SettingsConfigDict

logger = logging.getLogger(__name__)


def get_biopulse_mode() -> str:
    return os.environ.get("BIOPULSE_MODE", "single")


def is_multi_tenant() -> bool:
    return get_biopulse_mode().lower() == "multi"


def _resolve_env_file() -> str:
    env = os.environ.get("ENV", "development").lower()
    if env == "production":
        candidates = [".env.prod", "config/.env.prod", ".env"]
    else:
        candidates = [".env.dev", "config/.env.dev", ".env"]
    for path in candidates:
        if os.path.isfile(path):
            logger.info("Config: loading %s (ENV=%s)", path, env)
            return path
    logger.warning("Config: no env file found for ENV=%s, falling back to .env", env)
    return ".env"


class Config(BaseSettings):
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7

    database_url: str = "sqlite:///./data/cloud.db"
    assistant_database_url: str = "sqlite:///./data/assistant.db"
    opportunity_database_url: str = "sqlite:///./data/opportunity.db"
    sales_assistant_database_url: str = "sqlite:///./data/sales_assistant.db"
    sales_coach_database_url: str = "sqlite:///./data/sales_coach.db"
    db_pool_size: int = 10
    db_max_overflow: int = 20

    host: str = "0.0.0.0"

    digital_human_provider: str = "internal"

    cloud_api_url: str = "http://localhost:8000"

    ai_chat_url: str = "http://localhost:8000/ai/chat"
    ai_gateway_timeout: int = 120

    deepseek_api_key: str = ""
    deepseek_api_url: str = "https://api.deepseek.com/v1/chat/completions"
    deepseek_model: str = "deepseek-v4-flash"

    openrouter_api_key: str = ""
    openrouter_api_url: str = "https://openrouter.ai/api/v1/chat/completions"
    openrouter_model: str = "openrouter/anthropic/claude-sonnet-4"

    openai_api_key: str = ""
    openai_api_url: str = "https://api.openai.com/v1/chat/completions"
    openai_model: str = "openai/gpt-4o-mini"
    secret_key: str = ""  # PRIMARY: SECRET_KEY from env
    jwt_secret_key: str = ""  # FALLBACK: JWT_SECRET_KEY from env (legacy compat)

    @property
    def effective_secret_key(self) -> str:
        if not self.secret_key and not self.jwt_secret_key:
            logger.warning("⚠️ 未配置 SECRET_KEY/JWT_SECRET_KEY，JWT 签名不稳定")
        return self.secret_key or self.jwt_secret_key or os.urandom(32).hex()

    cors_origins: str = "*"
    cloud_db_path: str = "data/cloud.db"
    assistant_db_path: str = "data/assistant.db"
    opportunity_db_path: str = "data/opportunity.db"
    sales_assistant_db_path: str = "data/sales_assistant.db"
    sales_coach_db_path: str = "data/sales_coach.db"
    cloud_port: int = 8000
    opportunity_port: int = 8002
    admin_port: int = 8012
    assistant_port: int = 8003
    sales_assistant_port: int = 8004
    sales_coach_port: int = 8001
    pharma_intel_port: int = 8006
    market_access_port: int = 8007
    clinical_ops_port: int = 8010
    patient_engage_port: int = 8011

    ai_routing_mode: str = "cloud"
    ai_routing_enabled: bool = False
    ai_local_endpoint: str = ""
    ai_local_model: str = ""
    ai_cloud_agent_enabled: bool = True
    ai_complexity_threshold: int = 2000

    redis_url: str = ""

    pareto_objectives: dict = {
        "success_rate": {"direction": "maximize", "weight": 1.0},
        "avg_duration_ms": {"direction": "minimize", "weight": 1.0},
        "load": {"direction": "minimize", "weight": 0.5},
    }

    model_config = SettingsConfigDict(env_file=_resolve_env_file(), env_file_encoding="utf-8", extra="ignore")


Settings = Config

settings = Config()
