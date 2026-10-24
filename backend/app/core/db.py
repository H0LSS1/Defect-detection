"""数据库会话模块: 提供与 MySQL 通信的"连接池"和"会话工厂", 以及 FastAPI 的依赖注入入口.

在整个应用里的分工:
    - engine       : 全局只有一条(连接池管理者), 模块导入时创建
    - SessionLocal : "会话工厂", 需要操作数据库时 SessionLocal() 造一个会话
    - get_db       : 给路由函数用的依赖, 自动分配会话、用完自动归还

其他文件只 import 这三样, 不自己 create_engine.
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# settings.mysql_url 是 config.py 里拼好的连接串(@property, 不加括号)
from app.core.config import settings

# create_engine 创建连接池(engine).
# pool_pre_ping=True: 每次从池里拿连接前先"ping"一下数据库确认还活着.
#   为什么需要: MySQL 默认把闲置 8 小时的连接掐断(wait_timeout),
#   不加这个参数, 服务放一晚后第一个请求会报 OperationalError.
#   整个应用只允许创建这一个 engine, 千万别在每个请求里都建(那等于每请求开一个连接池).
engine = create_engine(settings.mysql_url, pool_pre_ping=True)

# sessionmaker 是"会话工厂": 它本身不是会话, 调用 SessionLocal() 才得到一个会话.
# 两个常用参数:
#   autoflush=False        : 查询前不要自动把未保存的改动刷进 SQL, 行为更可预期
#   expire_on_commit=False : commit 之后对象属性仍然可读.
#     (默认 True 时 commit 完再访问 user.username 会偷偷再发一条 SELECT,
#      初学者最容易踩的坑之一, 统一关掉)
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


def get_db():
    """FastAPI 依赖注入的标准写法(生成器依赖).

    工作流程:
      1. 请求进来, FastAPI 执行到 yield, 把 db 会话"塞"给路由函数的参数;
      2. 路由函数正常使用 db 查询/写入;
      3. 请求结束(无论成功报错), FastAPI 回到生成器继续执行 finally, 关闭会话.

    路由里的用法(不需要手动 close):
        def xxx(db: Session = Depends(get_db)):
            db.query(...)...

    为什么用函数+yield 而不是直接 SessionLocal():
        会话的生命周期必须和"请求"绑定 —— 请求结束必须归还,
        这个"包一层"的活交给 FastAPI 的依赖系统来做最干净.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
