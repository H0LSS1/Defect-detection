"""YOLO 检测器: 模型"常驻内存"的推理服务.

为什么要做成单例(全项目唯一实例):
    加载权重要 1~2 秒(读文件+初始化网络), 如果每个请求都 YOLO(...) 一次,
    每次都要白付这笔钱. 单例 = 只加载一次, 之后每次推理只花几十毫秒.
    实测(本项目): 第一次 1742ms, 第二次起 72ms.

使用规则: 其他代码一律通过 get_detector() 拿实例, 不要自己 new DefectDetector().
"""
from pathlib import Path

import numpy as np
from ultralytics import YOLO

from app.core.config import settings

# 模块级变量: 存放唯一的检测器实例, None 表示"还没创建"
_detector: "DefectDetector | None" = None


def get_detector() -> "DefectDetector":
    """懒加载单例入口: 第一次调用才真正加载模型, 之后返回同一实例."""
    global _detector
    if _detector is None:
        _detector = DefectDetector()
    return _detector


class DefectDetector:
    """封装 YOLO 模型: 加载 + 推理 + 把结果整理成好用的字典列表."""

    def __init__(self):
        # 权重路径从配置读(.env 的 YOLO_WEIGHTS, 可切 .pt/.onnx).
        # 定位层级: 本文件在 backend/app/services/ 下,
        #   parents[0]=services  parents[1]=app  parents[2]=backend
        # 所以 parents[2] / weights/xxx 才是真正的权重位置
        # (层级写错 ultralytics 会静默重新下载一份, 很难察觉).
        weights = Path(__file__).resolve().parents[2] / settings.yolo_weights
        self.model = YOLO(str(weights))

        # 类别映射表: {0: 'person', 1: 'bicycle', ...}
        # 模型输出的类别是数字 id, 用它翻译成可读的名字
        self.names = self.model.names

    def detect(self, img: np.ndarray, conf: float | None = None) -> list[dict]:
        """对一张图(BGR ndarray)做推理, 返回检测框列表.

        参数:
            img: 图像数组(调用方已做过增强), 不收文件路径 —— 避免多余磁盘IO
            conf: 本次推理的置信度阈值, 不传则用 settings.conf_threshold
        返回:
            [{"class_name","class_id","confidence","x1","y1","x2","y2"}, ...]
            字段与 detection_results 表一一对应, 方便直接入库.
        """
        # verbose=False: 关掉 ultralytics 每张图打印一行的日志
        results = self.model.predict(
            img, conf=conf or settings.conf_threshold, verbose=False
        )
        r = results[0]  # 单图输入时返回列表, 取第一个

        box_list = []
        for b in r.boxes:  # 每个检出的目标是一个 Box 对象
            # 坐标张量转 Python float 再取整(DB 是 INT 列)
            x1, y1, x2, y2 = (int(v) for v in b.xyxy[0].tolist())
            # 置信度 round 4 位(DB 是 DECIMAL(5,4))
            conf_score = round(float(b.conf[0]), 4)
            cls_id = int(b.cls[0])
            cls_name = r.names[cls_id]
            box_list.append(
                {
                    "x1": x1,
                    "y1": y1,
                    "x2": x2,
                    "y2": y2,
                    "confidence": conf_score,
                    "class_id": cls_id,
                    "class_name": cls_name,
                }
            )
        return box_list
