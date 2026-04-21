import httpx
import asyncio
import logging
from typing import Dict, Any

logger = logging.getLogger("Keres.APIClient")


class TeamserverClient:
    def __init__(self, base_url: str, api_key: str):
        self.base_url = base_url
        self.headers = {"Authorization": f"Bearer {api_key}"}
        self.client = httpx.AsyncClient(
            headers=self.headers,
            timeout=15.0,
            limits=httpx.Limits(max_connections=100)
        )

    async def forward_to_teamserver(self, data: Dict[str, Any], endpoint: str = "/api/v1/beacons/data"):
        url = f"{self.base_url}{endpoint}"
        max_retries = 3

        for attempt in range(max_retries):
            try:
                response = await self.client.post(url, json=data)
                response.raise_for_status()
                return response.json()

            except (httpx.ConnectError, httpx.TimeoutException):
                wait_time = (attempt + 1) * 2
                logger.warning(
                    f"Teamserver unreachable (Attempt {attempt + 1}/{max_retries}). Retrying in {wait_time}s...")
                await asyncio.sleep(wait_time)

            except httpx.HTTPStatusError as e:
                logger.error(f"Teamserver rejected data: {e.response.status_code}")
                break

        return None

    async def close(self):
        await self.client.aclose()