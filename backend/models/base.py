from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func
from sqlalchemy.types import DateTime
from sqlalchemy import BigInteger
from datetime import datetime

class Base(DeclarativeBase):
    id : Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    created_at : Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at : Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())