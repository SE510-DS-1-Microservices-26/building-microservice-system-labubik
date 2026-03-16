import logging

from fastapi import FastAPI

from app.api.users import router as users_router

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s - %(message)s",
)

app = FastAPI(title="Cafeteria — Users Service")

app.include_router(users_router)


@app.get("/health")
def health():
    return {"status": "ok", "service": "users"}
