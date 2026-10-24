"""Celery 实例: 分布式任务队列的"总调度台".

本项目里 Celery 的一句话解释:
    用户上传图片后, 推理要花几秒到几十秒, 不能让 HTTP 请求一直等着.
    于是 web 进程把"去处理任务 X"这件事写成一条消息扔进 Redis 队列(broker),
    worker 进程(另一个终端启动的后台程序)从队列里取出消息真正干活.

本模块只是"声明 Celery 实例和去哪连队列", 干活的函数在 services/tasks_worker.py.
"""
from celery import Celery

from app.core.config import settings


def _redis_url(db: int) -> str:
    """拼 Redis 连接串, 带密码时格式为 redis://:密码@主机:端口/库编号."""
    if settings.redis_password:
        return f"redis://:{settings.redis_password}@{settings.redis_host}:{settings.redis_port}/{db}"
    return f"redis://{settings.redis_host}:{settings.redis_port}/{db}"


celery_app = Celery(
    "defect",               # 应用名, 仅作标识
    broker=_redis_url(1),   # 队列: 任务消息排队的地(db1)
    backend=_redis_url(2),  # 回执: 任务函数的返回值存这里(db2)
)

# 声明 worker 启动时需要导入的模块(里面定义了具体任务函数).
# 血泪教训: 不写这个, worker 只加载了 celery_app.py, 一个任务都注册不上,
# 收到消息会报 "Received unregistered task" 并把消息丢弃.
celery_app.conf.update(
    task_serializer="json",       # 消息参数用什么格式序列化
    result_serializer="json",     # 结果用什么格式序列化
    accept_content=["json"],      # 只接受 json(安全默认)
    timezone="Asia/Shanghai",
    enable_utc=False,             # 日志时间用本地时区, 方便看
    include=["app.services.tasks_worker"],
)
