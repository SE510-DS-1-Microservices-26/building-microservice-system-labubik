from typing import Optional, Protocol
from uuid import UUID

from app.core.domain import WorkflowInstance


class WorkflowRepository(Protocol):
    def save(self, workflow: WorkflowInstance) -> None: ...
    def get_by_id(self, workflow_id: UUID) -> Optional[WorkflowInstance]: ...
