import datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel


class CockpitItem(BaseModel):
    tipo: str  # evento | promocao | conta_pagar | entrega_insumo
    referencia_id: int
    data_referencia: datetime.date
    descricao: str
    hora_inicio: Optional[datetime.time] = None
    hora_fim: Optional[datetime.time] = None
    valor: Optional[Decimal] = None
    fornecedor_nome: Optional[str] = None
    itens: list[str] = []

    model_config = {"from_attributes": True}
