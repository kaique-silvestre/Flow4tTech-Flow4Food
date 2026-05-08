from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class FichaTecnicaItemRequest(BaseModel):
    insumo_id: int
    quantidade: Decimal = Field(..., gt=0)


class ProdutoCreateRequest(BaseModel):
    nome: str = Field(..., min_length=1)
    categoria_id: Optional[int] = None
    preco_venda: Optional[Decimal] = None
    ficha_tecnica: Optional[list[FichaTecnicaItemRequest]] = None


class ProdutoUpdateRequest(BaseModel):
    nome: str = Field(..., min_length=1)
    categoria_id: Optional[int] = None
    preco_venda: Optional[Decimal] = None
    ficha_tecnica: Optional[list[FichaTecnicaItemRequest]] = None


class FichaTecnicaItemResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    insumo_id: int
    insumo_nome: str
    quantidade: Decimal
    unidade_base: str


class ProdutoResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nome: str
    categoria_id: Optional[int]
    preco_venda: Optional[Decimal]
    ativo: bool
    ficha_tecnica: Optional[list[FichaTecnicaItemResponse]] = None
