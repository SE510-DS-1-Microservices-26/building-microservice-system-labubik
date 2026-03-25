import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+psycopg://postgres:postgres@localhost:5432/workflow_db",
)


class Base(DeclarativeBase):
    pass


def get_engine():
    return create_engine(DATABASE_URL)


engine = get_engine()


def get_db():
    Session = sessionmaker(bind=engine, autocommit=False)
    with Session() as db:
        yield db
