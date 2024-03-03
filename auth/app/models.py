from enum import Enum
from app.database import Base
from sqlalchemy import Column, Integer, String, Boolean, Enum as EnumColumn
import uuid


class Role(str, Enum):
    ADMIN = "admin"
    WORKER = "worker"
    MANAGER = "manager"


class Account(Base):
    __tablename__ = "accounts"

    id = Column(Integer, primary_key=True, index=True)
    public_id = Column(String(50), unique=True, index=True, default=uuid.uuid4)
    username = Column(String(50), unique=True, index=True)
    encrypted_password = Column(String(100))
    full_name = Column(String(100))
    is_active = Column(Boolean, default=True)
    role = Column(EnumColumn(Role), default=Role.WORKER)
