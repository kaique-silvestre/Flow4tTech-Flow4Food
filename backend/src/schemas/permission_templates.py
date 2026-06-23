from typing import Optional

from pydantic import BaseModel


class TemplateCreate(BaseModel):
    nome: str
    descricao: Optional[str] = None
    screens: list[str]


class TemplateUpdate(BaseModel):
    nome: Optional[str] = None
    descricao: Optional[str] = None
    screens: Optional[list[str]] = None


class TemplateResponse(BaseModel):
    id: int
    tenant_id: Optional[int]
    nome: str
    descricao: Optional[str]
    is_system: bool
    screens: list[str]

    model_config = {"from_attributes": True}


class AssignTemplateRequest(BaseModel):
    template_id: Optional[int] = None
