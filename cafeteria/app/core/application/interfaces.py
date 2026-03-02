from typing import Optional, Protocol
from uuid import UUID
from app.core.domain import Order


class OrderRepository(Protocol):
    def save(self, order: Order) -> None: ...

    def get_by_id(self, order_id: UUID) -> Optional[Order]: ...
