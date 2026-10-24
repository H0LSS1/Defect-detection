"""任务相关表: tasks(检测任务主表).

一次检测任务 = 用户上传的一批图片 + 一个置信度阈值 + 一个模型版本.
任务的生命周期(状态机):
    pending(已创建排队) → running(worker 正在逐张处理)
      → completed(全部处理完) / failed(整体出错)
进度查看: completed_images / total_images, 前端轮询这两个字段.
"""

from datetime import datetime
from enum import Enum

from sqlalchemy import BigInteger, DateTime, ForeignKey, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from models.base import Base


class TaskStatus(str, Enum):
    """任务状态枚举, 与前端/进度接口约定好的一致."""

    pending = "pending"        # 已创建, 还没被 worker 领取
    running = "running"        # worker 处理中
    completed = "completed"    # 全部图片处理完成
    failed = "failed"          # 整体失败(error_message 记录原因)


class Task(Base):
    """tasks 表: 一行 = 一次检测任务."""

    # 对外任务号: 返回给前端/出现在报告上的编号(如 TSK20261024135720075E).
    # 接口一律用 task_no 而不暴露自增 id, 防止外部猜库里的数据量.
    task_no: Mapped[str] = mapped_column(String(32), unique=True, nullable=False)

    # 任务名称, 用户上传时自己起的
    task_name: Mapped[str] = mapped_column(String(100), nullable=False)

    # 创建人: 外键 -> users.id; index=True 建索引, "查我的任务"是高频查询
    user_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("users.id"), nullable=False, index=True
    )

    # 用的哪个模型权重: 外键 -> model_versions.id, 保证结果可追溯
    model_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("model_versions.id"), nullable=False
    )

    # 任务状态(见上方状态机)
    status: Mapped[TaskStatus] = mapped_column(
        nullable=False, default=TaskStatus.pending, index=True
    )

    # 图片总数 / 已完成数 —— 进度 = completed_images / total_images
    total_images: Mapped[int] = mapped_column(nullable=False, default=0)
    completed_images: Mapped[int] = mapped_column(nullable=False, default=0)

    # 本次任务的置信度阈值(DECIMAL(4,3), 如 0.250).
    # 记在任务上而不是全局配置里, 是为了让结果可复现:
    # 半年前跑的任务用的什么阈值, 一查便知.
    confidence_threshold: Mapped[float] = mapped_column(
        Numeric(4, 3), nullable=False, default=0.25
    )

    # 失败原因(failed 时写入, 截断到 500 字符防超长)
    error_message: Mapped[str | None] = mapped_column(String(500), nullable=True)

    # 开始/结束时间(计耗时用)
    started_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    __tablename__ = "tasks"
