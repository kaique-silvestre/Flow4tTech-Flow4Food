from decimal import Decimal

from sqlalchemy.orm import Session

from src.repositories import dashboard_repository as dr
from src.schemas.dashboard_schemas import (
    ComandaAbertaItem,
    DashboardResponse,
    DiaFaturamento,
    HoraBucket,
    ProdutoTop,
)


def dashboard(db: Session) -> DashboardResponse:
    fechadas_hoje = dr.comandas_fechadas_hoje(db)
    ids_hoje = [c.id for c in fechadas_hoje]

    faturamento_hoje = sum((c.total or Decimal("0") for c in fechadas_hoje), Decimal("0"))
    qtd_fechadas = len(fechadas_hoje)
    ticket_medio = (
        (faturamento_hoje / qtd_fechadas).quantize(Decimal("0.01"))
        if qtd_fechadas > 0
        else Decimal("0")
    )

    cmv = dr.cmv_hoje(db, ids_hoje)
    lucro_estimado = faturamento_hoje - cmv

    faturamento_por_hora = [HoraBucket(**h) for h in dr.faturamento_por_hora_hoje(db, ids_hoje)]
    top_10 = [ProdutoTop(**p) for p in dr.top_10_produtos_30d(db)]
    ultimos_30 = [DiaFaturamento(**d) for d in dr.faturamento_ultimos_30d(db)]
    heatmap = [DiaFaturamento(**d) for d in dr.heatmap_mes_atual(db)]

    abertas_raw = dr.comandas_abertas_com_detalhes(db)
    abertas_lista = [ComandaAbertaItem(**a) for a in abertas_raw]

    return DashboardResponse(
        faturamento_hoje=faturamento_hoje,
        ticket_medio_hoje=ticket_medio,
        comandas_abertas=len(abertas_lista),
        comandas_fechadas_hoje=qtd_fechadas,
        lucro_estimado_hoje=lucro_estimado,
        faturamento_por_hora=faturamento_por_hora,
        top_10_produtos=top_10,
        ultimos_30_dias=ultimos_30,
        heatmap_mes=heatmap,
        comandas_abertas_lista=abertas_lista,
    )
