from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict


class ComissaoResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    garcom_id: int
    comanda_id: int
    valor: Decimal
    percentual: Decimal
    pago: bool
    created_at: datetime


class ComissaoUpdateRequest(BaseModel):
    valor: Decimal


class GarcomStatsResponse(BaseModel):
    garcom_id: int
    total_comandas: int
    comandas_fechadas: int
    comissao_pendente: Decimal
    comissoes: list[ComissaoResponse]
