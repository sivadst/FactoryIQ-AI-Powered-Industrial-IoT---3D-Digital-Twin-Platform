from pydantic_settings import BaseSettings

import os

class Settings(BaseSettings):
    PROJECT_NAME: str = "FactoryIQ"
    API_V1_STR: str = "/api/v1"
    SECRET_KEY: str = os.getenv("SECRET_KEY", "this_is_a_very_secret_key_for_development_only_12345")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 8
    
    # Postgres
    POSTGRES_USER: str = os.getenv("POSTGRES_USER", "factory_admin")
    POSTGRES_PASSWORD: str = os.getenv("POSTGRES_PASSWORD", "factory_password")
    POSTGRES_SERVER: str = os.getenv("POSTGRES_SERVER", "localhost")
    POSTGRES_PORT: str = os.getenv("POSTGRES_PORT", "5432")
    POSTGRES_DB: str = os.getenv("POSTGRES_DB", "factoryiq")
    
    @property
    def SQLALCHEMY_DATABASE_URI(self) -> str:
        return f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_SERVER}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        
    class Config:
        case_sensitive = True

settings = Settings()
