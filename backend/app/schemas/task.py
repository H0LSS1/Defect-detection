from pydantic import BaseModel, ConfigDict
from datetime import datetime

from models.task import TaskStatus


class TaskOut(BaseModel):
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
