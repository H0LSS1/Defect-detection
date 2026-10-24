"""任务相关的 Pydantic 模型: 任务创建/列表/详情/进度 四类接口的出入参."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict

from models.image import ImageStatus
from models.task import TaskStatus


class TaskOut(BaseModel):
    """任务列表/创建返回的单行摘要(不含图片明细).

    from_attributes=True: 允许从 SQLAlchemy 的 Task 对象直接转换.
    """

    model_config = ConfigDict(from_attributes=True)

    id: int
    task_no: str
    task_name: str
    status: TaskStatus
    total_images: int
    completed_images: int
    confidence_threshold: float
    error_message: str | None = None
    created_at: datetime


class TaskProgressOut(BaseModel):
    """进度查询的响应体: GET /api/tasks/{task_no}/progress.

    completed/total 来自 Redis(worker 实时更新)或 MySQL(回退),
    percent 是给前端进度条直接绑定的百分数.
    """

    task_no: str
    status: TaskStatus
    completed: int
    total: int
    percent: float


class ImageOut(BaseModel):
    """任务详情里单张图片的信息(含三种图的路径, 前端拼静态 URL 展示)."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    filename: str                     # 用户看到的原始文件名
    status: ImageStatus               # 单图处理状态
    original_path: str                # 原图(上传的)
    enhanced_path: str | None = None  # 增强图(worker 处理后回填)
    annotated_path: str | None = None # 标注图(worker 画框后回填)
    file_size: int
    inference_time_ms: int | None = None


class TaskDetailOut(BaseModel):
    """任务详情的响应体: GET /api/tasks/{task_no}.

    = 任务元信息 + 图片列表(含每张图的检测图路径).
    """ 

    id: int
    task_no: str
    task_name: str
    status: TaskStatus
    total_images: int
    completed_images: int
    confidence_threshold: float
    error_message: str | None = None
    created_at: datetime
    started_at: datetime | None = None
    finished_at: datetime | None = None
    images: list[ImageOut]
