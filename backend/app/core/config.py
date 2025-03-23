from pydantic_settings import BaseSettings
from typing import Optional
import os
from pathlib import Path


class Settings(BaseSettings):
    APP_NAME: str = "Chores Tracker"
    API_V1_STR: str = "/api/v1"
    
    # Database
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./chores_tracker.db")
    
    # CORS
    BACKEND_CORS_ORIGINS: list = ["*"]
    
    # Security
    SECRET_KEY: str = os.getenv("SECRET_KEY", "development_secret_key")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 8  # 8 days
    
    # Templates
    TEMPLATES_DIR: Path = Path(__file__).parent.parent / "templates"

    class Config:
        env_file = ".env"


settings = Settings()