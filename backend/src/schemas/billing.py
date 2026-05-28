import datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, Field


class PlanoCreate(BaseModel):
    nome: str = Field(..., min_length=1, max_length=100)
    descricao: Optional[str] = None
    preco_mensal: Decimal = Field(..., gt=0)


class PlanoInfo(BaseModel):
    id: int
    nome: str
    descricao: Optional[str]
    preco_mensal: Decimal
    ativo: bool

    model_config = {"from_attributes": True}


class PagamentoCreate(BaseModel):
    valor: Decimal = Field(..., gt=0)
    data_pagamento: datetime.date
    data_vencimento: Optional[datetime.date] = None
    gateway_ref: Optional[str] = None


class PagamentoInfo(BaseModel):
    id: int
    tenant_id: int
    valor: Decimal
    data_pagamento: datetime.date
    data_vencimento: Optional[datetime.date]
    gateway_ref: Optional[str]

    model_config = {"from_attributes": True}


VALID_STATUS = {"trial", "ativa", "vencida", "cancelada", "suspensa"}


class AssinaturaUpdate(BaseModel):
    status: str
    data_vencimento: Optional[datetime.date] = None

    def model_post_init(self, __context) -> None:
        if self.status not in VALID_STATUS:
            raise ValueError(f"status deve ser um de: {', '.join(sorted(VALID_STATUS))}")
