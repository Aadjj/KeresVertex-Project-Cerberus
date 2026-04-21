import os
import secrets
from typing import Optional
from pydantic_settings import BaseSettings


class BeaconSettings(BaseSettings):
    SERVER_URL: str = 'https://edge-listener.com/receive'
    WS_URL: str = 'wss://edge-listener.com/ws'

    BEACON_ID: str = os.getenv("BEACON_ID", secrets.token_hex(4))
    OPERATIONAL_TOKEN: str = "keres_shadow_key_2026"

    SLEEP_TIME: int = 30
    JITTER: float = 0.2
    RECONNECT_DELAY: int = 5

    TLS_VERIFY: bool = True
    TLS_CERT_PATH: Optional[str] = None
    TLS_KEY_PATH: Optional[str] = None

    PLUGIN_PATH: str = './plugins'
    LOOT_DIR: str = './temp'

    model_config = {
        "env_file": ".env",
        "case_sensitive": True,
        "extra": "ignore"
    }


settings = BeaconSettings()