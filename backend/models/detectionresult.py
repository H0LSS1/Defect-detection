"""检测结果表: 模型在每张图上检出的"一个框"一行记录.

关系: 一张图(images) → 多个框(detection_results), 典型的一对多.
例: bus.jpg 检出 4 个 person + 1 个 bus, 那就是 5 行记录.
"""

from sqlalchemy import ForeignKey, Numeric, SmallInteger, String, BigInteger
from sqlalchemy.orm import Mapped, mapped_column

from models.base import Base


class DetectionResult(Base):
    """detection_results 表: 一行 = 一个检测框."""

    # 属于哪张图: 删图时连带删框(ON DELETE CASCADE)
    image_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("images.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # 类别名(如 person; 焊缝权重则是 porosity 等), 按类别统计要建索引
    class_name: Mapped[str] = mapped_column(String(50), nullable=False, index=True)

    # 类别在模型输出里的数字编号(0~79, 与 class_name 一一对应)
    class_id: Mapped[int] = mapped_column(SmallInteger, nullable=False)

    # 置信度(模型认为"这里确实有目标"的把握程度, 0~1).
    # DECIMAL(5,4): 总 5 位小数 4 位, 精确存到 0.0001, 避免 float 精度误差.
    confidence: Mapped[float] = mapped_column(Numeric(5, 4), nullable=False, index=True)

    # 框的像素坐标: 左上角(x1,y1) 和 右下角(x2,y2).
    # 存像素坐标而不是归一化坐标, 因为图片宽高就在 images 表里, 能换算回来,
    # 而且画框时直接可用不用再乘图片尺寸.
    x1: Mapped[int] = mapped_column(nullable=False)
    y1: Mapped[int] = mapped_column(nullable=False)
    x2: Mapped[int] = mapped_column(nullable=False)
    y2: Mapped[int] = mapped_column(nullable=False)

    __tablename__ = "detection_results"
