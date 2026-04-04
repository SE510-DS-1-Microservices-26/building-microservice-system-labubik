import logging
import uuid

from fastapi import FastAPI, Request

from app.api.orders import router as order_router

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s - %(message)s",
)
logger = logging.getLogger(__name__)

app = FastAPI(title="Cafeteria — Core Service")


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


app.include_router(order_router)


@app.get("/health")
def health():
    return {"status": "ok", "service": "core"}