from datetime import datetime
from typing import Optional

from pydantic import BaseModel

VALID_SCREENS = [
    "dashboard", "comandas", "compras", "estoque",
    "cadastros", "relatorios", "configuracoes", "gestao_usuarios",
]


class ProfileCreate(BaseModel):
    name: str
    description: Optional[str] = None
    screens: list[str]


class ProfileUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    screens: Optional[list[str]] = None


class ProfileResponse(BaseModel):
    id: int
    tenant_id: int
    name: str
    description: Optional[str]
    is_system: bool
    permissions: list[str]
    user_count: int
    created_at: datetime

    model_config = {"from_attributes": True}
