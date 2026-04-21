import os
from pydantic_settings import BaseSettings
from typing import Optional


class CoreSettings(BaseSettings):
    PROJECT_NAME: str = "Cerberus C2"
    VERSION: str = "2.0.0-2026"

    FERNET_KEY: str = os.getenv("CERBERUS_FERNET_KEY", "")
    JWT_SECRET: str = os.getenv("CERBERUS_JWT_SECRET", "")
    ALGORITHM: str = "HS256"

    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./storage/db/cerberus.db")

    BEACON_AUTH_TOKEN: str = os.getenv("BEACON_AUTH_TOKEN", "")

    class Config:
        env_file = ".env"


settings = CoreSettings()