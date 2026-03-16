from typing import Optional, Protocol
from uuid import UUID
from app.core.domain import User


class UserRepository(Protocol):
    def save(self, user: User) -> None: ...
    def get_by_id(self, user_id: UUID) -> Optional[User]: ...
