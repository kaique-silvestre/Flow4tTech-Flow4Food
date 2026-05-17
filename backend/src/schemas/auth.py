
from pydantic import BaseModel


class LoginRequest(BaseModel):
    identifier: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int = 28800  # 8 horas


class UserInfo(BaseModel):
    user_id: int
    tenant_id: int
    username: str
    name: str
    profile_id: int
    profile_name: str
    permissions: list[str]
