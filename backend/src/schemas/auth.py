
from typing import Optional

from pydantic import BaseModel, Field


class LoginRequest(BaseModel):
    identifier: str
    password: str = Field(..., max_length=72)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class AccessTokenResponse(BaseModel):
    access_token: str


class ChangePasswordRequest(BaseModel):
    current_password: str = Field(..., max_length=72)
    new_password: str = Field(..., max_length=72)


class UserInfo(BaseModel):
    user_id: int
    tenant_id: int
    username: str
    name: str
    profile_id: Optional[int]  # noqa: UP045
    profile_name: Optional[str]  # noqa: UP045
    permissions: list[str]


class ForgotPasswordRequest(BaseModel):
    email: str


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str = Field(..., max_length=72)


class GenericMessage(BaseModel):
    message: str


class ResetTokenInfo(BaseModel):
    name: str
