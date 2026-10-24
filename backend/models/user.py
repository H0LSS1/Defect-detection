"""用户表模型: 存平台的登录账号, 以及"谁能干什么"(角色权限).

对应的接口: app/api/auth.py (注册/登录/查询当前用户)
"""

# 枚举类型: 把角色限定成固定的几个值, 防止出现拼错的"超管"/"adin"之类
from datetime import datetime
from enum import Enum

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from models.base import Base


class UserRole(str, Enum):
    """用户角色枚举.

    继承 str 是为了让枚举值可以直接当字符串用:
        UserRole.admin == "admin"  →  True
    这样接口返回 JSON 时前端能直接拿到 "admin"/"inspector".
    """

    inspector = "inspector"   # 普通质检员: 只能操作自己创建的任务
    admin = "admin"           # 管理员: 可以看全部任务、管理用户


class User(Base):
    """users 表: 一个对象 = 一个注册用户.

    密码安全红线:
        数据库里只存 password_hash(bcrypt 哈希), 永远不存明文;
        就算数据库泄露, 攻击者也拿不到原始密码.
    """

    # 登录名, 唯一(重名注册会被接口以 409 拒绝)
    username: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)

    # bcrypt 哈希固定 60 字符, 给 255 留余量(以后换算法也放得下)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)

    # 展示用的姓名, 可不填
    real_name: Mapped[str] = mapped_column(String(100), nullable=True)

    # 角色: 标注 UserRole 类型后 SQLAlchemy 自动建 ENUM('inspector','admin') 列,
    # default 表示"注册时不传角色就给普通质检员"
    role: Mapped[UserRole] = mapped_column(nullable=False, default=UserRole.inspector)

    # 邮箱可选; unique=True 但允许 NULL(MySQL 里多个 NULL 不算重复)
    email: Mapped[str] = mapped_column(String(100), unique=True, nullable=True)

    # 账号状态: True 正常 / False 被禁用(禁用后登录和接口都会被拒)
    status: Mapped[bool] = mapped_column(nullable=False, default=True)

    # 最近一次登录时间, 登录接口成功后回填
    last_login: Mapped[datetime] = mapped_column(nullable=True)

    # 显式指定表名. 不写的话 SQLAlchemy 会自动用类名小写(user),
    # 而我们要的表名是复数 users —— 和建库脚本/设计文档保持一致.
    __tablename__ = "users"
