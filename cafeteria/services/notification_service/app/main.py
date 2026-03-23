import asyncio
import logging
from contextlib import asynccontextmanager
from typing import Optional

from fastapi import FastAPI

from app.api.notifications import router as notifications_router
from app.core.infrastructure.consumer import start_consumer

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s - %(message)s",
)
logger = logging.getLogger(__name__)

consumer_task: Optional[asyncio.Task] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global consumer_task
    logger.info("Starting RabbitMQ consumer background task")
    consumer_task = asyncio.create_task(start_consumer())
    yield
    if consumer_task:
        consumer_task.cancel()
        try:
            await consumer_task
        except asyncio.CancelledError:
            pass
    logger.info("Consumer task stopped")


app = FastAPI(title="Cafeteria — Notification Service", lifespan=lifespan)

app.include_router(notifications_router)


@app.get("/health")
def health():
    return {"status": "ok", "service": "notification"}
