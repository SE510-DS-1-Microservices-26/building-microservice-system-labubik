import logging
from uuid import UUID
from typing import Optional

import httpx
from tenacity import retry, stop_after_attempt, wait_fixed, retry_if_exception_type

from app.core.application.interfaces import OrderRepository
from app.core.domain import Order, OrderStatus

logger = logging.getLogger(__name__)


class UserValidationError(Exception):
    pass


class UsersServiceUnavailable(Exception):
    pass


class OrderService:
    def __init__(self, repository: OrderRepository, users_base_url: str = "", correlation_id: str = ""):
        self.repository = repository
        self.users_base_url = users_base_url
        self.correlation_id = correlation_id

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_fixed(1),
        retry=retry_if_exception_type(httpx.TransientError),
        reraise=True,
    )
    def _validate_user(self, user_id: UUID) -> None:
        if not self.users_base_url:
            return
        headers = {"X-Correlation-Id": self.correlation_id}
        try:
            with httpx.Client(timeout=5.0) as client:
                response = client.get(
                    f"{self.users_base_url}/users/{user_id}",
                    headers=headers,
                )
            if response.status_code == 404:
                raise UserValidationError(f"User {user_id} not found")
            response.raise_for_status()
            logger.info(
                "User %s validated",
                user_id,
                extra={"correlation_id": self.correlation_id},
            )
        except httpx.TimeoutException as exc:
            logger.error(
                "Timeout validating user %s: %s",
                user_id,
                exc,
                extra={"correlation_id": self.correlation_id},
            )
            raise UsersServiceUnavailable("Users service timed out") from exc
        except httpx.HTTPStatusError as exc:
            logger.error(
                "HTTP error validating user %s: %s",
                user_id,
                exc,
                extra={"correlation_id": self.correlation_id},
            )
            raise UsersServiceUnavailable("Users service unavailable") from exc

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
        logger.info(
            "Order %s created for customer %s",
            order.id,
            customer_name,
            extra={"correlation_id": self.correlation_id},
        )
        return order

    def get_order(self, order_id: UUID) -> Optional[Order]:
        return self.repository.get_by_id(order_id)

    def update_order_status(self, order_id: UUID, new_status: OrderStatus) -> Order:
        order = self.repository.get_by_id(order_id)
        if order is None:
            raise ValueError(f"Order {order_id} was not found!")
        order.change_status(new_status)
        self.repository.save(order)
        logger.info(
            "Order %s status updated to %s",
            order_id,
            new_status,
            extra={"correlation_id": self.correlation_id},
        )
        return order