import pytest
from app.core.domain import Order, OrderStatus
from app.core.application import OrderService
from app.core.application.interfaces import OrderRepository
from typing import Dict, Optional
from uuid import UUID, uuid4


class InMemoryOrderRepository(OrderRepository):
    def __init__(self):
        self._storage: Dict[UUID, Order] = {}

    def save(self, order: Order) -> None:
        self._storage[order.id] = order

    def get_by_id(self, order_id: UUID) -> Optional[Order]:
        return self._storage.get(order_id)


def order_service():
    return OrderService(InMemoryOrderRepository())


def test_create_order_returns_order_with_created_status():
    service = order_service()
    order = service.create_order("Sofiia", "Salad", 1, 150.50)
    assert order.status == OrderStatus.CREATED


def test_create_order_saves_to_repository():
    repository = InMemoryOrderRepository()
    service = OrderService(repository)
    order = service.create_order("Sofiia", "Salad", 1, 150.50)
    assert repository.get_by_id(order.id) is not None


def test_get_order_returns_existing_order():
    service = order_service()
    order = service.create_order("Max", "Pasta", 2, 130.0)
    result = service.get_order(order.id)
    assert result is not None
    assert result.customer_name == "Max"


def test_get_order_returns_none_if_not_found():
    service = order_service()
    result = service.get_order(uuid4())
    assert result is None


def test_update_order_status_to_pending():
    service = order_service()
    order = service.create_order("Sasha", "Pizza", 1, 200.0)
    result = service.update_order_status(order.id, OrderStatus.PENDING)
    assert result.status == OrderStatus.PENDING


def test_update_order_status_raises_if_order_not_found():
    service = order_service()
    with pytest.raises(ValueError, match="was not found!"): service.update_order_status(uuid4(), OrderStatus.PENDING)
