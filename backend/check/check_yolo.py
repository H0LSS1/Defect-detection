"""YOLO smoke test: load pretrained yolov8n.pt, run inference on bundled sample image."""
import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[1]


def main() -> int:
    weights = BACKEND_DIR / "weights" / "yolov8n.pt"
    if not weights.exists():
        print(f"[FAIL] weights not found: {weights}")
        print("       download: https://github.com/ultralytics/assets/releases/download/v8.3.0/yolov8n.pt")
        return 1

    from ultralytics import YOLO
    import ultralytics

    model = YOLO(str(weights))
    names = model.names
    print(f"[OK] model loaded: {weights.name}, classes={len(names)}, params={sum(p.numel() for p in model.model.parameters()):,}")

    sample = Path(ultralytics.__file__).parent / "assets" / "bus.jpg"
    if not sample.exists():
        print(f"[FAIL] sample image not found: {sample}")
        return 1

    import time
    t0 = time.perf_counter()
    results = model.predict(source=str(sample), conf=0.25, verbose=False)
    elapsed_ms = (time.perf_counter() - t0) * 1000

    r = results[0]
    print(f"[OK] inference done on {sample.name}, image_size={r.orig_shape}, time={elapsed_ms:.0f}ms, detections={len(r.boxes)}")
    for b in r.boxes:
        cls_id = int(b.cls[0])
        box = [round(v, 1) for v in b.xyxy[0].tolist()]
        print(f"     - {names[cls_id]:<12} conf={float(b.conf[0]):.2f} box={box}")

    out_dir = BACKEND_DIR / "results"
    out_dir.mkdir(parents=True, exist_ok=True)
    out = out_dir / "yolo_smoke.jpg"
    import cv2
    cv2.imwrite(str(out), r.plot())
    print(f"[OK] annotated image saved: {out}")
    print("[PASS] YOLO smoke test passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
