import logging
from uuid import UUID
from typing import Optional

import httpx

from app.core.application.interfaces import OrderRepository
from app.core.domain import Order, OrderStatus

logger = logging.getLogger(__name__)


class UserValidationError(Exception):
    """Raised when the owner user does not exist (404 from Users service)."""
    pass


class UsersServiceUnavailable(Exception):
    """Raised when the Users service is unreachable or times out."""
    pass


class OrderService:
    def __init__(self, repository: OrderRepository, users_base_url: str = ""):
        self.repository = repository
        self.users_base_url = users_base_url.rstrip("/")

    def _validate_user(self, owner_user_id: UUID) -> None:
        if not self.users_base_url:
            return
        url = f"{self.users_base_url}/users/{owner_user_id}"
        try:
            response = httpx.get(url, timeout=5.0)
        except (httpx.TimeoutException, httpx.ConnectError) as exc:
            logger.error("Users service unreachable: %s", exc)
            raise UsersServiceUnavailable("Users service is unavailable") from exc
        if response.status_code == 404:
            raise UserValidationError(f"User {owner_user_id} does not exist")
        if response.status_code != 200:
            logger.error("Unexpected response from Users service: %s", response.status_code)
            raise UsersServiceUnavailable(
                f"Users service returned unexpected status {response.status_code}"
            )

    def create_order(
        self,
        customer_name: str,
        item_name: str,
        quantity: int,
        price: float,
        owner_user_id: UUID,
    ) -> Order:
        self._validate_user(owner_user_id)
        order = Order(
            customer_name=customer_name,
            item_name=item_name,
            quantity=quantity,
            price=price,
            owner_user_id=owner_user_id,
        )
        self.repository.save(order)
        return order

    def get_order(self, order_id: UUID) -> Optional[Order]:
        return self.repository.get_by_id(order_id)

    def update_order_status(self, order_id: UUID, new_status: OrderStatus) -> Order:
        order = self.repository.get_by_id(order_id)
        if order is None:
            raise ValueError(f"Order {order_id} was not found!")
        order.change_status(new_status)
        self.repository.save(order)
        return order
