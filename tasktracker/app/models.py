from app.database import Base
from sqlalchemy import Column, Integer, String, Enum as EnumColumn, ForeignKey, DateTime
from enum import Enum
import datetime
import uuid


class Account(Base):
    __tablename__ = "accounts"

    id = Column(Integer, primary_key=True, index=True)
    public_id = Column(String(50), unique=True, index=True, default=uuid.uuid4)
    username = Column(String(50), unique=True, index=True)
    email = Column(String(50), unique=True, index=True, nullable=True)
    role = Column(String(50))
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(
        DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow
    )


class Status(Enum):
    CREATED = "created"
    ASSIGNED = "assigned"
    COMPLETED = "completed"


class Task(Base):
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, index=True)
    public_id = Column(String(50), unique=True, index=True, default=uuid.uuid4)
    title = Column(String(255))
    description = Column(String(100))
    account_id = Column(Integer)
    assigned_to = Column(Integer)
    status = Column(EnumColumn(Status), default=Status.CREATED)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    foreign_key = Column(Integer, ForeignKey("accounts.id"))


class AuthIdentity(Base):
    __tablename__ = "auth_identities"

    id = Column(Integer, primary_key=True, index=True)
    account_id = Column(Integer)
    token = Column(String(255), index=True, unique=True)
    expires_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(
        DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow
    )
