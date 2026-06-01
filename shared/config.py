from pydantic_settings import BaseSettings


class Settings(BaseSettings):
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

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8", "extra": "ignore"}


settings = Settings()
