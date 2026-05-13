import datetime
from decimal import Decimal
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field

from src.models.itens_comanda import MotivoCancelamento
from src.schemas.fechamento import PagamentoResponse


class ComandaCreateRequest(BaseModel):
    identificacao: str = Field(..., min_length=1)
    tipo_identificacao: Literal["nome", "mesa"]
    garcom_id: int
    pessoas: list[str] = Field(..., min_length=1)


class LancarItemRequest(BaseModel):
    item_id: int
    quantidade: Decimal = Field(..., gt=0)
    pessoa_associada: Optional[str] = None
    observacao: Optional[str] = None
    cortesia: bool = False
    version: int


class EditarItemRequest(BaseModel):
    quantidade: Optional[Decimal] = Field(None, gt=0)
    pessoa_associada: Optional[str] = None
    observacao: Optional[str] = None
    version: int


class CancelarItemRequest(BaseModel):
    motivo: MotivoCancelamento
    estornado: bool = False
    version: int


class PatchComandaRequest(BaseModel):
    identificacao: Optional[str] = Field(None, min_length=1)
    garcom_id: Optional[int] = None
    pessoas: Optional[list[str]] = Field(None, min_length=1)


class ItemComandaResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    item_id: int
    item_nome: str
    quantidade: Decimal
    preco_unitario: Decimal
    subtotal: Decimal
    pessoa_associada: Optional[str]
    observacao: Optional[str]
    cortesia: bool
    cancelado: bool
    motivo_cancelamento: Optional[str]
    estornado: bool
    created_at: datetime.datetime


class ComandaResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    identificacao: str
    tipo_identificacao: str
    garcom_id: int
    garcom_nome: str
    status: str
    version: int
    pessoas: list[str]
    total_parcial: Decimal
    itens_ativos: list[ItemComandaResponse]
    created_at: datetime.datetime
    tempo_aberta_minutos: int
    desconto_percentual: Optional[Decimal] = None
    desconto_valor: Optional[Decimal] = None
    total: Optional[Decimal] = None
    saldo_pendente: Optional[Decimal] = None
    data_fechamento: Optional[datetime.datetime] = None
    pagamentos: list[PagamentoResponse] = []
    itens_negativos: list[str] = []
    estoque_insuficiente: list[str] = []
