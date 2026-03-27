import logging

from fastapi import FastAPI

from app.api.workflows import router as workflow_router

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s - %(message)s",
)

app = FastAPI(title="Cafeteria — Workflow Service")

app.include_router(workflow_router)


@app.get("/health")
def health():
    return {"status": "ok", "service": "workflow"}
