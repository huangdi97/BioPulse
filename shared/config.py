from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Auth
    SECRET_KEY: str = "dev-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # Database
    DATABASE_URL: str = "sqlite:///./data/cloud.db"
    DB_POOL_SIZE: int = 5
    DB_MAX_OVERFLOW: int = 20

    # Server
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    # AI Gateway
    AI_GATEWAY_URL: str = "http://localhost:8000/ai/chat"
    AI_GATEWAY_TIMEOUT: int = 120

    # Legacy fields — kept for backward compatibility
    deepseek_api_key: str = ""
    jwt_secret_key: str = "dev-secret-key-change-in-production"
    cors_origins: str = "*"
    cloud_db_path: str = "data/cloud.db"
    assistant_db_path: str = "data/assistant.db"
    opportunity_db_path: str = "data/opportunity.db"
    sales_assistant_db_path: str = "data/sales_assistant.db"
    sales_coach_db_path: str = "data/sales_coach.db"
    cloud_port: int = 8000
    assistant_port: int = 8003
    opportunity_port: int = 8002
    sales_assistant_port: int = 8004
    sales_coach_port: int = 8001

    # Pareto routing objectives — direction must be "maximize" or "minimize"
    PARETO_OBJECTIVES: dict = {
        "success_rate": {"direction": "maximize", "weight": 1.0},
        "avg_duration_ms": {"direction": "minimize", "weight": 1.0},
        "load": {"direction": "minimize", "weight": 0.5},
    }

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


settings = Settings()
