import datetime
from decimal import Decimal
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, field_validator, model_validator

TipoCompra = Literal["imediata", "agendada", "a_prazo"]


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
    tipo_compra: TipoCompra = "imediata"
    data_prevista_recebimento: Optional[datetime.date] = None
    data_prevista_pagamento: Optional[datetime.date] = None
    itens: list[ItemCompraRequest]

    @field_validator("itens")
    @classmethod
    def must_have_items(cls, v: list[ItemCompraRequest]) -> list[ItemCompraRequest]:
        if not v:
            raise ValueError("deve ter ao menos 1 item")
        return v

    @model_validator(mode="after")
    def validate_datas_por_tipo(self) -> "CompraCreateRequest":
        if self.tipo_compra == "agendada" and not self.data_prevista_recebimento:
            raise ValueError("data_prevista_recebimento é obrigatória para compra agendada")
        if self.tipo_compra in ("agendada", "a_prazo") and not self.data_prevista_pagamento:
            raise ValueError("data_prevista_pagamento é obrigatória para compra agendada ou a prazo")
        return self


class ItemCompraResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    item_id: int
    item_nome: str
    quantidade: Decimal
    custo_unitario: Decimal
    custo_total: Decimal


class CompraPatchRequest(BaseModel):
    fornecedor_id: Optional[int] = None
    data_compra: Optional[datetime.date] = None
    numero_nota: Optional[str] = None
    data_prevista_recebimento: Optional[datetime.date] = None
    data_prevista_pagamento: Optional[datetime.date] = None


class CompraResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    fornecedor_id: Optional[int]
    fornecedor_nome: Optional[str]
    data_compra: datetime.date
    numero_nota: Optional[str]
    total: Decimal
    status: str
    tipo_compra: str = "imediata"
    data_prevista_recebimento: Optional[datetime.date] = None
    data_real_recebimento: Optional[datetime.date] = None
    data_prevista_pagamento: Optional[datetime.date] = None
    itens: list[ItemCompraResponse]
    created_at: datetime.datetime
    warning: Optional[str] = None


class ComprasPageResponse(BaseModel):
    itens: list[CompraResponse]
    total: int
    pagina: int
    por_pagina: int
    total_paginas: int
    total_periodo: Decimal
