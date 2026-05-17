import datetime

from pydantic import BaseModel


class HoraBucket(BaseModel):
    hora: int
    faturamento: float


class ProdutoTop(BaseModel):
    item_id: int
    nome: str
    quantidade: int
    faturamento: float


class DiaFaturamento(BaseModel):
    data: datetime.date
    faturamento: float


class ComandaAbertaItem(BaseModel):
    id: int
    identificacao: str
    qtd_itens: int
    total: float
    aberta_ha_minutos: int


class DashboardHistoricoItem(BaseModel):
    data: datetime.date
    faturamento: float
    total_compras: float


class DashboardResumoAnualItem(BaseModel):
    mes: int
    faturamento: float
    total_compras: float


class EntregaEsperadaItem(BaseModel):
    compra_id: int
    fornecedor_nome: str
    data_prevista_recebimento: datetime.date
    total: float


class DashboardResponse(BaseModel):
    faturamento_hoje: float
    ticket_medio_hoje: float
    cmv_hoje: float
    comandas_abertas: int
    comandas_fechadas_hoje: int
    lucro_estimado_hoje: float
    faturamento_por_hora: list[HoraBucket]
    top_10_produtos: list[ProdutoTop]
    ultimos_30_dias: list[DiaFaturamento]
    heatmap_mes: list[DiaFaturamento]
    comandas_abertas_lista: list[ComandaAbertaItem]
    contas_vencendo_7_dias_total: float = 0.0
    contas_vencendo_7_dias_qtd: int = 0
    entregas_esperadas_7_dias: list[EntregaEsperadaItem] = []
