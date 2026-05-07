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
