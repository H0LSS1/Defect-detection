"""把 .pt 权重导出成 ONNX 格式(一次性的模型格式转换脚本).

.pt 和 .onnx 的区别:
    .pt   : PyTorch 私有格式, 推理必须装 PyTorch(好几个 GB)
    .onnx : 开放交换格式, 用 ONNX Runtime 就能推理(轻量, CPU 上还更快)
本项目实测(见 backend/check/check_onnx.py): 检测结果零差异, 延迟 64ms → 32ms.

运行方式(在项目根目录):
    .venv\\Scripts\\python backend\\scripts\\export_onnx.py
导出产物: backend/weights/yolov8n.onnx(与 .pt 同目录同名)
"""
from pathlib import Path
import sys

# 路径处理必须放在"项目内 import"之前(backend/scripts 不在 Python 默认搜索路径里)
BACKEND_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_DIR))

from ultralytics import YOLO

from app.core.config import settings


def export_yolo_onnx():
    """把 settings.yolo_weights 指向的权重导出为 ONNX, 返回导出路径."""
    weights_path = BACKEND_DIR / settings.yolo_weights
    if not weights_path.exists():
        raise FileNotFoundError(f"权重文件不存在：{weights_path}")

    model = YOLO(str(weights_path))
    print(f"成功加载权重: {weights_path}")

    # export 参数说明:
    #   format="onnx"  目标格式
    #   imgsz=640      输入图片边长(与训练/推理一致)
    #   simplify=True  用 onnxslim 简化计算图(去掉冗余节点, 推理更快)
    #   dynamic=True   允许动态 batch/尺寸(推理时不再强制 640x640 固定输入)
    out_files = model.export(format="onnx", imgsz=640, simplify=True, dynamic=True)
    print(f"ONNX导出完成，输出：{out_files}")
    return out_files


# 直接运行本文件时执行导出; 被别的模块 import 时不触发
if __name__ == "__main__":
    out = export_yolo_onnx()
    print("exists:", Path(out).exists())
