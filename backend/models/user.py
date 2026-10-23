from models.base import Base
from sqlalchemy.orm import Mapped, mapped_column
from enum import Enum
from datetime import datetime
from sqlalchemy import String
from sqlalchemy.types import DateTime

class UserRole(str, Enum):
    inspector = "inspector"
    admin = "admin"

class User(Base):
    username: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    real_name: Mapped[str] = mapped_column(String(100), nullable=True)
    role : Mapped[UserRole] = mapped_column(nullable=False, default=UserRole.inspector)
    email: Mapped[str] = mapped_column(String(100), unique=True, nullable=True)
    last_login: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    status: Mapped[bool] = mapped_column(nullable=False, default=True)

    __tablename__ = "users"