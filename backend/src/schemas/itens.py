from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from src.models.itens import TipoItem, UnidadeBase


class ComponenteRequest(BaseModel):
    insumo_id: int
    quantidade: Decimal = Field(..., gt=0)


class ComponenteResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    insumo_id: int
    insumo_nome: str
    quantidade: Decimal
    unidade_base: str


class ItemCreateRequest(BaseModel):
    nome: str = Field(..., min_length=1)
    categoria_id: Optional[int] = None
    tipo: TipoItem
    vendavel: bool = False
    unidade_base: UnidadeBase
    quantidade_caixa: Optional[int] = None
    preco_venda: Optional[Decimal] = None
    ficha_tecnica: Optional[list[ComponenteRequest]] = None


class ItemUpdateRequest(BaseModel):
    nome: str = Field(..., min_length=1)
    categoria_id: Optional[int] = None
    tipo: TipoItem
    vendavel: bool = False
    unidade_base: UnidadeBase
    quantidade_caixa: Optional[int] = None
    preco_venda: Optional[Decimal] = None
    ficha_tecnica: Optional[list[ComponenteRequest]] = None


class ItemResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nome: str
    categoria_id: Optional[int]
    tipo: str
    vendavel: bool
    unidade_base: str
    quantidade_caixa: Optional[int]
    custo_medio: Optional[Decimal]
    preco_venda: Optional[Decimal]
    estoque_atual: Decimal
    ativo: bool
    custo_composto: Optional[Decimal] = None
    cmv_percentual: Optional[Decimal] = None
    componentes: Optional[list[ComponenteResponse]] = None
