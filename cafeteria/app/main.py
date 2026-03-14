import logging

from fastapi import FastAPI

from app.api.orders import router as order_router

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s - %(message)s",
)

app = FastAPI(title="Cafeteria delivery: Modular Monolith")

app.include_router(order_router)


@app.get("/health")
def health():
    return {"status": "ok"}
