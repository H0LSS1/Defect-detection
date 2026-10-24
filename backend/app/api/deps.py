"""可复用的依赖: "当前登录用户"和"管理员权限"的统一入口.

什么是依赖注入(Dependency Injection, DI):
    路由函数不自己写"读请求头→解析token→查数据库"这套流程,
    而是声明"我需要一个参数", FastAPI 自动调用依赖函数把值准备好塞进来.
    好处: 同一套登录校验逻辑, 所有路由共享, 改一处全体生效.

用法示例:
    @router.get("/me")
    def me(user: User = Depends(get_current_user)):
        ...  # 能执行到这里, user 一定是有效登录用户
"""

import jwt
from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.security import decode_access_token
from models.user import User, UserRole

# HTTPBearer: 声明"token 放在请求头 Authorization: Bearer <token> 里".
# 请求没带这个头时, FastAPI 自动返回 403, 不用自己写.
bearer = HTTPBearer()


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer),
    db: Session = Depends(get_db),
) -> User:
    """从 token 还原出当前用户(所有需要登录的接口都用这个依赖).

    依赖也可以套依赖: 本函数又依赖 bearer 和 get_db,
    FastAPI 会自动把整条链路都解析好.
    """
    # credentials.credentials 才是 token 字符串本体
    # (credentials 是 HTTPBearer 包装出来的对象)
    try:
        payload = decode_access_token(credentials.credentials)
    except jwt.ExpiredSignatureError:
        # security.py 只负责抛 jwt 异常, 翻译成 HTTP 401 是本层的职责
        raise HTTPException(status_code=401, detail="token已经过期")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="token无效")

    # payload["sub"] 是签发时存的用户 id 字符串, 转回 int 按主键查
    user = db.get(User, int(payload["sub"]))
    if user is None:
        raise HTTPException(status_code=401, detail="用户不存在")
    if not user.status:
        raise HTTPException(status_code=401, detail="用户已经被禁用")

    return user


def require_admin(user: User = Depends(get_current_user)) -> User:
    """管理员权限门槛: 角色不够返回 403(已登录但权限不足).

    注意 401 和 403 的区别:
        401 = 你还没登录/凭证无效;  403 = 登录了, 但这个操作不让你干.
    """
    if user.role != UserRole.admin:
        raise HTTPException(status_code=403, detail="需要管理员权限")
    return user
