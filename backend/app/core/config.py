from pydantic_settings import BaseSettings
from typing import Optional, List, Union
import os
from pathlib import Path


class Settings(BaseSettings):
    APP_NAME: str = "Chores Tracker"
    API_V1_STR: str = "/api/v1"
    
    # Environment
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
    
    # Database
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./chores_tracker.db")
    
    # CORS
    BACKEND_CORS_ORIGINS: Union[List[str], str] = os.getenv("BACKEND_CORS_ORIGINS", "*")
    
    @property
    def CORS_ORIGINS(self) -> List[str]:
        if isinstance(self.BACKEND_CORS_ORIGINS, str):
            return [origin.strip() for origin in self.BACKEND_CORS_ORIGINS.split(",")]
        return self.BACKEND_CORS_ORIGINS
    
    # Security
    SECRET_KEY: str = os.getenv("SECRET_KEY", "development_secret_key")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 60 * 24 * 8))  # 8 days
    
    # Templates
    TEMPLATES_DIR: Path = Path(__file__).parent.parent / "templates"
    
    # Debug
    DEBUG: bool = os.getenv("DEBUG", "True").lower() in ("true", "1", "t")

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()