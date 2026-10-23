from models.base import Base
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String

class DefectClass(Base):
    class_name : Mapped[str] = mapped_column(String(50), nullable=False,unique=True)
    color : Mapped[str] = mapped_column(String(50), nullable=True)
    display_name : Mapped[str] = mapped_column(String(50), nullable=False)
    is_enabled : Mapped[bool] = mapped_column(nullable=False,default=True)

    __tablename__ = "defect_classes"