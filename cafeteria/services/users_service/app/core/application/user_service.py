from typing import Optional
from uuid import UUID

from app.core.application.interfaces import UserRepository
from app.core.domain import User


class UserService:
    def __init__(self, repository: UserRepository):
        self.repository = repository

    def create_user(self, display_name: str) -> User:
        user = User(display_name=display_name)
        self.repository.save(user)
        return user

    def get_user(self, user_id: UUID) -> Optional[User]:
        return self.repository.get_by_id(user_id)
