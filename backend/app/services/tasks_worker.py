"""Celery 任务: 检测任务的真正执行者(跑在 worker 进程里, 不在 web 进程).

worker 进程与 web 进程是两个独立的 Python 程序:
    web : uvicorn 启动, 负责收请求、把"任务id"写进 Redis 队列
    worker: celery 启动(启动命令见 PLAN.md), 从队列取任务id, 执行本文件的 process_task

本文件的完整职责(单张图的流水线):
    读原图 → 图像增强 → YOLO 推理 → 检测框入库 → 画标注图落盘 → 更新任务进度
"""
import json
import logging
import time
import uuid
from datetime import datetime
from pathlib import Path

import cv2
import numpy as np

from app.core.celery_app import celery_app
from app.core.config import settings
from app.core.db import SessionLocal
from app.core.redis import get_redis
from app.services.detector import get_detector
from app.services.enhance import ImageEnhancer
from models.detectionresult import DetectionResult
from models.image import Image, ImageStatus
from models.task import Task, TaskStatus

# 日志器: 单图失败时必须留下记录, 否则出了问题完全没有线索(踩过的坑)
logger = logging.getLogger(__name__)

BACKEND_DIR = Path(__file__).resolve().parents[2]  # backend/ 目录
PROGRESS_TTL = 86400  # 进度 key 的存活时间(秒), 一天后自动删除防垃圾堆积


def _imread_safe(path: Path) -> np.ndarray:
    """中文路径安全读图: cv2.imread 遇到中文路径会静默返回 None, 用 imdecode 替代."""
    img = cv2.imdecode(np.fromfile(str(path), dtype=np.uint8), cv2.IMREAD_COLOR)
    if img is None:
        raise IOError(f"cannot decode image: {path}")
    return img


def _imwrite_safe(path: Path, img: np.ndarray) -> None:
    """中文路径安全写图: cv2.imwrite 的对应安全版本."""
    ok, buf = cv2.imencode(path.suffix, img)
    if not ok:
        raise IOError(f"imencode failed: {path}")
    buf.tofile(path)


def _set_progress(task_id: int, status: str, completed: int, total: int) -> None:
    """把任务进度写成 Redis 的 JSON 字符串, 供进度接口秒级查询.

    key:   defect:task:{id}:progress
    value: {"completed": 2, "total": 5, "status": "running"}
    ex=86400: 一天后自动过期, 防止历史任务的进度永远占着内存.
    """
    r = get_redis()
    r.set(
        f"defect:task:{task_id}:progress",
        json.dumps({"completed": completed, "total": total, "status": status}),
        ex=PROGRESS_TTL,
    )


