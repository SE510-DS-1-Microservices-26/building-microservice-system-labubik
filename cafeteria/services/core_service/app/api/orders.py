import logging
import os
from uuid import UUID

from fastapi import APIRouter, HTTPException, Depends, Request
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.application import OrderService
from app.core.application.order_service import UserValidationError, UsersServiceUnavailable
from app.core.domain import OrderStatus
from app.core.infrastructure import PostgresOrderRepository, get_db

logger = logging.getLogger(__name__)
router = APIRouter()

USERS_BASE_URL = os.getenv("USERS_BASE_URL", "")


class CreateOrderRequest(BaseModel):
    customer_name: str
    item_name: str
    quantity: int
    price: float
    owner_user_id: UUID


class UpdateStatusRequest(BaseModel):
    status: OrderStatus


class OrderResponse(BaseModel):
    id: UUID
    customer_name: str
    item_name: str
    quantity: int
    price: float
    total: float
    status: OrderStatus
    owner_user_id: UUID

    model_config = {"from_attributes": True}


def get_service(request: Request, db: Session = Depends(get_db)) -> OrderService:
    repo = PostgresOrderRepository(db)
    correlation_id = getattr(request.state, "correlation_id", "")
    return OrderService(repo, users_base_url=USERS_BASE_URL, correlation_id=correlation_id)


def _to_response(order) -> OrderResponse:
    return OrderResponse(
        id=order.id,
        customer_name=order.customer_name,
        item_name=order.item_name,
        quantity=order.quantity,
        price=order.price,
        total=order.total,
        status=order.status,
        owner_user_id=order.owner_user_id,
    )


@router.post("/core-items", response_model=OrderResponse, status_code=201)
def create_order(
    body: CreateOrderRequest,
    service: OrderService = Depends(get_service),
):
    logger.info("Creating order for customer: %s", body.customer_name)
    try:
        order = service.create_order(
            customer_name=body.customer_name,
            item_name=body.item_name,
            quantity=body.quantity,
            price=body.price,
            owner_user_id=body.owner_user_id,
        )
        return _to_response(order)
    except UserValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except UsersServiceUnavailable as e:
        raise HTTPException(status_code=503, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))


@router.get("/core-items/{order_id}", response_model=OrderResponse)
def get_order(
    order_id: UUID,
    service: OrderService = Depends(get_service),
):
    order = service.get_order(order_id)
    if order is None:
        raise HTTPException(status_code=404, detail="Order was not found!")
    return _to_response(order)


@router.patch("/core-items/{order_id}/status", response_model=OrderResponse)
def update_status(
    order_id: UUID,
    body: UpdateStatusRequest,
    service: OrderService = Depends(get_service),
):
    logger.info("Updating order %s to status %s", order_id, body.status)
    try:
        order = service.update_order_status(order_id, body.status)
        return _to_response(order)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
