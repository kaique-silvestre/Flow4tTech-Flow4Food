import datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel


class EstabelecimentoInfo(BaseModel):
    nome: str
    cnpj: Optional[str]
    endereco: Optional[str]
    telefone: Optional[str]


class ItemComprovanteRow(BaseModel):
    nome: str
    quantidade: Decimal
    preco_unitario: Decimal
    subtotal: Decimal
    cortesia: bool


class PagamentoComprovanteRow(BaseModel):
    metodo_nome: str
    valor: Decimal
    valor_nota: Optional[Decimal] = None
    troco: Optional[Decimal] = None


class ComprovanteResponse(BaseModel):
    comanda_id: int
    identificacao: str
    tipo_identificacao: str
    garcom_nome: str
    data_fechamento: Optional[datetime.datetime]
    estabelecimento: EstabelecimentoInfo
    itens: list[ItemComprovanteRow]
    subtotal: Decimal
    desconto_percentual: Optional[Decimal]
    desconto_valor: Optional[Decimal]
    total: Optional[Decimal]
    pagamentos: list[PagamentoComprovanteRow]
