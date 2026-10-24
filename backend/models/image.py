"""图片表: 任务里的每一张图一行记录, 记录原图/增强图/标注图的"路径与状态".

路径设计约定(重要):
    - 数据库里存的是"相对 backend/ 目录"的路径(如 uploads/TSK.../original/xx.jpg),
      不存绝对路径 —— 换机器/换盘符时代码不用改;
    - 磁盘文件名用 uuid 随机生成, 用户上传的原始文件名(filename 列)只做展示:
      防止重名覆盖、防止路径里带中文或特殊字符、防止恶意构造的路径穿越.
"""

from datetime import datetime
from enum import Enum

from sqlalchemy import BigInteger, ForeignKey, SmallInteger, String
from sqlalchemy.orm import Mapped, mapped_column

from models.base import Base


class ImageStatus(str, Enum):
    """单张图的处理状态(注意: 这是"图片的状态", 任务整体状态在 tasks.status)."""

    uploaded = "uploaded"      # 已上传落盘, 还没被处理
    enhancing = "enhancing"    # 图像增强中
    detecting = "detecting"    # 模型推理中
    done = "done"              # 处理完成
    failed = "failed"          # 这张图处理失败(不影响任务里其他图)


class Image(Base):
    """images 表: 一行 = 任务里的一张图片."""

    # 属于哪个任务: 删任务时连带删掉图片记录(ON DELETE CASCADE)
    task_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("tasks.id", ondelete="CASCADE"), nullable=False, index=True
    )

    # 上传人
    user_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("users.id"), nullable=False
    )

    # 原始图路径(相对 backend/), 如 uploads/TSK.../original/xxxx.jpg
    original_path: Mapped[str] = mapped_column(String(255), nullable=False)

    # 增强图路径(worker 增强完回填), 展示"增强前后对比"用
    enhanced_path: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # 标注图路径(worker 画完缺陷框回填), 前端 <img> 直接展示检测结果
    annotated_path: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # 用户上传时的原始文件名(仅展示)
    filename: Mapped[str] = mapped_column(String(255), nullable=False)

    # 文件大小(字节)
    file_size: Mapped[int] = mapped_column(nullable=False)

    # 图片宽高(worker 读取图片后回填; SMALLINT 最大 32767px 足够)
    width: Mapped[int | None] = mapped_column(SmallInteger, nullable=True)
    height: Mapped[int | None] = mapped_column(SmallInteger, nullable=True)

    # 图片格式(jpg/png/...)
    format: Mapped[str | None] = mapped_column(String(10), nullable=True)

    # 单图状态
    status: Mapped[ImageStatus] = mapped_column(
        nullable=False, default=ImageStatus.uploaded
    )

    # 单图推理耗时(毫秒), 统计看板"平均推理耗时"的数据来源
    inference_time_ms: Mapped[int | None] = mapped_column(nullable=True)

    __tablename__ = "images"
