from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, computed_field

from src.models.insumos import UnidadeBase


class InsumoCreateRequest(BaseModel):
    nome: str = Field(..., min_length=1)
    categoria_id: Optional[int] = None
    unidade_base: UnidadeBase
    quantidade_caixa: Optional[int] = None


class InsumoUpdateRequest(BaseModel):
    nome: str = Field(..., min_length=1)
    categoria_id: Optional[int] = None
    unidade_base: UnidadeBase
    quantidade_caixa: Optional[int] = None
    nivel_critico: Optional[Decimal] = None


class InsumoResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nome: str
    categoria_id: Optional[int]
    unidade_base: str
    quantidade_caixa: Optional[int]
    custo_medio: Optional[Decimal]
    estoque_atual: Decimal
    estoque_reservado: Decimal
    nivel_critico: Optional[Decimal]
    ativo: bool

    @computed_field  # type: ignore[misc]
    @property
    def estoque_disponivel(self) -> Decimal:
        return self.estoque_atual - self.estoque_reservado


class InsumoPageResponse(BaseModel):
    itens: list[InsumoResponse]
    total: int
    pagina: int
    por_pagina: int
    total_paginas: int
