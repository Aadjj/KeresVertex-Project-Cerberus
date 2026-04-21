import os
import asyncio
import json
import logging
import random
import websockets
from typing import Callable, Dict, Any, Optional
from .auth_service import AuthService

logger = logging.getLogger("Keres.WS")


class WebSocketClient:
    def __init__(self, auth_service: AuthService):
        self.auth_service = auth_service
        self.ws_url = os.getenv('TEAMSERVER_WS_URL', 'wss://localhost/ws')
        self.ws: Optional[websockets.WebSocketClientProtocol] = None
        self.event_handlers: Dict[str, Callable] = {}
        self.stop_event = asyncio.Event()
        self.connect_task: Optional[asyncio.Task] = None

        self.headers = self.auth_service.common_headers

    def register_event_handler(self, event_type: str, handler: Callable):
        self.event_handlers[event_type] = handler
        logger.debug(f"Registered handler for event: {event_type}")

    async def _connect_loop(self):
        backoff = 2
        while not self.stop_event.is_set():
            try:
                token = await self.auth_service.get_valid_token()

                current_headers = self.headers.copy()
                current_headers['Authorization'] = f'Bearer {token}'

                logger.info(f"Connecting to Teamserver WS at {self.ws_url}...")

                async with websockets.connect(
                        self.ws_url,
                        extra_headers=current_headers,
                        ping_interval=20,
                        ping_timeout=10,
                        close_timeout=5
                ) as ws:
                    self.ws = ws
                    logger.info("WebSocket Link Established.")
                    backoff = 2

                    async for message in ws:
                        if self.stop_event.is_set():
                            break
                        await self._handle_message(message)

            except (websockets.ConnectionClosed, websockets.InvalidStatusCode) as e:
                logger.warning(f"Connection lost ({e}). Reconnecting...")
            except Exception as e:
                logger.error(f"WebSocket Error: {type(e).__name__}")

            if not self.stop_event.is_set():
                sleep_time = backoff + random.uniform(0, 1)
                logger.info(f"Retrying connection in {sleep_time:.2f}s...")
                await asyncio.sleep(sleep_time)
                backoff = min(backoff * 1.5, 60)

    async def _handle_message(self, message: str):
        try:
            data = json.loads(message)
            event_type = data.get('event')

            logger.debug(f"Received Event: {event_type}")

            handler = self.event_handlers.get(event_type)
            if handler:
                if asyncio.iscoroutinefunction(handler):
                    await handler(data)
                else:
                    handler(data)
            else:
                logger.info(f"No handler registered for: {event_type}")

        except json.JSONDecodeError:
            logger.error("Received non-JSON payload from WebSocket.")
        except Exception as e:
            logger.exception(f"Error in event handler: {e}")

    async def start(self):
        if self.connect_task is None or self.connect_task.done():
            self.stop_event.clear()
            self.connect_task = asyncio.create_task(self._connect_loop())

    async def send_event(self, event_type: str, data: Dict[str, Any]):
        if self.ws and self.ws.open:
            payload = json.dumps({"event": event_type, **data})
            await self.ws.send(payload)
        else:
            logger.warning("Attempted to send over closed WebSocket.")

    async def close(self):
        logger.info("Closing WebSocket connection...")
        self.stop_event.set()
        if self.ws:
            await self.ws.close()
        if self.connect_task:
            try:
                await asyncio.wait_for(self.connect_task, timeout=5)
            except asyncio.TimeoutError:
                self.connect_task.cancel()
        logger.info("WebSocket Interface Offline.")