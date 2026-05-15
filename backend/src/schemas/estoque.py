import datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, ConfigDict, field_validator

from src.models.movimentos_estoque import MotivoPerda


class SaldoItemResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nome: str
    categoria_id: Optional[int]
    categoria_nome: Optional[str]
    unidade_base: str
    estoque_atual: Decimal
    estoque_reservado: Decimal
    estoque_disponivel: Decimal
    custo_medio: Optional[Decimal]
    nivel_critico: Optional[Decimal]


class InsumoCriticoResponse(BaseModel):
    id: int
    nome: str
    unidade_base: str
    estoque_disponivel: Decimal
    nivel_critico: Decimal


class BaixaSemVendaRequest(BaseModel):
    item_id: int
    quantidade: Decimal
    motivo: MotivoPerda
    observacao: Optional[str] = None

    @field_validator("quantidade")
    @classmethod
    def must_be_positive(cls, v: Decimal) -> Decimal:
        if v <= 0:
            raise ValueError("deve ser maior que zero")
        return v


class MovimentoResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    item_id: int
    item_nome: str
    unidade_base: str
    tipo: str
    quantidade: Decimal
    custo_unitario: Optional[Decimal]
    saldo_apos: Decimal
    motivo: Optional[str]
    observacao: Optional[str]
    compra_id: Optional[int]
    created_at: datetime.datetime


class MovimentoListResponse(BaseModel):
    itens: list[MovimentoResponse]
    total: int
    pagina: int
    por_pagina: int
