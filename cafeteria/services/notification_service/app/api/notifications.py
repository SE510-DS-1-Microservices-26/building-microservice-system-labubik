import logging
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.infrastructure import get_db
from app.core.infrastructure.notification_repository import NotificationModel

logger = logging.getLogger(__name__)
router = APIRouter()


class NotificationResponse(BaseModel):
    event_id: UUID
    correlation_id: str
    core_item_id: UUID
    owner_user_id: UUID
    summary: str
    payload: str
    received_at: str

    model_config = {"from_attributes": True}


@router.get("/notifications", response_model=list[NotificationResponse])
def list_notifications(db: Session = Depends(get_db)):
    records = db.query(NotificationModel).order_by(NotificationModel.received_at.desc()).all()
    return [
        NotificationResponse(
            event_id=r.event_id,
            correlation_id=r.correlation_id,
            core_item_id=r.core_item_id,
            owner_user_id=r.owner_user_id,
            summary=r.summary,
            payload=r.payload,
            received_at=str(r.received_at),
        )
        for r in records
    ]


@router.get("/notifications/{event_id}", response_model=NotificationResponse)
def get_notification(event_id: UUID, db: Session = Depends(get_db)):
    record = db.get(NotificationModel, event_id)
    if record is None:
        raise HTTPException(status_code=404, detail="Notification not found")
    return NotificationResponse(
        event_id=record.event_id,
        correlation_id=record.correlation_id,
        core_item_id=record.core_item_id,
        owner_user_id=record.owner_user_id,
        summary=record.summary,
        payload=record.payload,
        received_at=str(record.received_at),
    )
