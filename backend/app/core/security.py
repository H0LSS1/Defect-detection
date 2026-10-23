from datetime import datetime, timezone, timedelta
from passlib.context import CryptContext
import jwt
from app.core.config import settings

# 密码哈希
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


# JWT签发与校验
def create_access_token(subject: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(
        minutes=settings.access_token_expire_minutes
    )
    payload = {"sub": subject, "exp": expire}
    token = jwt.encode(
        payload=payload, key=settings.secret_key, algorithm=settings.jwt_algorithm
    )
    return token


def decode_access_token(token: str) -> dict:
    return jwt.decode(token, settings.secret_key, algorithms=[settings.jwt_algorithm])
