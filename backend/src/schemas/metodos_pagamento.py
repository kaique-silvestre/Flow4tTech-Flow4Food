from pydantic import BaseModel, ConfigDict, Field


class MetodoPagamentoCreateRequest(BaseModel):
    nome: str = Field(..., min_length=1)


class MetodoPagamentoUpdateRequest(BaseModel):
    nome: str = Field(..., min_length=1)
    ativo: bool = True


class MetodoPagamentoResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nome: str
    ativo: bool
