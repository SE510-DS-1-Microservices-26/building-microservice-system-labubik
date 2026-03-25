import json
import logging
from datetime import datetime
from typing import Optional
from uuid import UUID

from sqlalchemy import Column, String, DateTime, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.domain import Notification
from app.core.infrastructure.database import Base

logger = logging.getLogger(__name__)


class NotificationModel(Base):
    __tablename__ = "notifications"

    event_id = Column(PGUUID(as_uuid=True), primary_key=True)
    correlation_id = Column(String, nullable=False)
    core_item_id = Column(PGUUID(as_uuid=True), nullable=False)
    owner_user_id = Column(PGUUID(as_uuid=True), nullable=False)
    summary = Column(String, nullable=False)
    payload = Column(Text, nullable=False)
    received_at = Column(DateTime, nullable=False, default=datetime.utcnow)


class PostgresNotificationRepository:
    def __init__(self, session: Session):
        self.session = session

    def save(self, notification: Notification) -> bool:
        record = NotificationModel(
            event_id=notification.event_id,
            correlation_id=notification.correlation_id,
            core_item_id=notification.core_item_id,
            owner_user_id=notification.owner_user_id,
            summary=notification.summary,
            payload=json.dumps(notification.payload, default=str),
            received_at=notification.received_at,
        )
        try:
            self.session.add(record)
            self.session.commit()
            return True
        except IntegrityError:
            self.session.rollback()
            logger.debug("IntegrityError on event_id=%s — duplicate ignored", notification.event_id)
            return False
