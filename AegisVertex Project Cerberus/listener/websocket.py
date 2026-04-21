import asyncio
import websockets
import logging
import json
from typing import Optional


class WebSocketManager:
    def __init__(self, url: str, api_key: str):
        self.url = url
        self.api_key = api_key
        self.websocket: Optional[websockets.WebSocketClientProtocol] = None
        self.connected = asyncio.Event()
        self.message_queue = asyncio.Queue()
        self.logger = logging.getLogger("Keres.WS_Manager")
        self.is_running = True

    async def connect(self):
        backoff = 1
        headers = {"Authorization": f"Bearer {self.api_key}"}

        while self.is_running:
            try:
                self.logger.info(f"[*] Connecting to Backhaul: {self.url}")
                async with websockets.connect(
                        self.url,
                        extra_headers=headers,
                        ping_interval=20,
                        ping_timeout=10
                ) as ws:
                    self.websocket = ws
                    self.logger.info("[+] Tunnel connected and authenticated.")

                    self.connected.set()
                    backoff = 1

                    await self._listen()

            except Exception as e:
                self.connected.clear()
                self.websocket = None
                self.logger.warning(f"[!] Tunnel disconnected ({e}). Retrying in {backoff}s...")

                if not self.is_running:
                    break

                await asyncio.sleep(backoff)
                backoff = min(backoff * 2, 60)

    async def _listen(self):
        try:
            async for message in self.websocket:
                await self._handle_incoming(message)
        except websockets.ConnectionClosed:
            self.logger.info("[-] Teamserver closed the connection.")
        finally:
            self.connected.clear()

    async def _handle_incoming(self, message: str):
        self.logger.debug(f"Received from Teamserver: {message}")
        try:
            await self.message_queue.put(json.loads(message))
        except json.JSONDecodeError:
            self.logger.error("[-] Received non-JSON message from Teamserver.")

    async def send_event(self, event_type: str, data: dict):
        await self.connected.wait()

        payload = json.dumps({"event": event_type, "data": data})
        try:
            await self.websocket.send(payload)
        except Exception as e:
            self.logger.error(f"[-] Failed to send event to Teamserver: {e}")
            self.connected.clear()

    async def stop(self):
        self.is_running = False
        self.connected.clear()
        if self.websocket:
            await self.websocket.close()

    async def run(self):
        await self.connect()