import datetime
from decimal import Decimal
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field


class AbrirCaixaRequest(BaseModel):
    valor_abertura: Decimal = Field(..., ge=0)


class FecharCaixaRequest(BaseModel):
    valor_informado: Decimal = Field(..., ge=0)
    observacao: Optional[str] = None


class MovimentoCaixaRequest(BaseModel):
    tipo: Literal["sangria", "suprimento"]
    valor: Decimal = Field(..., gt=0)
    motivo: str = Field(..., min_length=1)


class CaixaMovimentoResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    sessao_id: int
    tipo: str
    valor: Decimal
    motivo: str
    user_id: int
    created_at: datetime.datetime


class CaixaSessaoResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    status: str
    valor_abertura: Decimal
    valor_informado: Optional[Decimal] = None
    valor_esperado: Optional[Decimal] = None
    diferenca: Optional[Decimal] = None
    aberto_por_user_id: int
    fechado_por_user_id: Optional[int] = None
    opened_at: datetime.datetime
    closed_at: Optional[datetime.datetime] = None
    observacao: Optional[str] = None
    created_at: datetime.datetime
    movimentos: list[CaixaMovimentoResponse] = []
