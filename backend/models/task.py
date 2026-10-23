from models.base import Base
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String, ForeignKey, Numeric, BigInteger
from sqlalchemy.types import DateTime
from sqlalchemy.sql import func
from datetime import datetime
from enum import Enum


class TaskStatus(str, Enum):
    pending = "pending"
    running = "running"
    completed = "completed"
    failed = "failed"


class Task(Base):
    task_no : Mapped[str] = mapped_column(String(32), unique=True, nullable=False)
    task_name : Mapped[str] = mapped_column(String(100), nullable=False)
    user_id : Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id"), nullable=False, index=True)
    model_id : Mapped[int] = mapped_column(BigInteger, ForeignKey("model_versions.id"), nullable=False)
    status : Mapped[TaskStatus] = mapped_column(nullable=False, default=TaskStatus.pending, index=True)
    total_images : Mapped[int] = mapped_column(nullable=False, default=0)
    completed_images : Mapped[int] = mapped_column(nullable=False, default=0)
    confidence_threshold : Mapped[float] = mapped_column(Numeric(4, 3), nullable=False, default=0.25)
    error_message : Mapped[str | None] = mapped_column(String(500), nullable=True)
    started_at : Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    finished_at : Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    __tablename__ = "tasks"
