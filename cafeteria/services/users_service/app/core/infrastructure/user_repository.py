from typing import Optional
from uuid import uuid4, UUID

from app.core.domain import User
from app.core.infrastructure.database import Base
from sqlalchemy import Column, String
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Session


class UserModel(Base):
    __tablename__ = "users"
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    display_name = Column(String, nullable=False)


class PostgresUserRepository:
    def __init__(self, session: Session):
        self.session = session

    def save(self, user: User) -> None:
        existing = self.session.get(UserModel, user.id)
        if existing:
            existing.display_name = user.display_name
        else:
            self.session.add(UserModel(id=user.id, display_name=user.display_name))
        self.session.commit()

    def get_by_id(self, user_id: UUID) -> Optional[User]:
        db_user = self.session.get(UserModel, user_id)
        if db_user is None:
            return None
        u = User.__new__(User)
        u.id = db_user.id
        u.display_name = db_user.display_name
        return u
