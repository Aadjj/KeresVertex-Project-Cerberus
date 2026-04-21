import os
import asyncio
import httpx
import logging
import random
from typing import Any, Dict, Optional
from .auth_service import AuthService

logger = logging.getLogger("Keres.API")


class APIClient:
    def __init__(self, auth_service: AuthService):
        self.auth_service = auth_service
        self.api_base_url = os.getenv('TEAMSERVER_API_URL', 'https://localhost/api')

        self.http_client = httpx.AsyncClient(
            base_url=self.api_base_url,
            headers=self.auth_service.common_headers,
            timeout=20.0,
            follow_redirects=True
        )

        self.retry_limit = 5
        self.base_backoff = 2.0
        self.lock = asyncio.Lock()

    async def request(self, method: str, path: str, **kwargs) -> Any:
        retries = 0
        while retries < self.retry_limit:
            token = await self.auth_service.get_valid_token()

            headers = kwargs.pop('headers', {})
            headers['Authorization'] = f'Bearer {token}'
            headers['X-Request-ID'] = f"{random.getrandbits(32):x}"

            try:
                response = await self.http_client.request(
                    method,
                    path,
                    headers=headers,
                    **kwargs
                )

                if response.status_code == 401:
                    logger.warning(f"Unauthorized (401) for {path}. Forcing session refresh.")
                    await self.auth_service.refresh_session()
                    retries += 1
                    continue

                if response.status_code in [429, 500, 502, 503, 504]:
                    logger.error(f"Server error {response.status_code}. Retrying...")
                    retries += 1
                    await self._jittered_sleep(retries)
                    continue

                response.raise_for_status()

                if response.headers.get("Content-Type") == "application/json":
                    return response.json()
                return response.content

            except httpx.HTTPStatusError as e:
                logger.error(f"HTTP Failure [{e.response.status_code}] -> {method} {path}")
                break

            except (httpx.RequestError, asyncio.TimeoutError) as e:
                retries += 1
                logger.warning(f"Network error (Attempt {retries}): {type(e).__name__}")
                await self._jittered_sleep(retries)

        raise Exception(f"Keres API Request failed: {method} {path} after {self.retry_limit} attempts.")

    async def _jittered_sleep(self, attempt: int):
        sleep_time = (self.base_backoff * (2 ** (attempt - 1))) + random.uniform(0, 1)
        await asyncio.sleep(sleep_time)

    async def close(self):
        await self.http_client.aclose()
        logger.info("API Client connection pool closed.")