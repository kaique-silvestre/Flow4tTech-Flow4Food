from pydantic import BaseModel, ConfigDict, Field


class GarcomCreateRequest(BaseModel):
    nome: str = Field(..., min_length=1)


class GarcomUpdateRequest(BaseModel):
    nome: str = Field(..., min_length=1)
    ativo: bool = True


class GarcomResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nome: str
    ativo: bool


class GarcomPageResponse(BaseModel):
    itens: list[GarcomResponse]
    total: int
    pagina: int
    por_pagina: int
    total_paginas: int
