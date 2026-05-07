import datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, ConfigDict, field_validator


class ItemCompraRequest(BaseModel):
    item_id: int
    quantidade: Decimal
    custo_total: Decimal

    @field_validator("quantidade", "custo_total")
    @classmethod
    def must_be_positive(cls, v: Decimal) -> Decimal:
        if v <= 0:
            raise ValueError("deve ser maior que zero")
        return v


class CompraCreateRequest(BaseModel):
    fornecedor_id: Optional[int] = None
    data_compra: datetime.date
    numero_nota: Optional[str] = None
    itens: list[ItemCompraRequest]

    @field_validator("itens")
    @classmethod
    def must_have_items(cls, v: list[ItemCompraRequest]) -> list[ItemCompraRequest]:
        if not v:
            raise ValueError("deve ter ao menos 1 item")
        return v


class ItemCompraResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    item_id: int
    item_nome: str
    quantidade: Decimal
    custo_unitario: Decimal
    custo_total: Decimal


class CompraResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    fornecedor_id: Optional[int]
    fornecedor_nome: Optional[str]
    data_compra: datetime.date
    numero_nota: Optional[str]
    total: Decimal
    itens: list[ItemCompraResponse]
    created_at: datetime.datetime
