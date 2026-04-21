import os
import asyncio
import httpx
import json
import logging
import secrets
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Optional

logger = logging.getLogger("Keres.Auth")


class AuthService:
    def __init__(self, api_url: str, username: str, password: str, token_path: str = "./.vault"):
        self.api_url = api_url
        self.username = username
        self.password = password
        self.token_file = Path(token_path) / "session.dat"

        self.common_headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
            "Accept": "application/json",
            "X-Keres-Session": secrets.token_hex(8)
        }

        self.http_client = httpx.AsyncClient(
            base_url=self.api_url,
            headers=self.common_headers,
            timeout=15.0,
            verify=False
        )

        self.access_token: Optional[str] = None
        self.refresh_token: Optional[str] = None
        self.token_expiry: datetime = datetime.now(timezone.utc)
        self.lock = asyncio.Lock()
        self._renew_task: Optional[asyncio.Task] = None
        self._stop_event = asyncio.Event()

        self._load_tokens_from_vault()

    def _load_tokens_from_vault(self):
        if self.token_file.exists():
            try:
                data = json.loads(self.token_file.read_text())
                self.access_token = data.get('at')
                self.refresh_token = data.get('rt')
                if data.get('exp'):
                    self.token_expiry = datetime.fromisoformat(data['exp'])
                logger.info("Vault unlocked. Session restored.")
            except Exception as e:
                logger.error(f"Vault corruption detected: {e}")

    def _save_tokens_to_vault(self):
        try:
            self.token_file.parent.mkdir(parents=True, exist_ok=True)
            data = {
                'at': self.access_token,
                'rt': self.refresh_token,
                'exp': self.token_expiry.isoformat()
            }
            self.token_file.write_text(json.dumps(data))
        except Exception as e:
            logger.warning(f"Failed to secure vault: {e}")

    async def authenticate(self):
        backoff = 2
        while not self._stop_event.is_set():
            try:
                logger.info(f"Attempting authentication for {self.username}...")
                response = await self.http_client.post('/auth/login', json={
                    'username': self.username,
                    'password': self.password
                })

                if response.status_code == 200:
                    self._update_state(response.json())
                    self._start_renewal_loop()
                    return True

                logger.error(f"Login rejected: {response.status_code}")

            except httpx.RequestError as e:
                logger.warning(f"Connection failed: {e}. Retrying in {backoff}s...")

            await asyncio.sleep(backoff)
            backoff = min(backoff * 1.5, 30)

    async def get_valid_token(self) -> str:
        async with self.lock:
            now = datetime.now(timezone.utc)
            if not self.access_token or (self.token_expiry - now).total_seconds() < 30:
                await self.refresh_session()
            return self.access_token

    async def refresh_session(self):
        if not self.refresh_token:
            await self.authenticate()
            return

        try:
            response = await self.http_client.post('/auth/refresh', json={
                'refresh_token': self.refresh_token
            })
            if response.status_code == 200:
                self._update_state(response.json())
            else:
                logger.warning("Session expired. Full re-auth required.")
                await self.authenticate()
        except Exception as e:
            logger.error(f"Session refresh failed: {e}")

    def _update_state(self, data: dict):
        self.access_token = data.get('access_token')
        self.refresh_token = data.get('refresh_token')
        expires_in = data.get('expires_in', 3600)
        self.token_expiry = datetime.now(timezone.utc) + timedelta(seconds=expires_in - 30)
        self._save_tokens_to_vault()

    def _start_renewal_loop(self):
        if not self._renew_task or self._renew_task.done():
            self._renew_task = asyncio.create_task(self._renewal_worker())

    async def _renewal_worker(self):
        while not self._stop_event.is_set():
            now = datetime.now(timezone.utc)
            sleep_duration = (self.token_expiry - now).total_seconds() - 60

            if sleep_duration > 0:
                try:
                    await asyncio.wait_for(self._stop_event.wait(), timeout=sleep_duration)
                except asyncio.TimeoutError:
                    pass

            if not self._stop_event.is_set():
                await self.refresh_session()

    async def shutdown(self):
        self._stop_event.set()
        if self._renew_task:
            self._renew_task.cancel()
        self.access_token = None
        self.refresh_token = None
        await self.http_client.aclose()
        logger.info("Session closed securely.")