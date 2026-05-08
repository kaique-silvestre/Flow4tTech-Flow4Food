import datetime
from decimal import Decimal

from pydantic import BaseModel


class HoraBucket(BaseModel):
    hora: int
    faturamento: Decimal


class ProdutoTop(BaseModel):
    item_id: int
    nome: str
    quantidade: int
    faturamento: Decimal


class DiaFaturamento(BaseModel):
    data: datetime.date
    faturamento: Decimal


class ComandaAbertaItem(BaseModel):
    id: int
    identificacao: str
    qtd_itens: int
    total: Decimal
    aberta_ha_minutos: int


class DashboardResponse(BaseModel):
    faturamento_hoje: Decimal
    ticket_medio_hoje: Decimal
    comandas_abertas: int
    comandas_fechadas_hoje: int
    lucro_estimado_hoje: Decimal
    faturamento_por_hora: list[HoraBucket]
    top_10_produtos: list[ProdutoTop]
    ultimos_30_dias: list[DiaFaturamento]
    heatmap_mes: list[DiaFaturamento]
    comandas_abertas_lista: list[ComandaAbertaItem]
