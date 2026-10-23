from models.base import Base
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String, ForeignKey, BigInteger
from enum import Enum


class ReportFormat(str, Enum):
    docx = "docx"
    pdf = "pdf"


class Report(Base):
    task_id : Mapped[int] = mapped_column(BigInteger, ForeignKey("tasks.id"), nullable=False, index=True)
    user_id : Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id"), nullable=False)
    file_path : Mapped[str] = mapped_column(String(255), nullable=False)
    file_format : Mapped[ReportFormat] = mapped_column(nullable=False, default=ReportFormat.docx)
    file_size : Mapped[int] = mapped_column(nullable=False)
    defect_count : Mapped[int] = mapped_column(nullable=False, default=0)

    __tablename__ = "reports"
