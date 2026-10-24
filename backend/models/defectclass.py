"""缺陷类别字典表: "模型输出的类别名 -> 界面展示名/颜色" 的映射.

为什么需要它:
    换上焊缝权重后, 模型输出的是英文类别(porosity/crack/slag_inclusion),
    前端界面要显示中文(气孔/裂纹/夹渣), 画框还要用统一颜色.
    把映射关系放进数据库而不是写死在前端, 以后换模型/改配色就不用动代码.
"""

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from models.base import Base


class DefectClass(Base):
    """defect_classes 表: 一行 = 一种缺陷类别的展示配置."""

    # 模型输出的原始类别名, 唯一
    class_name: Mapped[str] = mapped_column(String(50), nullable=False, unique=True)

    # 界面展示名(中文), 统计看板/图例/报告都取这个
    display_name: Mapped[str] = mapped_column(String(50), nullable=False)

    # 画框颜色, 格式 "#RRGGBB", 如 "#FF5733"
    color: Mapped[str] = mapped_column(String(50), nullable=True)

    # 是否参与统计: 预训练阶段先插了 3 个焊缝类别占位(is_enabled=False),
    # 等真正换上焊缝权重再启用
    is_enabled: Mapped[bool] = mapped_column(nullable=False, default=True)

    __tablename__ = "defect_classes"
