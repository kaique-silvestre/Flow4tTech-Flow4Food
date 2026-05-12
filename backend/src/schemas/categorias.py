from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class CategoriaCreateRequest(BaseModel):
    nome: str = Field(..., min_length=1)
    parent_id: Optional[int] = None


class CategoriaUpdateRequest(BaseModel):
    nome: str = Field(..., min_length=1)
    parent_id: Optional[int] = None


class CategoriaResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nome: str
    parent_id: Optional[int] = None
    ativo: bool = True
    children: list["CategoriaResponse"] = []


CategoriaResponse.model_rebuild()
