from pydantic import BaseModel, ConfigDict, Field


class CategoriaCreateRequest(BaseModel):
    nome: str = Field(..., min_length=1)


class CategoriaUpdateRequest(BaseModel):
    nome: str = Field(..., min_length=1)


class CategoriaResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nome: str
