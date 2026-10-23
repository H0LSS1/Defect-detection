from models.base import Base
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String, ForeignKey, BigInteger


class OperationLog(Base):
    user_id : Mapped[int | None] = mapped_column(BigInteger, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    action : Mapped[str] = mapped_column(String(50), nullable=False)
    target_type : Mapped[str | None] = mapped_column(String(30), nullable=True)
    target_id : Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    detail : Mapped[str | None] = mapped_column(String(500), nullable=True)
    ip : Mapped[str | None] = mapped_column(String(45), nullable=True)

    __tablename__ = "operation_logs"
