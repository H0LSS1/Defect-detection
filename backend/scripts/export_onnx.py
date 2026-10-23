from ultralytics import YOLO
import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_DIR))
from app.core.config import settings


def export_yolo_onnx():
    weights_path = BACKEND_DIR / settings.yolo_weights
    if not weights_path.exists():
        raise FileNotFoundError(f"权重文件不存在：{weights_path}")

    model = YOLO(str(weights_path))
    print(f"成功加载权重: {weights_path}")

    out_files = model.export(format="onnx", imgsz=640, simplify=True, dynamic=True)
    print(f"ONNX导出完成，输出：{out_files}")
    return out_files


if __name__ == "__main__":
    out = export_yolo_onnx()
    print("exists:", Path(out).exists())
