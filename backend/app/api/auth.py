from fastapi import APIRouter, Depends
from fastapi import HTTPException
from app.core.db import get_db
from sqlalchemy.orm import Session

from app.schemas.user import UserCreate, UserLogin, UserOut, Token
from models.user import User
from app.core.security import (
    hash_password,
    verify_password,
    create_access_token,
)
from app.api.deps import get_current_user, require_admin

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/register", response_model=UserOut)
def register(body: UserCreate, db: Session = Depends(get_db)):

    existing = db.query(User).filter(User.username == body.username).first()
    if existing:
        raise HTTPException(status_code=409, detail="用户已存在")
    if body.email is not None:
        email_taken = db.query(User).filter(User.email == body.email).first()
        if email_taken:
            raise HTTPException(status_code=409, detail="邮箱已存在")

    password_hash = hash_password(body.password)
    user = User(
        username=body.username,
        password_hash=password_hash,
        real_name=body.real_name,
        email=body.email,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    return user


@router.post("/login", response_model=Token)
def login(body: UserLogin, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == body.username).first()
    if user is None or not verify_password(body.password, user.password_hash):
        raise HTTPException(status_code=401, detail="用户名或密码错误")
    if not user.status:
        raise HTTPException(status_code=401, detail="用户被禁用")

    token = create_access_token(str(user.id))
    return Token(access_token=token)


@router.get("/me", response_model=UserOut)
def me(user: User = Depends(get_current_user)):
    return user
