"""模型版本表: 登记"平台用过哪些检测权重", 让每次检测可追溯.

为什么需要这张表:
    tasks 表的每一行都有 model_id 外键指向这里,
    这样任意一条历史任务都能回答"当时是用哪个权重、什么参数跑的".
    如果不登记, 三个月后没人记得某批结果是 yolov8n 还是别的模型出的.
"""

from sqlalchemy import String, SmallInteger
from sqlalchemy.orm import Mapped, mapped_column

from models.base import Base


class ModelVersion(Base):
    """model_versions 表: 一行 = 一个登记在册的权重文件."""

    # 权重名称, 如 yolov8n
    modelname: Mapped[str] = mapped_column(String(50), nullable=False)

    # 权重文件路径(相对 backend/ 目录), 如 weights/yolov8n.pt
    file_path: Mapped[str] = mapped_column(String(100), nullable=False)

    # 模型类别数(yolov8n 预训练是 COCO 80 类)
    classess_count: Mapped[int] = mapped_column(SmallInteger, nullable=False)

    # 推理时输入图片的边长, YOLO 系列默认 640x640
    input_size: Mapped[int] = mapped_column(SmallInteger, nullable=False, default=640)

    # 是否当前可用: 任务创建时只允许选 is_active=True 的权重
    is_active: Mapped[bool] = mapped_column(nullable=False, default=True)

    # 备注(如 "COCO 预训练权重")
    remark: Mapped[str | None] = mapped_column(String(100), nullable=True)

    __tablename__ = "model_versions"

    # id / created_at / updated_at 三个字段继承自 models/base.py 的 Base,
    # 这里不用重复写.
