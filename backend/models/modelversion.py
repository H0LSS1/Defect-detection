from models.base import Base
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String
from sqlalchemy import SmallInteger


class ModelVersion(Base):
    modelname : Mapped[str] = mapped_column(String(50), nullable=False)
    file_path : Mapped[str] = mapped_column(String(100), nullable=False)
    classess_count : Mapped[int] = mapped_column(SmallInteger,nullable=False)
    input_size: Mapped[int] = mapped_column(SmallInteger,nullable=False,default=640)
    is_active: Mapped[bool] = mapped_column(nullable=False,default=True)
    remark : Mapped[str | None] = mapped_column(String(100),nullable=True)

    __tablename__ = "model_versions"