import logging
import uuid

from fastapi import FastAPI, Request

from app.api.orders import router as order_router

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s [%(correlation_id)s] - %(message)s",
)

app = FastAPI(title="Cafeteria delivery: Modular Monolith")


@app.middleware("http")
async def add_correlation_id(request: Request, call_next):
    correlation_id = request.headers.get("X-Correlation-Id", str(uuid.uuid4()))
    request.state.correlation_id = correlation_id
    response = await call_next(request)
    response.headers["X-Correlation-Id"] = correlation_id
    return response


app.include_router(order_router)


@app.get("/health")
def health():
    return {"status": "ok"}