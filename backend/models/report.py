"""报告表: 每次"导出检测报告"动作的记录.

报告本体是 results/{task_no}/report/ 下的 .docx 文件,
这张表只记录"谁在什么时候导出了哪份报告"以及关键指标快照.
"""

from enum import Enum

from sqlalchemy import BigInteger, Enum as SAEnum, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from models.base import Base


class ReportFormat(str, Enum):
    """报告格式, 目前支持 Word; 以后可扩展 pdf."""

    docx = "docx"
    pdf = "pdf"


class Report(Base):
    """reports 表: 一行 = 一次报告导出记录."""

    # 属于哪个任务、谁导出的
    task_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("tasks.id"), nullable=False, index=True
    )
    user_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("users.id"), nullable=False
    )

    # 报告文件路径(相对 backend/)
    file_path: Mapped[str] = mapped_column(String(255), nullable=False)

    # 格式(docx/pdf); 派发列名 file_format 是因为 format 是 Python 内置名, 避开混淆
    file_format: Mapped[ReportFormat] = mapped_column(
        nullable=False, default=ReportFormat.docx
    )

    # 文件大小(字节)
    file_size: Mapped[int] = mapped_column(nullable=False)

    # 导出时的缺陷框总数(快照): 之后任务数据变了, 报告内容不变 —— 报告是"历史定格"
    defect_count: Mapped[int] = mapped_column(nullable=False, default=0)

    __tablename__ = "reports"
