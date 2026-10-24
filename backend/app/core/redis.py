"""Redis 业务连接单例(进度/缓存), 固定使用 settings.redis_db(即 db0).

本项目里 Redis 同时扮演三个角色, 用 db 编号隔离互不干扰:
    db0 -> 业务数据(本文件): 检测进度等
    db1 -> Celery broker  : 任务消息队列(见 celery_app.py)
    db2 -> Celery backend : 任务执行结果回执

单例的意义: redis.Redis 对象内部管理着连接池,
全项目共用一个即可, 和数据库 engine 同理.
"""

import redis

from app.core.config import settings

# 模块级变量, 保存唯一的连接实例; None 表示"还没创建"
_redis: redis.Redis | None = None


def get_redis() -> redis.Redis:
    """懒加载单例: 第一次调用时创建连接, 之后每次返回同一个实例.

    (与 services/detector.py 里 get_detector 的写法同款)
    """
    global _redis
    if _redis is None:
        _redis = redis.Redis(
            host=settings.redis_host,
            port=settings.redis_port,
            db=settings.redis_db,
            # settings 里无密码时是空字符串 "", redis 客户端要求传 None
            password=settings.redis_password or None,
            # decode_responses=True: get() 返回 str 而不是 bytes.
            # 不加的话拿到 b'{"completed":1}' 这种字节串, 还得手动 .decode().
            decode_responses=True,
        )
    return _redis
