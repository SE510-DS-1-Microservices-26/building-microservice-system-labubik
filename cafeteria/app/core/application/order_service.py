from uuid import UUID
from typing import Optional
from app.core.application.interfaces import OrderRepository
from app.core.domain import Order, OrderStatus


class OrderService:
    def __init__(self, repository: OrderRepository):
        self.repository = repository

    def create_order(self, customer_name: str, item_name: str, quantity: int, price: float) -> Order:
        order = Order(
            customer_name=customer_name,
            item_name=item_name,
            quantity=quantity,
            price=price
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
