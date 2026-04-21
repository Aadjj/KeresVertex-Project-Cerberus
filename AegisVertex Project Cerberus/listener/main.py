import asyncio
import uvicorn
import logging
from fastapi import FastAPI, Request, status
from contextlib import asynccontextmanager

from handlers import handle_incoming_data
from websocket import WebSocketClient

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("Keres.Listener")

ts_client = WebSocketClient(uri="wss://teamserver.internal/ws/listener_1")


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("[*] Listener starting up...")

    connection_task = asyncio.create_task(ts_client.maintain_connection())

    yield

    logger.info("[*] Listener shutting down...")
    connection_task.cancel()
    try:
        await connection_task
    except asyncio.CancelledError:
        pass


app = FastAPI(title="Keres Edge Listener", lifespan=lifespan)


@app.post("/receive", status_code=status.HTTP_200_OK)
async def receive_data(request: Request):
    try:
        data = await request.json()
        response = await handle_incoming_data(data, ts_client)

        return response if response else {"status": "ok"}

    except Exception as e:
        logger.error(f"[-] Error processing beacon data: {e}")
        return {"status": "error", "message": "Invalid payload"}


@app.get("/")
async def index():
    return {"service": "running"}


@app.post("/receive")
async def receive_data(
    request: Request,
    authenticated: bool = Security(authenticate_beacon)
):
    data = await request.json()
    response = await handle_incoming_data(data, ts_client)
    return response if response else {"status": "ok"}


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8080,
        log_level="info",
        proxy_headers=True
    )