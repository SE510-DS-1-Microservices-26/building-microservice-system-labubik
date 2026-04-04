import asyncio
import logging
import uuid
from contextlib import asynccontextmanager
from typing import Optional

from fastapi import FastAPI, Request

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


@app.middleware("http")
async def correlation_id_middleware(request: Request, call_next):
    correlation_id = request.headers.get("X-Correlation-Id")
    if not correlation_id:
        correlation_id = str(uuid.uuid4())

    request.state.correlation_id = correlation_id

    logger.info(
        "[%s] %s %s",
        correlation_id,
        request.method,
        request.url.path,
    )

    response = await call_next(request)
    response.headers["X-Correlation-Id"] = correlation_id
    return response


app.include_router(notifications_router)


@app.get("/health")
def health():
    return {"status": "ok", "service": "notification"}