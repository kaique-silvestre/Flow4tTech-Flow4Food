from datetime import datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, Field


class LancarConsumoRequest(BaseModel):
    consumidor_id: int
    produto_id: int
    quantidade: Decimal = Field(gt=0)
    observacao: Optional[str] = None


class LancarConsumoBatchItem(BaseModel):
    produto_id: int
    quantidade: Decimal = Field(gt=0)
    observacao: Optional[str] = None


class LancarConsumoBatchRequest(BaseModel):
    consumidor_id: int
    itens: list[LancarConsumoBatchItem] = Field(min_length=1)


class ItemConsumoInternoResponse(BaseModel):
    id: int
    consumidor_id: int
    consumidor_nome: str
    produto_id: int
    produto_nome: str
    quantidade: Decimal
    custo_unitario: Decimal
    subtotal: Decimal
    observacao: Optional[str]
    created_at: datetime

    model_config = {"from_attributes": True}


class LancarConsumoBatchResponse(BaseModel):
    itens: list[ItemConsumoInternoResponse]


class ResumoConsumidorResponse(BaseModel):
    consumidor_id: int
    consumidor_nome: str
    itens_no_mes: int
    total: Decimal
    ultima_atividade: Optional[datetime]
