from models.base import Base
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String, ForeignKey, SmallInteger, BigInteger
from sqlalchemy.types import DateTime
from datetime import datetime
from enum import Enum


class ImageStatus(str, Enum):
    uploaded = "uploaded"
    enhancing = "enhancing"
    detecting = "detecting"
    done = "done"
    failed = "failed"


class Image(Base):
    task_id : Mapped[int] = mapped_column(BigInteger, ForeignKey("tasks.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id : Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id"), nullable=False)
    original_path : Mapped[str] = mapped_column(String(255), nullable=False)
    enhanced_path : Mapped[str | None] = mapped_column(String(255), nullable=True)
    filename : Mapped[str] = mapped_column(String(255), nullable=False)
    file_size : Mapped[int] = mapped_column(nullable=False)
    width : Mapped[int | None] = mapped_column(SmallInteger, nullable=True)
    height : Mapped[int | None] = mapped_column(SmallInteger, nullable=True)
    format : Mapped[str | None] = mapped_column(String(10), nullable=True)
    status : Mapped[ImageStatus] = mapped_column(nullable=False, default=ImageStatus.uploaded)
    inference_time_ms : Mapped[int | None] = mapped_column(nullable=True)

    __tablename__ = "images"
