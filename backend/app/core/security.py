"""安全模块: 密码哈希(bcrypt) + JWT 令牌的签发与校验.

设计原则: 本文件是"纯工具层", 不 import fastapi, 不抛 HTTP 异常.
把 jwt 异常翻译成 HTTP 401 的事, 由 app/api/deps.py 的依赖来做 —— 分层清晰.

两个概念速记:
    - 密码哈希是"不可逆"的: 数据库里存哈希值, 登录时把明文再哈希一次做比对,
      就算数据库泄露, 攻击者也拿不到原始密码.
    - JWT(JSON Web Token)是"可验证的临时通行证":
      登录成功后服务端发一个 token 给前端, 之后前端每次请求都带上它,
      服务端用密钥验证签名 —— 签名对得上且没过期, 就认为这个用户已登录.
"""

from datetime import datetime, timedelta, timezone

# PyJWT 库(import 名就叫 jwt), 负责 JWT 的编码(签发)与解码(校验)
import jwt

# passlib 是密码哈希的封装库, CryptContext 管理具体的哈希算法
from passlib.context import CryptContext

from app.core.config import settings

# 密码哈希上下文: 声明使用 bcrypt 算法.
# deprecated="auto": 将来若换了更强的算法, 旧哈希会被自动标记为"待升级".
# 已知提示: passlib 1.7.4 配新版 bcrypt 会打一行 "error reading bcrypt version"
# 警告, 属于两个库的版本兼容问题, 不影响功能(本项目把 bcrypt 钉在 4.0.1).
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    """把明文密码加密成哈希(注册时用, 结果存入 users.password_hash 列).

    bcrypt 的特性: 同一个密码每次哈希结果都不同(内部自带随机盐),
    所以数据库里不存在"两个相同哈希", 比对只能靠 verify_password.
    """
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    """校验明文密码与哈希是否匹配(登录时用).

    plain:  用户本次输入的明文
    hashed: 数据库里存的哈希
    """
    return pwd_context.verify(plain, hashed)


def create_access_token(subject: str) -> str:
    """签发 JWT(登录成功后调用).

    subject: 放进 token 的用户标识, 这里传 user.id 转成的字符串
             (JWT 规范要求 sub 声明必须是字符串).
    token 内容(payload)只有两条:
        sub: 谁的通行证(用户 id)
        exp: 过期时间(当前 UTC 时间 + 有效期), PyJWT 会自动转成时间戳
    加上 secret_key 的签名后, 前端拿到的就是一串
    "xxx.yyy.zzz" 形式的字符串(三段: 头.载荷.签名, 均 Base64 编码).
    """
    expire = datetime.now(timezone.utc) + timedelta(
        minutes=settings.access_token_expire_minutes
    )
    payload = {"sub": subject, "exp": expire}
    token = jwt.encode(
        payload=payload, key=settings.secret_key, algorithm=settings.jwt_algorithm
    )
    return token


def decode_access_token(token: str) -> dict:
    """校验并解码 JWT, 返回 payload 字典(如 {"sub": "1", "exp": ...}).

    校验失败会直接抛异常, 由上层(app/api/deps.py)翻译成 HTTP 401:
        jwt.ExpiredSignatureError  —— token 过期了
        jwt.InvalidTokenError      —— 签名不对/token 被篡改/格式错误
    注意这里故意不 try/except —— 本文件保持纯函数, 不掺 HTTP 语义.
    """
    return jwt.decode(token, settings.secret_key, algorithms=[settings.jwt_algorithm])
