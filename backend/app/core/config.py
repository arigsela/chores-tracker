from pydantic import ConfigDict
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
    _raw_database_url: str = os.getenv(
        "DATABASE_URL",
        "mysql+aiomysql://chores-user:password@localhost:3306/chores-db"
    )

    @property
    def DATABASE_URL(self) -> str:
        """
        Ensure DATABASE_URL always uses aiomysql driver for async compatibility.

        This automatically converts:
        - mysql://... -> mysql+aiomysql://...
        - mysql+mysqldb://... -> mysql+aiomysql://...
        - mysql+pymysql://... -> mysql+aiomysql://...
        """
        url = self._raw_database_url

        # Force aiomysql driver for any MySQL connection
        if url.startswith("mysql://"):
            url = url.replace("mysql://", "mysql+aiomysql://", 1)
        elif url.startswith("mysql+mysqldb://"):
            url = url.replace("mysql+mysqldb://", "mysql+aiomysql://", 1)
        elif url.startswith("mysql+pymysql://"):
            url = url.replace("mysql+pymysql://", "mysql+aiomysql://", 1)

        return url
    
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
    
    # Testing
    TESTING: bool = os.getenv("TESTING", "False").lower() in ("true", "1", "t")
    
    # Registration Control (Beta Feature)
    # Comma-separated list of valid registration codes for beta users
    REGISTRATION_CODES: Union[List[str], str] = os.getenv(
        "REGISTRATION_CODES",
        "BETA2024,FAMILY_TRIAL,CHORES_BETA"  # Default codes for development
    )

    @property
    def VALID_REGISTRATION_CODES(self) -> List[str]:
        """Parse registration codes from environment variable."""
        if isinstance(self.REGISTRATION_CODES, str):
            return [code.strip().upper() for code in self.REGISTRATION_CODES.split(",") if code.strip()]
        return [code.upper() for code in self.REGISTRATION_CODES if code]

    # Metrics Security
    # Comma-separated list of IPs/CIDR ranges allowed to access /metrics endpoint
    # Default allows: localhost, internal networks (10.x, 172.16-31.x, 192.168.x)
    METRICS_ALLOWED_IPS: str = os.getenv(
        "METRICS_ALLOWED_IPS",
        "127.0.0.1,10.0.0.0/8,172.16.0.0/12,192.168.0.0/16"
    )

    @property
    def metrics_allowed_ips_list(self) -> List[str]:
        """Parse METRICS_ALLOWED_IPS into a list."""
        return [ip.strip() for ip in self.METRICS_ALLOWED_IPS.split(",") if ip.strip()]

    # Optional bearer token for metrics access (if not using IP whitelist)
    METRICS_AUTH_TOKEN: Optional[str] = os.getenv("METRICS_AUTH_TOKEN", None)

    model_config = ConfigDict(
        env_file=".env",
        case_sensitive=True,
        extra='ignore'  # Ignore extra environment variables not defined in Settings
    )


settings = Settings()
