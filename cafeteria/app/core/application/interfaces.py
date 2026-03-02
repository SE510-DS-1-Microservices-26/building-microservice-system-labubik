from typing import Optional
from uuid import UUID
from abc import ABC, abstractmethod
from app.core.domain import Order


class OrderRepository(ABC):
    @abstractmethod
    def save(self, order: Order) -> None:
        pass

    @abstractmethod
    def get_by_id(self, order_id: UUID) -> Optional[Order]:
        pass
