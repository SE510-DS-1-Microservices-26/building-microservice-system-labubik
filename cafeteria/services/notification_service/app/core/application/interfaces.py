from typing import Protocol
from app.core.domain import Notification


class NotificationRepository(Protocol):
    def save(self, notification: Notification) -> bool: ...
