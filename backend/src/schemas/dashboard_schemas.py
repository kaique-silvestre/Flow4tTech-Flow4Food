import datetime
from decimal import Decimal

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
    total: Decimal


class InsumoCriticoItem(BaseModel):
    nome: str
    estoque_atual: float
    nivel_critico: float
    unidade_base: str


class DashboardResponse(BaseModel):
    faturamento_hoje: Decimal
    ticket_medio_hoje: Decimal
    cmv_hoje: Decimal
    comandas_abertas: int
    comandas_fechadas_hoje: int
    lucro_estimado_hoje: Decimal
    faturamento_por_hora: list[HoraBucket]
    top_10_produtos: list[ProdutoTop]
    ultimos_30_dias: list[DiaFaturamento]
    heatmap_mes: list[DiaFaturamento]
    comandas_abertas_lista: list[ComandaAbertaItem]
    contas_vencendo_7_dias_total: Decimal = Decimal("0")
    contas_vencendo_7_dias_qtd: int = 0
    entregas_esperadas_7_dias: list[EntregaEsperadaItem] = []
    insumos_criticos: list[InsumoCriticoItem] = []
    faturamento_ontem: float = 0.0
    faturamento_7d: float = 0.0
    faturamento_7d_anterior: float = 0.0
    faturamento_mes_atual: Decimal = Decimal("0")
    faturamento_mes_anterior: Decimal = Decimal("0")
