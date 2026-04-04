from datetime import datetime
from enum import Enum
from typing import Optional
from uuid import UUID, uuid4


class WorkflowState(str, Enum):
    STARTED = "started"
    ORDER_CREATED = "order_created"
    ORDER_CONFIRMED = "order_confirmed"
    COMPLETED = "completed"
    COMPENSATING = "compensating"
    CANCELLED = "cancelled"
    FAILED = "failed"


class WorkflowType(str, Enum):
    PLACE_ORDER = "place-order"


class WorkflowInstance:
    def __init__(
        self,
        workflow_type: WorkflowType,
        payload: dict,
        workflow_id: Optional[UUID] = None,
    ):
        self.workflow_id: UUID = workflow_id or uuid4()
        self.type: WorkflowType = workflow_type
        self.state: WorkflowState = WorkflowState.STARTED
        self.payload: dict = payload
        self.created_at: datetime = datetime.utcnow()
        self.updated_at: datetime = datetime.utcnow()
        self.last_error: Optional[str] = None

    def transition(self, new_state: WorkflowState, error: Optional[str] = None) -> None:
        self.state = new_state
        self.updated_at = datetime.utcnow()
        self.last_error = error
