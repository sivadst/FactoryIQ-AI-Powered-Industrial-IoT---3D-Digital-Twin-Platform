from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List, Optional
import os

class Settings(BaseSettings):
    model_config = SettingsConfigDict(case_sensitive=True, env_file=".env", extra="ignore")
    
    PROJECT_NAME: str = "FactoryIQ — Industrial AI & 3D Digital Twin Platform"
    VERSION: str = "2.0.0"
    API_V1_STR: str = "/api/v1"
    
    # Security & JWT
    SECRET_KEY: str = os.getenv("SECRET_KEY", "factoryiq-industrial-enterprise-secret-key-change-in-production-2026")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 12  # 12 hours
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # Environment & Mode
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
    DEBUG: bool = os.getenv("DEBUG", "True").lower() in ("true", "1")
    
    # CORS
    BACKEND_CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:8000",
        "http://127.0.0.1:8000",
    ]
    
    # Database Configuration
    USE_SQLITE: bool = os.getenv("USE_SQLITE", "True").lower() in ("true", "1")
    SQLITE_DB_PATH: str = os.getenv("SQLITE_DB_PATH", "factoryiq.db")
    
    POSTGRES_USER: str = os.getenv("POSTGRES_USER", "factory_admin")
    POSTGRES_PASSWORD: str = os.getenv("POSTGRES_PASSWORD", "factory_password")
    POSTGRES_SERVER: str = os.getenv("POSTGRES_SERVER", "localhost")
    POSTGRES_PORT: str = os.getenv("POSTGRES_PORT", "5432")
    POSTGRES_DB: str = os.getenv("POSTGRES_DB", "factoryiq")
    
    # Telemetry & Factory Simulator Config
    MACHINES_COUNT: int = 24
    SIMULATION_INTERVAL_SECONDS: float = 1.0
    OEE_CALCULATION_INTERVAL_SECONDS: int = 15
    WORK_ORDER_INTERVAL_SECONDS: int = 30
    
    @property
    def SQLALCHEMY_DATABASE_URI(self) -> str:
        if self.USE_SQLITE:
            return f"sqlite+aiosqlite:///{self.SQLITE_DB_PATH}"
        return f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_SERVER}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        
    @property
    def SYNC_DATABASE_URI(self) -> str:
        if self.USE_SQLITE:
            return f"sqlite:///{self.SQLITE_DB_PATH}"
        return f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_SERVER}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"

settings = Settings()
