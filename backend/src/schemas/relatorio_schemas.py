import datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel


class PagamentoResumo(BaseModel):
    metodo_id: int
    metodo_nome: str
    total: Decimal
    qtd: int


class ComandaRelatorioItem(BaseModel):
    id: int
    identificacao: str
    garcom_nome: str
    total: Decimal
    desconto_percentual: Optional[Decimal]
    desconto_valor: Optional[Decimal]
    cortesias: Decimal
    data_fechamento: datetime.datetime
    pagamentos: list[PagamentoResumo]


class VendasDoDiaResponse(BaseModel):
    data: datetime.date
    qtd_comandas: int
    faturamento_bruto: Decimal
    total_descontos: Decimal
    total_cortesias: Decimal
    faturamento_liquido: Decimal
    por_metodo: list[PagamentoResumo]
    comandas: list[ComandaRelatorioItem]


class HistoricoResponse(BaseModel):
    total: int
    comandas: list[ComandaRelatorioItem]


class FechamentoCaixaResponse(BaseModel):
    data: datetime.date
    qtd_comandas: int
    faturamento_bruto: Decimal
    descontos: Decimal
    cortesias: Decimal
    faturamento_liquido: Decimal
    por_metodo: list[PagamentoResumo]
