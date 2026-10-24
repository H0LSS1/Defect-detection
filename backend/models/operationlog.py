"""操作日志表: 记录"谁在什么时候干了什么", 用于审计追溯.

和业务表的区别: 日志只追加、不修改不删除, 用户被删后日志仍保留
(外键 ON DELETE SET NULL, user_id 变 NULL 但日志行还在).
"""

from sqlalchemy import BigInteger, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from models.base import Base


class OperationLog(Base):
    """operation_logs 表: 一行 = 一次用户操作."""

    # 操作人: 用户被删时置为 NULL(SET NULL), 日志本身保留
    user_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )

    # 动作标识: login / create_task / export_report 等, 英文小写下划线
    action: Mapped[str] = mapped_column(String(50), nullable=False)

    # 操作对象: 类型(task/image/report) + 对象 id, 组合起来定位到具体目标
    target_type: Mapped[str | None] = mapped_column(String(30), nullable=True)
    target_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)

    # 补充说明(如 "导出了 11 个缺陷的报告")
    detail: Mapped[str | None] = mapped_column(String(500), nullable=True)

    # 客户端 IP; VARCHAR(45) 是 IPv6 的最大长度(IPv4 只要 15)
    ip: Mapped[str | None] = mapped_column(String(45), nullable=True)

    __tablename__ = "operation_logs"
