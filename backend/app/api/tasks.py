"""任务路由: 本平台的核心业务 —— 创建检测任务 / 列表 / 进度 / 详情 / 报告导出.

整体异步流程(为什么"创建任务"接口能秒回):
    1. POST /api/tasks       : 收图、落盘、建任务记录(pending), 把"任务id"写进 Redis 消息队列,
                               立刻返回 task_no —— 用户不用等推理;
    2. celery worker(另一个进程)从队列取出任务, 真正干活:
       增强 → 推理 → 标注图 → 结果入库 → 每处理完一张更新 Redis 进度;
    3. GET /{task_no}/progress: 前端轮询这个接口拿进度, 全部完成后拉详情/导出报告.
"""

from datetime import datetime
from pathlib import Path
import json
import uuid

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.celery_app import celery_app
from app.core.config import settings
from app.core.db import get_db
from app.core.redis import get_redis
from app.schemas.task import ImageOut, TaskDetailOut, TaskOut, TaskProgressOut
from app.services.report import build_task_report
from models.defectclass import DefectClass
from models.detectionresult import DetectionResult
from models.image import Image, ImageStatus
from models.modelversion import ModelVersion
from models.report import Report
from models.task import Task, TaskStatus
from models.user import User, UserRole

# 允许上传的图片后缀白名单(小写). 不在名单里的直接 400 拒绝,
# 防止用户传任意文件(如 .exe/.php)到服务器上.
ALLOWED_EXTS = {".jpg", ".jpeg", ".png", ".bmp"}

router = APIRouter(prefix="/api/tasks", tags=["tasks"])


