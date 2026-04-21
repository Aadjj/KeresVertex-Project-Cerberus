import asyncio
import websockets
import logging
import json
from typing import Optional

logger = logging.getLogger("Keres.WS_Client")


class WebSocketClient:
    def __init__(self, url: str, api_key: str):
        self.url = url
        self.api_key = api_key
        self.connection: Optional[websockets.WebSocketClientProtocol] = None
        self.is_running = True

    async def maintain_connection(self):
        backoff = 1
        while self.is_running:
            try:
                logger.info(f"[*] Attempting tunnel connection to {self.url}...")

                headers = {"Authorization": f"Bearer {self.api_key}"}

                async with websockets.connect(
                        self.url,
                        extra_headers=headers,
                        ping_interval=20,
                        ping_timeout=10
                ) as ws:
                    self.connection = ws
                    backoff = 1
                    logger.info("[+] Backhaul tunnel established with Teamserver.")

                    await self.send_json({"event": "listener_online", "data": "Edge-01"})

                    async for message in ws:
                        await self._handle_message(message)

            except (websockets.ConnectionClosed, ConnectionRefusedError, OSError) as e:
                self.connection = None
                logger.warning(f"[!] Tunnel lost: {e}. Reconnecting in {backoff}s...")
                await asyncio.sleep(backoff)
                backoff = min(backoff * 2, 60)

            except Exception as e:
                logger.error(f"[-] Unexpected tunnel error: {e}")
                await asyncio.sleep(5)

    async def _handle_message(self, message: str):
        try:
            data = json.loads(message)
            event = data.get("event")

            if event == "task_for_beacon":
                logger.info(f"[*] Received task for beacon {data.get('beacon_id')}")

        except json.JSONDecodeError:
            logger.error("[-] Received malformed JSON from Teamserver.")

    async def send_json(self, payload: dict):
        if self.connection and self.connection.open:
            await self.connection.send(json.dumps(payload))
        else:
            logger.error("[-] Cannot send data: Tunnel is offline.")

    async def shutdown(self):
        self.is_running = False
        if self.connection:
            await self.connection.close()