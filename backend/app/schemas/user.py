from pydantic import BaseModel, EmailStr, Field, ConfigDict
from models.user import UserRole
from datetime import datetime


class UserCreate(BaseModel):
    username: str = Field(min_length=3, max_length=50)
    password: str = Field(min_length=6, max_length=72)
    real_name: str | None = Field(default=None)
    email: EmailStr | None = Field(default=None)


class UserLogin(BaseModel):
    username: str = Field(min_length=3, max_length=50)
    password: str = Field(min_length=6, max_length=72)


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    username: str
    real_name: str | None = Field(default=None)
    role: UserRole
    status: bool
    created_at: datetime


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
