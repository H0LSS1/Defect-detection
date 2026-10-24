"""用户相关的 Pydantic 模型: 定义"接口进出的数据长什么样".

和 ORM 模型(models/user.py)的分工一定要分清:
    ORM 模型   = 数据库里这张表长什么样(字段全、含密码哈希)
    Pydantic 模型 = 某个接口的请求/响应长什么样(按需裁剪 + 自动校验)

为什么要分开:
    注册接口进来只需要 用户名/密码/姓名/邮箱 → UserCreate 校验
    用户信息接口出去绝不能带 password_hash   → UserOut 只声明安全字段
    Pydantic 只序列化"声明过的字段", 没声明的自动被挡住, 这就是安全边界.
"""

from datetime import datetime

# BaseModel: 所有 Pydantic 模型的父类
# EmailStr: 带邮箱格式校验的字符串类型(需要 pip install email-validator)
# Field: 给字段加约束(长度/默认值等)
# ConfigDict: Pydantic v2 的类级配置开关
from pydantic import BaseModel, ConfigDict, EmailStr, Field

from models.user import UserRole


class UserCreate(BaseModel):
    """注册接口的请求体: POST /api/auth/register 的 JSON."""

    username: str = Field(min_length=3, max_length=50)    # 用户名 3~50 字符
    password: str = Field(min_length=6, max_length=72)
    # 72 是 bcrypt 的硬上限: bcrypt 只取前 72 字节, 多了也白传

    real_name: str | None = None                          # 姓名, 选填
    # 标注成 str | None 自动可空; EmailStr 会校验格式, 假邮箱直接 422 拒绝
    email: EmailStr | None = None


class UserLogin(BaseModel):
    """登录接口的请求体: POST /api/auth/login 的 JSON."""

    username: str
    password: str


class UserOut(BaseModel):
    """用户信息的响应体: 返回给前端的用户数据(不含任何敏感字段).

    model_config = ConfigDict(from_attributes=True):
        默认 Pydantic 只会从"字典"里读数据, 加这个配置后允许从
        "对象的属性"里读 —— 这样才能把 SQLAlchemy 的 User 对象
        直接交给本模型做转换(UserOut.model_validate(user_orm)).
    """

    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str
    real_name: str | None = None
    role: UserRole          # 枚举自动序列化成 "inspector"/"admin"
    status: bool
    created_at: datetime
    last_login: datetime | None = None   # 用户管理列表展示用
    # 注意: 这里故意没有 password_hash 字段 —— ORM 对象里即使有,
    # 转换成 UserOut 后也会被丢弃, 密码哈希永远不会泄露给前端.


class UserUpdate(BaseModel):
    """管理员修改用户的请求体(PUT /api/auth/users/{user_id}).

    两个字段都可省略: 只传 status 就只改状态, 只传 role 就只改角色.
    """ 

    status: bool | None = None      # 启用(True)/禁用(False)
    role: UserRole | None = None    # 改成 inspector/admin


class Token(BaseModel):
    """登录成功后的响应体: 前端拿到 access_token, 之后每个请求带上它.

    token_type="bearer" 是 HTTP 认证的标准写法,
    前端把它拼成请求头: Authorization: Bearer <access_token>
    """

    access_token: str
    token_type: str = "bearer"
