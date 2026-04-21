import json
import logging
from typing import List, Dict, Any, Union
from fastapi import WebSocket

logger = logging.getLogger("Keres.WS_Manager")


class WebSocketManager:
    def __init__(self):
        self.active_connections: Dict[Union[int, str], List[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, group: Union[int, str]):
        await websocket.accept()

        if group not in self.active_connections:
            self.active_connections[group] = []

        self.active_connections[group].append(websocket)
        logger.info(f"Operator connected to Group {group}. Total in group: {len(self.active_connections[group])}")

    def disconnect(self, websocket: WebSocket, group: Union[int, str]):
        if group in self.active_connections:
            try:
                self.active_connections[group].remove(websocket)
                if not self.active_connections[group]:
                    del self.active_connections[group]
                logger.info(f"Operator disconnected from Group {group}.")
            except ValueError:
                pass

    async def send_personal_message(self, message: dict, websocket: WebSocket):
        await websocket.send_json(message)

    async def broadcast(self, message: Any, group: Union[int, str] = "broadcast"):
        targets = []

        if group == "broadcast":
            for connections in self.active_connections.values():
                targets.extend(connections)
        elif group in self.active_connections:
            targets = self.active_connections[group]

        if not targets:
            return

        payload = message if isinstance(message, dict) else {"event": "info", "data": str(message)}

        for connection in targets:
            try:
                await connection.send_json(payload)
            except Exception as e:
                logger.error(f"Failed to send WS message: {e}")