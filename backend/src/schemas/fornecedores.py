from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class FornecedorCreateRequest(BaseModel):
    nome: str = Field(..., min_length=1)
    telefone: Optional[str] = None
    email: Optional[str] = None


class FornecedorUpdateRequest(BaseModel):
    nome: str = Field(..., min_length=1)
    telefone: Optional[str] = None
    email: Optional[str] = None


class FornecedorResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nome: str
    telefone: Optional[str]
    email: Optional[str]
    ativo: bool = True


class FornecedorPageResponse(BaseModel):
    itens: list[FornecedorResponse]
    total: int
    pagina: int
    por_pagina: int
    total_paginas: int
