from datetime import datetime
from typing import Optional
from uuid import uuid4, UUID

from app.core.domain import Order, OrderStatus
from app.core.infrastructure.database import Base
from sqlalchemy import Column, String, Integer, Float, DateTime, Enum as SAEnum
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Session


class OrderModel(Base):
    __tablename__ = "orders"
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    customer_name = Column(String, nullable=False)
    item_name = Column(String, nullable=False)
    quantity = Column(Integer, nullable=False)
    price = Column(Float, nullable=False)
    owner_user_id = Column(PGUUID(as_uuid=True), nullable=False)
    status = Column(
        SAEnum(
            OrderStatus,
            values_callable=lambda x: [e.value for e in x],
            name="orderstatus",
            create_type=False,
        ),
        nullable=False,
        default=OrderStatus.CREATED,
    )
    created_at = Column(DateTime, default=datetime.utcnow)


class PostgresOrderRepository:
    def __init__(self, session: Session):
        self.session = session

    def save(self, order: Order) -> None:
        existing = self.session.get(OrderModel, order.id)
        if existing:
            existing.status = order.status
            existing.quantity = order.quantity
        else:
            db_order = OrderModel(
                id=order.id,
                customer_name=order.customer_name,
                item_name=order.item_name,
                quantity=order.quantity,
                price=order.price,
                owner_user_id=order.owner_user_id,
                status=order.status,
                created_at=order.created_at,
            )
            self.session.add(db_order)
        self.session.commit()

    def get_by_id(self, order_id: UUID) -> Optional[Order]:
        db_order = self.session.get(OrderModel, order_id)
        if db_order is None:
            return None
        order = Order.__new__(Order)
        order.id = db_order.id
        order.customer_name = db_order.customer_name
        order.item_name = db_order.item_name
        order.quantity = db_order.quantity
        order.price = db_order.price
        order.owner_user_id = db_order.owner_user_id
        order.status = db_order.status
        order.created_at = db_order.created_at
        return order
