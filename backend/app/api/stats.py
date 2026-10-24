"""统计路由: 给阶段 6 前端的 ECharts 看板提供数据源.

一个接口(/overview)返回看板需要的全部数据:
    总任务数 / 总图片数 / 检出框总数 / 平均推理耗时
    类别分布(饼图) / 近 14 天任务与图片趋势(折线图)
权限: admin 看全平台, inspector 只统计自己的数据(与任务列表同规则).
"""
from collections import Counter
from datetime import date, timedelta

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.db import get_db
from models.defectclass import DefectClass
from models.detectionresult import DetectionResult
from models.image import Image, ImageStatus
from models.task import Task
from models.user import User, UserRole

router = APIRouter(prefix="/api/stats", tags=["stats"])


@router.get("/overview")
def overview(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """看板总览: 一次请求返回所有图表数据(省得前端发好几个请求)."""
    # ① 确定数据可见范围: admin 全平台, inspector 仅本人
    tasks_q = db.query(Task)
    if user.role != UserRole.admin:
        tasks_q = tasks_q.filter(Task.user_id == user.id)
    tasks = tasks_q.all()
    task_ids = [t.id for t in tasks]  # 后面用这批 id 过滤图片和检出框

    # ② 把图片和检出框一次性查出来, 内存里做统计
    #    (学习项目数据量小, Python 统计最直观; 数据量大应改成 SQL GROUP BY)
    images = (
        db.query(Image).filter(Image.task_id.in_(task_ids)).all() if task_ids else []
    )
    detections = (
        db.query(DetectionResult)
        .join(Image, DetectionResult.image_id == Image.id)
        .filter(Image.task_id.in_(task_ids))
        .all()
        if task_ids
        else []
    )

    # ③ 类别分布: 统计每个类别出现次数, 并翻译成中文名/颜色.
    # Counter 是标准库的计数器, Counter(["a","a","b"]) → {"a":2,"b":1}
    class_map = {c.class_name: c for c in db.query(DefectClass).all()}
    counter = Counter(d.class_name for d in detections)
    distribution = [
        {
            "class_name": name,                                        # 模型原始类别名
            "display_name": class_map[name].display_name if name in class_map else name,  # 中文名(没登记就显示原名)
            "color": class_map[name].color if name in class_map else None,  # 前端画图用
            "count": count,
        }
        # most_common(): 按出现次数降序排列
        for name, count in counter.most_common()
    ]

    # ④ 近 14 天趋势: 每天建了几个任务、传了几张图
    today = date.today()
    days = [today - timedelta(days=i) for i in range(13, -1, -1)]  # 13 天前 → 今天
    tasks_by_day = Counter(t.created_at.date() for t in tasks)
    images_by_day = Counter(i.created_at.date() for i in images)
    trend = [
        {
            "date": d.isoformat(),                    # "2026-10-24" 格式
            "tasks": tasks_by_day.get(d, 0),          # 没数据的天补 0
            "images": images_by_day.get(d, 0),
        }
        for d in days
    ]

    # ⑤ 顶层汇总指标
    done_images = sum(1 for i in images if i.status == ImageStatus.done)
    inference_times = [i.inference_time_ms for i in images if i.inference_time_ms]

    return {
        "total_tasks": len(tasks),
        "total_images": len(images),
        "done_images": done_images,
        "total_detections": len(detections),
        # 平均单图推理耗时(ms), 无数据时返回 None(前端显示 "-")
        "avg_inference_ms": round(sum(inference_times) / len(inference_times), 1)
        if inference_times
        else None,
        "class_distribution": distribution,
        "trend": trend,
    }
