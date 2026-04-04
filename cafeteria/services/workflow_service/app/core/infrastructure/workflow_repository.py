import json
from datetime import datetime
from typing import Optional
from uuid import uuid4, UUID

from sqlalchemy import Column, String, DateTime, Text, Enum as SAEnum
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Session

from app.core.domain import WorkflowInstance, WorkflowState, WorkflowType
from app.core.infrastructure.database import Base


class WorkflowModel(Base):
    __tablename__ = "workflow_instances"

    workflow_id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    type = Column(String, nullable=False)
    state = Column(
        SAEnum(
            WorkflowState,
            values_callable=lambda x: [e.value for e in x],
            name="workflowstate",
            create_type=False,
        ),
        nullable=False,
    )
    payload = Column(Text, nullable=False, default="{}")
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    last_error = Column(Text, nullable=True)


class PostgresWorkflowRepository:
    def __init__(self, session: Session):
        self.session = session

    def save(self, workflow: WorkflowInstance) -> None:
        existing = self.session.get(WorkflowModel, workflow.workflow_id)
        if existing:
            existing.state = workflow.state
            existing.payload = json.dumps(workflow.payload, default=str)
            existing.updated_at = workflow.updated_at
            existing.last_error = workflow.last_error
        else:
            self.session.add(
                WorkflowModel(
                    workflow_id=workflow.workflow_id,
                    type=workflow.type.value,
                    state=workflow.state,
                    payload=json.dumps(workflow.payload, default=str),
                    created_at=workflow.created_at,
                    updated_at=workflow.updated_at,
                    last_error=workflow.last_error,
                )
            )
        self.session.commit()

    def get_by_id(self, workflow_id: UUID) -> Optional[WorkflowInstance]:
        row = self.session.get(WorkflowModel, workflow_id)
        if row is None:
            return None
        wf = WorkflowInstance.__new__(WorkflowInstance)
        wf.workflow_id = row.workflow_id
        wf.type = WorkflowType(row.type)
        wf.state = row.state
        wf.payload = json.loads(row.payload)
        wf.created_at = row.created_at
        wf.updated_at = row.updated_at
        wf.last_error = row.last_error
        return wf