@router.post("", response_model=TaskOut)
async def create_task(
    # multipart 表单(和 JSON 请求体不同): 普通字段用 Form(), 文件用 File().
    # 文件参数会被 FastAPI 包装成 UploadFile(有 .filename/.read() 等).
    task_name: str = Form(...),          # ... 表示必填
    conf: float = Form(0.25),            # 置信度阈值, 不传用 0.25
    files: list[UploadFile] = File(...), # 支持一次多选文件
    # 登录态: 任务归属当前用户(没有有效 token 根本进不了函数体)
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """创建检测任务: 收图 → 落盘 → 建记录 → 扔进队列 → 立即返回任务号."""
    # ① 找当前可用的模型版本(init_db.py 种子数据里的 yolov8n).
    #    任务必须记录 model_id, 保证"这批结果是用什么模型跑的"可追溯.
    model = db.query(ModelVersion).filter(ModelVersion.is_active.is_(True)).first()
    if model is None:
        # 500 = 服务器端配置问题(不是用户的错), 给出排查提示
        raise HTTPException(
            status_code=500, detail="无可用模型版本，请检查 model_versions 表"
        )
    model_id = model.id

    # ② 生成对外任务号: TSK + 时间戳(可读可排序) + 4 位随机段(防同秒冲突)
    task_no = (
        "TSK" + datetime.now().strftime("%Y%m%d%H%M%S") + uuid.uuid4().hex[:4].upper()
    )

    total_images = 0
    for _ in files:
        total_images += 1

    # ③ 建任务记录: 初始状态 pending(排队中), 完成数 0.
    task = Task(
        task_no=task_no,
        task_name=task_name,
        model_id=model_id,
        user_id=user.id,
        confidence_threshold=conf,
        total_images=total_images,
        status=TaskStatus.pending,
        completed_images=0,
    )
    db.add(task)   # 加入会话
    db.flush()     # 立刻发 INSERT 拿到自增 task.id, 但事务还没提交:
                   # 后面任何一步失败可以整体回滚, 不会留下"半截任务"

    # 原图目录: backend/uploads/{任务号}/original/
    # parents[2] = backend(app/api/tasks.py → api → app → backend)
    save_dir = (
        Path(__file__).resolve().parents[2] / settings.upload_dir / task_no / "original"
    )
    save_dir.mkdir(parents=True, exist_ok=True)

    # ④ 逐张图: 校验后缀 → 读内容 → 随机名落盘 → 建图片记录
    for f in files:
        # 从"用户报的文件名"里取后缀并转小写; filename 可能为 None, 用 or "" 兜底
        ext = Path(f.filename or "").suffix.lower()
        if ext not in ALLOWED_EXTS:
            raise HTTPException(
                status_code=400, detail=f"不支持的文件类型: {f.filename}"
            )

        # 磁盘文件名用 uuid 随机生成 —— 与展示名分离:
        # 防重名覆盖 / 防中文路径问题 / 防恶意路径穿越
        disk_name = uuid.uuid4().hex + ext
        data = await f.read()                        # async 路由读上传内容
        (save_dir / disk_name).write_bytes(data)     # 写入磁盘

        db.add(
            Image(
                task_id=task.id,
                user_id=user.id,
                # 数据库只存"相对 backend/"的路径, 换机器不用改数据
                original_path=f"{settings.upload_dir}/{task_no}/original/{disk_name}",
                filename=f.filename,                 # 原始文件名仅作展示
                file_size=len(data),
                status=ImageStatus.uploaded,
            )
        )

    # ⑤ 一次性提交: 前面所有 INSERT/落盘记录在这一刻生效.
    # (注意磁盘文件在上一步就已写出, 若此处失败会留下孤儿文件, 学习项目可接受)
    db.commit()
    db.refresh(task)  # 把数据库生成的字段(id/created_at)回填到对象

    # ⑥ 派发到 Celery 队列: web 进程只负责"喊一嗓子", 真正干活的是 worker 进程.
    # send_task 按任务名字符串派发, 本文件不需要 import worker 模块
    # (worker 模块会连带加载 torch, web 进程保持轻量).
    try:
        celery_app.send_task("tasks.process_task", args=[task.id])
    except Exception:
        # Redis 队列不可用时不让用户白等: 任务留在 pending 状态, 可稍后重新派发
        pass
    return task  # response_model=TaskOut 自动裁剪成约定字段


@router.get("", response_model=list[TaskOut])
def list_tasks(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """任务列表: admin 看全部, 普通用户只看自己创建的(数据库侧过滤)."""
    query = db.query(Task)
    if user.role != UserRole.admin:
        query = query.filter(Task.user_id == user.id)  # 过滤在 SQL 层做, 不捞全表再筛
    return query.order_by(Task.created_at.desc()).all()  # 新任务排前面


@router.get("/{task_no}/progress", response_model=TaskProgressOut)
def get_progress(
    task_no: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """查询任务进度(前端轮询此接口驱动进度条).

    两份数据源, 谁新鲜用谁:
        Redis  : worker 每处理完一张图就更新一次 —— 秒级新鲜, 但有 TTL 会过期;
        MySQL  : 权威数据 —— 稍滞后但永远在.
    """
    task = db.query(Task).filter(Task.task_no == task_no).first()
    if task is None or (user.role != UserRole.admin and task.user_id != user.id):
        # 不存在的任务和不属于你的任务统一 404, 不暴露存在性
        raise HTTPException(status_code=404, detail="任务不存在")

    if task.status in (TaskStatus.completed, TaskStatus.failed):
        # 终态: MySQL 是权威数据
        completed, total, status = task.completed_images, task.total_images, task.status
    else:
        # 运行中: 优先读 Redis; 拿不到(过期/还没写)再回退 MySQL
        raw = get_redis().get(f"defect:task:{task.id}:progress")
        if raw:
            data = json.loads(raw)
            completed, total = data["completed"], data["total"]
            status = TaskStatus(data["status"])
        else:
            completed, total, status = task.completed_images, task.total_images, task.status

    # 换算成百分数(给前端进度条直接绑定); total=0 时防除零
    percent = round(completed / total * 100, 1) if total else 0.0
    return TaskProgressOut(
        task_no=task.task_no, status=status, completed=completed, total=total, percent=percent
    )


def _get_owned_task(task_no: str, user: User, db: Session) -> Task:
    """按 task_no 取任务并校验归属: 不存在/不属于你 统一 404.

    抽成私有函数(下划线开头)是因为详情/报告两个接口都要用这套校验.
    统一 404 而不是 403: 不向越权者暴露"这个任务其实存在"的事实.
    """
    task = db.query(Task).filter(Task.task_no == task_no).first()
    if task is None or (user.role != UserRole.admin and task.user_id != user.id):
        raise HTTPException(status_code=404, detail="任务不存在")
    return task


@router.get("/{task_no}", response_model=TaskDetailOut)
def get_task_detail(
    task_no: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """任务详情: 任务元信息 + 每张图的状态与三种图(原图/增强图/标注图)路径.

    前端拿到 paths 后拼静态 URL 展示:
        http://host:8000/media/{path}    (main.py 里挂载的 StaticFiles)
    """
    task = _get_owned_task(task_no, user, db)
    images = (
        db.query(Image).filter(Image.task_id == task.id).order_by(Image.id).all()
    )
    # 先用 TaskOut 把任务字段转成字典, 再把图片列表塞进去组合成详情
    base = TaskOut.model_validate(task).model_dump()
    return TaskDetailOut(**base, images=[ImageOut.model_validate(i) for i in images])


@router.get("/{task_no}/report")
def export_report(
    task_no: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """导出 Word 检测报告: 生成 docx → 登记到 reports 表 → 文件流返回给前端下载."""
    task = _get_owned_task(task_no, user, db)
    if task.status not in (TaskStatus.completed, TaskStatus.failed):
        raise HTTPException(status_code=400, detail="任务尚未结束, 无法导出报告")

    # 收集数据: 图片列表 + 检测框( join 图片表过滤到本任务 ) + 类别中文映射
    images = db.query(Image).filter(Image.task_id == task.id).order_by(Image.id).all()
    results = (
        db.query(DetectionResult)
        .join(Image, DetectionResult.image_id == Image.id)
        .filter(Image.task_id == task.id)
        .order_by(DetectionResult.image_id, DetectionResult.id)
        .all()
    )
    class_display = {c.class_name: c.display_name for c in db.query(DefectClass).all()}
    base_dir = Path(__file__).resolve().parents[2]  # backend/ 目录

    # 纯服务函数: 生成 docx 并落盘到 results/{task_no}/report/{task_no}.docx
    report_path = build_task_report(task, images, results, class_display, base_dir)

    # reports 表 upsert(有则更新无则插入): 同任务同格式只保留最新一次导出记录
    rep = (
        db.query(Report)
        .filter(Report.task_id == task.id, Report.file_format == "docx")
        .first()
    )
    if rep is None:
        rep = Report(task_id=task.id, user_id=user.id, file_format="docx")
        db.add(rep)
    rep.file_path = str(report_path.relative_to(base_dir)).replace("\\", "/")  # 存相对路径(统一正斜杠)
    rep.file_size = report_path.stat().st_size
    rep.defect_count = len(results)
    db.commit()

    # FileResponse: 把服务器文件作为下载流返回; filename 是浏览器"另存为"的默认名
    return FileResponse(
        path=str(report_path),
        filename=f"{task_no}.docx",
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    )
