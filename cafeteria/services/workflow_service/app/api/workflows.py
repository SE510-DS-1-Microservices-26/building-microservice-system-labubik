import logging
import os
from uuid import UUID

from fastapi import APIRouter, HTTPException, Depends, Request
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.application import WorkflowService
from app.core.infrastructure import PostgresWorkflowRepository, get_db

logger = logging.getLogger(__name__)
router = APIRouter()

CORE_SERVICE_URL = os.getenv("CORE_SERVICE_URL", "http://core-service:8080")


class PlaceOrderRequest(BaseModel):
    customer_name: str
    item_name: str
    quantity: int
    price: float
    owner_user_id: UUID


class WorkflowResponse(BaseModel):
    workflow_id: UUID
    type: str
    state: str
    payload: dict
    created_at: str
    updated_at: str
    last_error: str | None = None


def get_service(request: Request, db: Session = Depends(get_db)) -> WorkflowService:
    repo = PostgresWorkflowRepository(db)
    correlation_id = getattr(request.state, "correlation_id", "")
    return WorkflowService(
        repo,
        core_service_url=CORE_SERVICE_URL,
        correlation_id=correlation_id,
    )


def _to_response(wf) -> WorkflowResponse:
    return WorkflowResponse(
        workflow_id=wf.workflow_id,
        type=wf.type.value,
        state=wf.state.value,
        payload=wf.payload,
        created_at=str(wf.created_at),
        updated_at=str(wf.updated_at),
        last_error=wf.last_error,
    )


@router.post("/workflows/place-order", response_model=WorkflowResponse, status_code=201)
def start_place_order(
        body: PlaceOrderRequest,
        service: WorkflowService = Depends(get_service),
):
    logger.info("Starting place-order workflow for customer: %s", body.customer_name)
    wf = service.start_place_order(body.model_dump())
    return _to_response(wf)


@router.get("/workflows/{workflow_id}", response_model=WorkflowResponse)
def get_workflow(
        workflow_id: UUID,
        service: WorkflowService = Depends(get_service),
):
    wf = service.get_workflow(workflow_id)
    if wf is None:
        raise HTTPException(status_code=404, detail="Workflow not found")
    return _to_response(wf)
