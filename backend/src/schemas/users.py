from datetime import datetime
from typing import Optional

from pydantic import BaseModel, field_validator


class UserCreate(BaseModel):
    name: str
    username: str
    email: Optional[str] = None
    profile_id: int
    password: str
    is_active: bool = True

    @field_validator("password")
    @classmethod
    def password_min_length(cls, v: str) -> str:
        if len(v) < 6:
            raise ValueError("Senha deve ter no mínimo 6 caracteres")
        return v


class UserUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    profile_id: Optional[int] = None
    is_active: Optional[bool] = None


class UserResponse(BaseModel):
    id: int
    tenant_id: int
    profile_id: int
    profile_name: str
    name: str
    username: str
    email: Optional[str]
    is_active: bool
    last_login: Optional[datetime]
    created_at: datetime

    model_config = {"from_attributes": True}


class UsernameCheckResponse(BaseModel):
    available: bool


class ResetPasswordResponse(BaseModel):
    temp_password: str