# name= 显式命名任务: web 进程用这个名字符串派发(send_task),
# 两边只靠这个字符串对齐, web 进程不需要 import 本模块(连带加载 torch).
@celery_app.task(name="tasks.process_task")
def process_task(task_id: int) -> dict:
    """处理一个检测任务: 遍历任务的所有图片, 逐张走完整流水线."""
    # 独立会话: worker 是请求结束后才执行的, 请求的 get_db 会话早已关闭,
    # 必须自己从工厂造一个, 用完在 finally 里关闭.
    db = SessionLocal()
    try:
        task = db.get(Task, task_id)
        if task is None:
            return {"task_id": task_id, "status": "not_found"}

        # ① 标记 running 并记录开始时间
        task.status = TaskStatus.running
        task.started_at = datetime.now()
        db.commit()
        _set_progress(task_id, "running", 0, task.total_images)

        # ② 准备资源: 增强器 + 检测器(首次调用时才加载模型, 单例)
        enhancer = ImageEnhancer()
        detector = get_detector()
        results_dir = BACKEND_DIR / settings.result_dir / task.task_no
        enhanced_dir = results_dir / "enhanced"     # 增强图目录
        annotated_dir = results_dir / "annotated"   # 标注图目录
        enhanced_dir.mkdir(parents=True, exist_ok=True)
        annotated_dir.mkdir(parents=True, exist_ok=True)

        images = db.query(Image).filter(Image.task_id == task_id).order_by(Image.id).all()
        detections_total = 0
        # DECIMAL 列从 MySQL 读出来是 Decimal 类型,
        # ultralytics 只认 int/float, 必须转 float(踩过的坑)
        conf_value = float(task.confidence_threshold)

        # ③ 逐张处理: enumerate(...,1) 让序号从 1 开始, 正好当进度计数
        for i, img_row in enumerate(images, 1):
            try:
                # a. 读原图
                img = _imread_safe(BACKEND_DIR / img_row.original_path)
                # b. 图像增强(中值去噪 -> CLAHE -> 自适应伽马)
                enhanced = enhancer.enhance(img)

                # c. 增强图落盘(随机名), 相对路径回填数据库
                enhanced_name = uuid.uuid4().hex + ".jpg"
                _imwrite_safe(enhanced_dir / enhanced_name, enhanced)
                img_row.enhanced_path = (
                    f"{settings.result_dir}/{task.task_no}/enhanced/{enhanced_name}"
                )

                # d. 推理(用任务上记录的阈值) + 计时
                t0 = time.perf_counter()
                boxes = detector.detect(enhanced, conf=conf_value)
                elapsed_ms = int((time.perf_counter() - t0) * 1000)

                # e. 画标注图: 红框 + "类别 置信度" 标签(putText 不支持中文, 用英文)
                annotated = enhanced.copy()
                for b in boxes:
                    cv2.rectangle(
                        annotated, (b["x1"], b["y1"]), (b["x2"], b["y2"]), (0, 0, 255), 2
                    )
                    label = f'{b["class_name"]} {b["confidence"]:.2f}'
                    cv2.putText(
                        annotated, label, (b["x1"], max(b["y1"] - 6, 12)),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2, cv2.LINE_AA,
                    )
                annotated_name = uuid.uuid4().hex + ".jpg"
                _imwrite_safe(annotated_dir / annotated_name, annotated)
                img_row.annotated_path = (
                    f"{settings.result_dir}/{task.task_no}/annotated/{annotated_name}"
                )

                # f. 检测框入库(幂等: 先删这张图的旧结果, 任务重跑不会翻倍)
                db.query(DetectionResult).filter(
                    DetectionResult.image_id == img_row.id
                ).delete()
                for b in boxes:
                    db.add(DetectionResult(
                        image_id=img_row.id,
                        class_name=b["class_name"],
                        class_id=b["class_id"],
                        confidence=b["confidence"],
                        x1=b["x1"], y1=b["y1"], x2=b["x2"], y2=b["y2"],
                    ))

                # g. 回填单图状态与耗时
                img_row.status = ImageStatus.done
                img_row.inference_time_ms = elapsed_ms
                detections_total += len(boxes)
            except Exception as exc:
                # 单图失败不拖垮整个任务: 标记 failed 继续下一张,
                # 但必须留日志(踩过的坑: 静默吞异常导致问题完全不可见)
                logger.warning("image %s failed: %s: %s", img_row.id, type(exc).__name__, exc)
                img_row.status = ImageStatus.failed

            # h. 每处理完一张就更新进度并提交:
            #    - 前端轮询能看到逐张爬升
            #    - 中途崩溃时, 已完成的图不丢
            task.completed_images = i
            _set_progress(task_id, "running", i, task.total_images)
            db.commit()

        # ⑤ 全部完成
        task.status = TaskStatus.completed
        task.finished_at = datetime.now()
        db.commit()
        _set_progress(task_id, "completed", task.completed_images, task.total_images)
        return {"task_id": task_id, "status": "completed", "detections": detections_total}

    except Exception as exc:
        # ⑥ 整体失败(资源准备/数据库层面的错误): 任务标 failed 并记录原因.
        # 注意里层还包了一层 try —— 若连数据库都连不上, 标记失败的动作本身也会炸.
        try:
            task = db.get(Task, task_id)
            if task is not None:
                task.status = TaskStatus.failed
                task.error_message = str(exc)[:500]  # 截断, 对齐列宽
                task.finished_at = datetime.now()
                db.commit()
                _set_progress(task_id, "failed", task.completed_images, task.total_images)
        except Exception:
            pass
        return {"task_id": task_id, "status": "failed", "error": str(exc)[:500]}
    finally:
        db.close()  # 无论成败, 会话必须归还
