from datetime import datetime
from enum import Enum
from uuid import UUID, uuid4


class OrderStatus(str, Enum):
    CREATED = "created"
    PENDING = "pending"
    CANCELLED = "cancelled"
    CONFIRMED = "confirmed"


class Order:
    def __init__(self, customer_name: str, item_name: str, quantity: int, price: float):
        if not customer_name or not customer_name.strip():
            raise ValueError("Customer name cannot be empty!")
        if quantity <= 0:
            raise ValueError("Quantity must be positive!")
        if price <= 0:
            raise ValueError("Price must be positive!")

        self.id: UUID = uuid4()
        self.customer_name: str = customer_name.strip()
        self.item_name: str = item_name.strip()
        self.quantity: int = quantity
        self.price: float = price
        self.status: OrderStatus = OrderStatus.CREATED
        self.created_at: datetime = datetime.utcnow()

    def start_processing(self):
        if self.status != OrderStatus.CREATED:
            raise ValueError("Order was already processed!")
        self.status = OrderStatus.PENDING

    def confirm(self):
        if self.status != OrderStatus.PENDING:
            raise ValueError(f"Cannot confirm order with status '{self.status}'")
        self.status = OrderStatus.CONFIRMED

    def cancel(self):
        if self.status == OrderStatus.CANCELLED:
            raise ValueError("Order was already cancelled!")
        self.status = OrderStatus.CANCELLED

    def change_status(self, new_status: OrderStatus):
        if new_status == OrderStatus.PENDING:
            self.start_processing()
        elif new_status == OrderStatus.CONFIRMED:
            self.confirm()
        elif new_status == OrderStatus.CANCELLED:
            self.cancel()
        else:
            raise ValueError(f"Cannot change status to '{new_status}'")

    @property
    def total(self) -> float:
        return self.quantity * self.price
