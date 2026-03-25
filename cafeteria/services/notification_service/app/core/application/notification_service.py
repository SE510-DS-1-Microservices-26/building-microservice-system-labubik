import logging
from app.core.application.interfaces import NotificationRepository
from app.core.domain import Notification

logger = logging.getLogger(__name__)


class NotificationService:
    def __init__(self, repository: NotificationRepository):
        self.repository = repository

    def handle(self, notification: Notification) -> None:
        inserted = self.repository.save(notification)
        if inserted:
            logger.info(
                "Stored notification event_id=%s core_item_id=%s",
                notification.event_id,
                notification.core_item_id,
            )
        else:
            logger.info(
                "Duplicate event_id=%s — ignored", notification.event_id
            )
