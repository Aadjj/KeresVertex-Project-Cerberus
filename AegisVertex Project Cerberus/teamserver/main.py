import uvicorn
import logging
import signal
import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

import config
import models
import db
import api
import plugins
from websocket import WebSocketManager

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s'
)
logger = logging.getLogger("Keres.Main")

ws_manager = WebSocketManager()


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Keres Teamserver initializing...")

    async with db.engine.begin() as conn:
        await conn.run_sync(models.Base.metadata.create_all)

    plugins.register(app)

    yield

    logger.info("Keres Teamserver shutting down...")


app = FastAPI(
    title="Keres C2 Teamserver",
    version="1.0.0",
    lifespan=lifespan,
    debug=config.settings.DEBUG
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api.router, prefix="/api")

app.state.ws_manager = ws_manager


@app.websocket("/ws/{group_id}")
async def websocket_endpoint(websocket: WebSocket, group_id: str):
    await ws_manager.connect(websocket, group=group_id)
    try:
        while True:
            data = await websocket.receive_text()

            await ws_manager.broadcast(
                {
                    "event": "chat",
                    "group": group_id,
                    "data": data
                },
                group=group_id
            )
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket, group=group_id)
    except Exception as e:
        logger.error(f"WebSocket Error in group {group_id}: {e}")
        ws_manager.disconnect(websocket, group=group_id)


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=config.settings.HOST,
        port=config.settings.PORT,
        reload=config.settings.DEBUG,
        log_level="info"
    )