import json
import logging
import websockets
from typing import Any

logger = logging.getLogger("Keres.Beacon.Comms")

class BeaconComms:
    def __init__(self, ws_client: websockets.WebSocketClientProtocol):
        self.ws = ws_client

    async def send_json(self, payload: Any):
        """
        Serializes and sends data upstream.
        """
        try:
            if self.ws and self.ws.open:
                await self.ws.send(json.dumps(payload))
            else:
                logger.error("[-] Transport error: WebSocket is closed.")
        except Exception as e:
            logger.error(f"[-] Comms failure: {e}")

    async def receive_json(self) -> Any:
        """
        Wait for and decode incoming JSON messages.
        """
        message = await self.ws.recv()
        return json.loads(message)

    def __aiter__(self):
        return self.ws.__aiter__()