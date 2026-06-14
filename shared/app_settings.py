from typing import List

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # General
    app_name: str = "BioPulse"
    version: str = "1.0.0"
    debug: bool = True

    # CORS
    cors_origins: List[str] = ["*"]

    # Cloud API URL used by other services
    cloud_api_base: str = "http://localhost:8000"

    # Data directory
    data_dir: str = ""  # empty = auto-detect

    # Logging
    log_level: str = "INFO"

    # Redis
    redis_url: str = "redis://localhost:6379/0"

    model_config = {"env_prefix": "OCFE_", "env_file": ".env", "extra": "ignore"}

    # AI
    ai_local_endpoint: str = "http://localhost:11434"


settings = Settings()
