import pytest
from typing import Dict, Optional
from uuid import UUID, uuid4

from fastapi.testclient import TestClient

from app.api.orders import get_service
from app.core.application import OrderService
from app.core.domain import Order
from app.main import app


class InMemoryOrderRepository:
    def __init__(self):
        self._storage: Dict[UUID, Order] = {}

    def save(self, order: Order) -> None:
        self._storage[order.id] = order

    def get_by_id(self, order_id: UUID) -> Optional[Order]:
        return self._storage.get(order_id)


@pytest.fixture
def client():
    repo = InMemoryOrderRepository()
    service = OrderService(repo)

    def override_get_service():
        return service

    app.dependency_overrides[get_service] = override_get_service
    yield TestClient(app)
    app.dependency_overrides.clear()


def test_health(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_create_order(client):
    response = client.post(
        "/core-items",
        json={
            "customer_name": "Sofiia",
            "item_name": "Salad",
            "quantity": 1,
            "price": 150.50,
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["customer_name"] == "Sofiia"
    assert data["item_name"] == "Salad"
    assert data["status"] == "created"
    assert data["total"] == 150.50


def test_get_order(client):
    create_response = client.post(
        "/core-items",
        json={"customer_name": "Max", "item_name": "Pasta", "quantity": 2, "price": 130.0},
    )
    order_id = create_response.json()["id"]

    get_response = client.get(f"/core-items/{order_id}")
    assert get_response.status_code == 200
    assert get_response.json()["id"] == order_id
    assert get_response.json()["total"] == 260.0


def test_get_order_not_found(client):
    response = client.get(f"/core-items/{uuid4()}")
    assert response.status_code == 404


def test_update_order_status(client):
    create_response = client.post(
        "/core-items",
        json={"customer_name": "Sasha", "item_name": "Pizza", "quantity": 1, "price": 200.0},
    )
    order_id = create_response.json()["id"]

    patch_response = client.patch(
        f"/core-items/{order_id}/status", json={"status": "pending"}
    )
    assert patch_response.status_code == 200
    assert patch_response.json()["status"] == "pending"


def test_update_order_status_invalid_transition(client):
    create_response = client.post(
        "/core-items",
        json={"customer_name": "Lena", "item_name": "Soup", "quantity": 1, "price": 55.0},
    )
    order_id = create_response.json()["id"]

    # CREATED -> DELIVERED is not allowed
    patch_response = client.patch(
        f"/core-items/{order_id}/status", json={"status": "delivered"}
    )
    assert patch_response.status_code == 422


def test_create_order_invalid_empty_customer(client):
    response = client.post(
        "/core-items",
        json={"customer_name": " ", "item_name": "Salad", "quantity": 1, "price": 150.50},
    )
    assert response.status_code == 422


def test_create_order_invalid_negative_price(client):
    response = client.post(
        "/core-items",
        json={"customer_name": "Alice", "item_name": "Juice", "quantity": 1, "price": -1.0},
    )
    assert response.status_code == 422


def test_create_order_invalid_zero_quantity(client):
    response = client.post(
        "/core-items",
        json={"customer_name": "Alice", "item_name": "Juice", "quantity": 0, "price": 10.0},
    )
    assert response.status_code == 422
