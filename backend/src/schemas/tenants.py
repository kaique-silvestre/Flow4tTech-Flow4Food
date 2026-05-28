from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, Field


class TenantCreate(BaseModel):
    nome_fantasia: str = Field(..., min_length=1, max_length=200)
    cnpj: Optional[str] = Field(None, max_length=18)
    admin_name: str = Field(..., min_length=1, max_length=200)
    admin_username: str = Field(..., min_length=3, max_length=100)
    admin_email: EmailStr
    admin_password: str = Field(..., min_length=6)


class TenantUpdate(BaseModel):
    nome_fantasia: Optional[str] = Field(None, min_length=1, max_length=200)
    status: Optional[str] = Field(None)


class AssinaturaInfo(BaseModel):
    id: int
    status: str
    data_inicio: datetime
    data_vencimento: Optional[datetime] = None

    model_config = {"from_attributes": True}


class TenantResponse(BaseModel):
    id: int
    nome_fantasia: str
    cnpj: Optional[str] = None
    status: str
    admin_user_id: Optional[int] = None
    created_at: datetime
    assinatura: Optional[AssinaturaInfo] = None

    model_config = {"from_attributes": True}
