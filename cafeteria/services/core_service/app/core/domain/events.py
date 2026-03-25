from datetime import datetime, timezone
from uuid import UUID, uuid4
from pydantic import BaseModel, Field


class CoreItemCreatedEvent(BaseModel):
    event_id: UUID = Field(default_factory=uuid4)
    occurred_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    correlation_id: str
    core_item_id: UUID
    owner_user_id: UUID
    summary: str
