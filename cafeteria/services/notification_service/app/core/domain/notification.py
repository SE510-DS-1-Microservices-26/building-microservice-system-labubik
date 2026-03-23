from datetime import datetime
from typing import Optional
from uuid import UUID


class Notification:
    def __init__(
            self,
            event_id: UUID,
            correlation_id: str,
            core_item_id: UUID,
            owner_user_id: UUID,
            summary: str,
            payload: dict,
            received_at: Optional[datetime] = None,
    ):
        self.event_id = event_id
        self.correlation_id = correlation_id
        self.core_item_id = core_item_id
        self.owner_user_id = owner_user_id
        self.summary = summary
        self.payload = payload
        self.received_at = received_at or datetime.utcnow()
