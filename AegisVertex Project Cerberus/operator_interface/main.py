import os
import asyncio
import logging
import signal
from typing import Any, Dict

from .auth_service import AuthService
from .api_client import APIClient
from .websocket_client import WebSocketClient

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s'
)
logger = logging.getLogger("Keres.Operator")


class KeresOperator:
    def __init__(self):
        self.api_url = os.getenv('TEAMSERVER_API_URL', 'https://localhost/api')
        self.username = os.getenv('TEAMSERVER_USERNAME', 'admin')
        self.password = os.getenv('TEAMSERVER_PASSWORD', 'password123')

        self.auth = AuthService(self.api_url, self.username, self.password)
        self.api = APIClient(self.auth)
        self.ws = WebSocketClient(self.auth)

        self.shutdown_event = asyncio.Event()

    async def on_new_beacon(self, event: Dict[str, Any]):
        data = event.get('data', {})
        logger.info(f"[*] NEW BEACON: {data.get('id')} @ {data.get('ip')} ({data.get('os')})")

    async def on_task_result(self, event: Dict[str, Any]):
        data = event.get('data', {})
        logger.info(f"[+] TASK COMPLETE [{data.get('task_id')}]:\n{data.get('output')}")

    async def setup(self):
        logger.info("Initializing Keres Operator session...")
        auth_success = await self.auth.authenticate()
        if not auth_success:
            logger.error("Failed to establish initial session. Check credentials/URL.")
            return False

        self.ws.register_event_handler('beacon_register', self.on_new_beacon)
        self.ws.register_event_handler('task_result', self.on_task_result)

        await self.ws.start()
        return True

    async def run_example_ops(self):
        try:
            beacons = await self.api.request('GET', '/beacons')
            logger.info(f"Active Beacons: {len(beacons)}")

            if beacons:
                target_id = beacons[0]['id']
                await self.api.request('POST', f'/beacons/{target_id}/tasks', json={
                    'command': 'whoami',
                    'options': '/all'
                })
                logger.info(f"Tasked {target_id} with 'whoami'")

        except Exception as e:
            logger.error(f"Operational error: {e}")

    async def shutdown(self):
        logger.info("Commencing graceful shutdown...")
        self.shutdown_event.set()

        await self.ws.close()
        await self.api.close()
        await self.auth.shutdown()

        logger.info("Keres Operator Offline.")


async def main():
    operator = KeresOperator()

    loop = asyncio.get_running_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, lambda: asyncio.create_task(operator.shutdown()))

    if await operator.setup():
        await operator.run_example_ops()

        try:
            await operator.shutdown_event.wait()
        except asyncio.CancelledError:
            pass


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass