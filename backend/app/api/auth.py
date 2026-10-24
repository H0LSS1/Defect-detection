"""认证路由: 注册 / 登录 / 查询当前用户, 三个接口.

完整登录链路(把三个接口串起来看):
    1. POST /register  → 账号落库(密码只有哈希)
    2. POST /login     → 校验密码, 签发 JWT 给前端
    3. GET  /me        → 前端带 JWT 访问, 返回"我是谁"
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_admin
from app.core.db import get_db
from app.core.security import create_access_token, hash_password, verify_password
from app.schemas.user import Token, UserCreate, UserLogin, UserOut
from models.user import User

# prefix: 本文件所有接口的公共前缀; tags: Swagger 文档里的分组名
router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/register", response_model=UserOut)
def register(body: UserCreate, db: Session = Depends(get_db)):
    """注册新用户.

    流程: 查重 → 密码哈希 → 建对象入库 → 返回(响应模型自动裁掉敏感字段)
    """
    # ① 查重: 用户名是唯一约束, 先查后插能返回友好的 409,
    #    否则撞唯一索引会抛数据库异常变成 500
    existing = db.query(User).filter(User.username == body.username).first()
    if existing:
        raise HTTPException(status_code=409, detail="用户已存在")
    # 邮箱同理(模型里也是 unique); 前端没填邮箱(email 为 None)就跳过查重
    if body.email is not None:
        email_taken = db.query(User).filter(User.email == body.email).first()
        if email_taken:
            raise HTTPException(status_code=409, detail="邮箱已存在")

    # ② 哈希: 到这一步 body.password 还在内存里, 哈希完就只存哈希值
    password_hash = hash_password(body.password)

    # ③ 入库: role 不传, 走模型默认值 inspector(普通质检员)
    user = User(
        username=body.username,
        password_hash=password_hash,
        real_name=body.real_name,
        email=body.email,
    )
    db.add(user)      # 加入会话(还没写进数据库)
    db.commit()       # 提交事务(真正写入)
    db.refresh(user)  # 把数据库生成的 id/created_at 回填到对象里

    # response_model=UserOut 自动把 ORM 对象转成安全字段(无 password_hash)
    return user


@router.post("/login", response_model=Token)
def login(body: UserLogin, db: Session = Depends(get_db)):
    """登录: 校验账号密码, 签发 JWT.

    安全细节: "用户不存在"和"密码错误"返回同一条错误信息,
    不告诉攻击者"这个用户名是存在的" —— 防止撞库枚举有效用户名.
    状态码统一 401(Unauthorized).
    """
    user = db.query(User).filter(User.username == body.username).first()
    # verify_password(明文, 哈希): bcrypt 比对; 用户不存在时短路返回 401
    if user is None or not verify_password(body.password, user.password_hash):
        raise HTTPException(status_code=401, detail="用户名或密码错误")
    if not user.status:
        raise HTTPException(status_code=401, detail="用户被禁用")

    # 签发 token: sub 放用户 id 字符串, 之后的请求都靠它认人
    token = create_access_token(str(user.id))
    return Token(access_token=token)


@router.get("/me", response_model=UserOut)
def me(user: User = Depends(get_current_user)):
    """查询当前登录用户: 函数体里没有任何业务 —— 校验全在依赖里完成.

    这是依赖注入价值的最好例子: 需要登录态的接口,
    加一个参数 user: User = Depends(get_current_user) 就行.
    """
    return user
