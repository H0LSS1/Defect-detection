from pathlib import Path
from ultralytics import YOLO
import numpy as np

from app.core.config import settings

_detector: "DefectDetector | None" = None


def get_detector() -> "DefectDetector":
    global _detector
    if _detector is None:
        _detector = DefectDetector()
    return _detector


class DefectDetector:
    def __init__(self):
        weights = Path(__file__).resolve().parents[2] / settings.yolo_weights
        self.model = YOLO(str(weights))
        self.names = self.model.names

    def detect(self, img: np.ndarray, conf: float | None = None) -> list[dict]:
        results = self.model.predict(
            img, conf=conf or settings.conf_threshold, verbose=False
        )
        r = results[0]
        box_list = []
        for b in r.boxes:
            x1, y1, x2, y2 = (int(v) for v in b.xyxy[0].tolist())
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
