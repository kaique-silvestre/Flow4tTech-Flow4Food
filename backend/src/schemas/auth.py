from pydantic import BaseModel


class LoginRequest(BaseModel):
    senha: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int = 43200
