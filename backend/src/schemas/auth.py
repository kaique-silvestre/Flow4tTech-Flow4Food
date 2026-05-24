
from pydantic import BaseModel


class LoginRequest(BaseModel):
    identifier: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class AccessTokenResponse(BaseModel):
    access_token: str


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str


class UserInfo(BaseModel):
    user_id: int
    tenant_id: int
    username: str
    name: str
    profile_id: int
    profile_name: str
    permissions: list[str]


class ForgotPasswordRequest(BaseModel):
    email: str


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str


class GenericMessage(BaseModel):
    message: str


class ResetTokenInfo(BaseModel):
    name: str
