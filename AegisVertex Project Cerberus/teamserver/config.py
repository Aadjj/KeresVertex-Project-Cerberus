import os
from typing import Optional
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings


class ListenerSettings(BaseSettings):
    HOST: str = Field('0.0.0.0', alias='LISTENER_HOST')
    PORT: int = Field(9000, alias='LISTENER_PORT')
    PROTOCOL: str = Field('TCP', alias='LISTENER_PROTOCOL')

    USE_TLS: bool = Field(False, alias='USE_TLS')
    TLS_CERT_PATH: Optional[str] = Field(None, alias='TLS_CERT_PATH')
    TLS_KEY_PATH: Optional[str] = Field(None, alias='TLS_KEY_PATH')

    LOG_LEVEL: str = Field('INFO', alias='LOG_LEVEL')
    PLUGIN_PATH: str = Field('./plugins', alias='PLUGIN_PATH')

    DEFAULT_JITTER: float = 0.2
    DEFAULT_SLEEP: int = 60

    DATABASE_URL: str = Field('sqlite+aiosqlite:///./keres.db', alias='DATABASE_URL')
    SECRET_KEY: str = Field('change-me-in-production', alias='SECRET_KEY')
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_MINUTES: int = 1440

    @field_validator('PROTOCOL')
    @classmethod
    def validate_protocol(cls, v: str):
        allowed = ['TCP', 'UDP', 'HTTP', 'HTTPS']
        if v.upper() not in allowed:
            raise ValueError(f"Protocol must be one of {allowed}")
        return v.upper()

    @field_validator('TLS_CERT_PATH', 'TLS_KEY_PATH')
    @classmethod
    def validate_tls_files(cls, v: Optional[str], info):
        if info.data.get('USE_TLS') and not v:
            raise ValueError("Path must be set if USE_TLS is True")
        return v

    model_config = {
        "env_file": ".env",
        "case_sensitive": True,
        "extra": "ignore"
    }


settings = ListenerSettings()