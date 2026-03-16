import logging
from uuid import UUID

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.application import UserService
from app.core.infrastructure import PostgresUserRepository, get_db

logger = logging.getLogger(__name__)
router = APIRouter()


class CreateUserRequest(BaseModel):
    display_name: str


class UserResponse(BaseModel):
    id: UUID
    display_name: str

    model_config = {"from_attributes": True}


def get_service(db: Session = Depends(get_db)) -> UserService:
    return UserService(PostgresUserRepository(db))


@router.post("/users", response_model=UserResponse, status_code=201)
def create_user(body: CreateUserRequest, service: UserService = Depends(get_service)):
    logger.info("Creating user: %s", body.display_name)
    try:
        user = service.create_user(display_name=body.display_name)
        return UserResponse(id=user.id, display_name=user.display_name)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))


@router.get("/users/{user_id}", response_model=UserResponse)
def get_user(user_id: UUID, service: UserService = Depends(get_service)):
    user = service.get_user(user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return UserResponse(id=user.id, display_name=user.display_name)
