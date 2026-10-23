from models.base import Base
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String, ForeignKey, SmallInteger, Numeric, BigInteger


class DetectionResult(Base):
    image_id : Mapped[int] = mapped_column(BigInteger, ForeignKey("images.id", ondelete="CASCADE"), nullable=False, index=True)
    class_name : Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    class_id : Mapped[int] = mapped_column(SmallInteger, nullable=False)
    confidence : Mapped[float] = mapped_column(Numeric(5, 4), nullable=False, index=True)
    x1 : Mapped[int] = mapped_column(nullable=False)
    y1 : Mapped[int] = mapped_column(nullable=False)
    x2 : Mapped[int] = mapped_column(nullable=False)
    y2 : Mapped[int] = mapped_column(nullable=False)

    __tablename__ = "detection_results"
