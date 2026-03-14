import logging

from fastapi import APIRouter, HTTPException
from fastapi.params import Depends
from pydantic import BaseModel
from uuid import UUID

from sqlalchemy.orm import Session

from app.core.application import OrderService
from app.core.domain import OrderStatus
from app.core.infrastructure import PostgresOrderRepository, get_db

logger = logging.getLogger(__name__)
router = APIRouter()


class CreateOrderRequest(BaseModel):
    customer_name: str
    item_name: str
    quantity: int
    price: float


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

    model_config = {"from_attributes": True}


def get_service(db: Session = Depends(get_db)) -> OrderService:
    repo = PostgresOrderRepository(db)
    return OrderService(repo)


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
        )
        return OrderResponse(
            id=order.id,
            customer_name=order.customer_name,
            item_name=order.item_name,
            quantity=order.quantity,
            price=order.price,
            total=order.total,
            status=order.status,
        )
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
    return OrderResponse(
        id=order.id,
        customer_name=order.customer_name,
        item_name=order.item_name,
        quantity=order.quantity,
        price=order.price,
        total=order.total,
        status=order.status,
    )


@router.patch("/core-items/{order_id}/status", response_model=OrderResponse)
def update_status(
    order_id: UUID,
    body: UpdateStatusRequest,
    service: OrderService = Depends(get_service),
):
    logger.info("Updating order %s to status %s", order_id, body.status)
    try:
        order = service.update_order_status(order_id, body.status)
        return OrderResponse(
            id=order.id,
            customer_name=order.customer_name,
            item_name=order.item_name,
            quantity=order.quantity,
            price=order.price,
            total=order.total,
            status=order.status,
        )
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
