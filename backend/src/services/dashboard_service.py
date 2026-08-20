import datetime
from decimal import ROUND_HALF_UP, Decimal

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from src.models.compras import Compra
from src.models.contas_pagar import ContaPagar
from src.models.fornecedores import Fornecedor
from src.repositories import dashboard_repository as dr
from src.schemas.dashboard_schemas import (
    ComandaAbertaItem,
    DashboardHistoricoItem,
    DashboardResponse,
    DashboardResumoAnualItem,
    DiaFaturamento,
    EntregaEsperadaItem,
    HoraBucket,
    InsumoCriticoItem,
    ProdutoTop,
)


def dashboard(db: Session) -> DashboardResponse:
    fechadas_hoje = dr.comandas_fechadas_hoje(db)
    ids_hoje = [c.id for c in fechadas_hoje]

    faturamento_hoje = sum((c.total or Decimal("0") for c in fechadas_hoje), Decimal("0"))
    qtd_fechadas = len(fechadas_hoje)
    ticket_medio = (
        (faturamento_hoje / qtd_fechadas).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
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

    hoje = datetime.date.today()
    em_7_dias = hoje + datetime.timedelta(days=7)

    contas_vencendo = db.execute(
        select(func.count(), func.sum(ContaPagar.valor)).where(
            ContaPagar.status.in_(["pendente", "vencido"]),
            ContaPagar.data_vencimento >= hoje,
            ContaPagar.data_vencimento <= em_7_dias,
        )
    ).one()
    contas_vencendo_qtd = contas_vencendo[0] or 0
    contas_vencendo_total = contas_vencendo[1] or Decimal("0")

    compras_agendadas = db.execute(
        select(Compra).where(
            Compra.status == "confirmado",
            Compra.data_prevista_recebimento <= em_7_dias,
        )
    ).scalars().all()

    entregas = []
    for c in compras_agendadas:
        if c.data_prevista_recebimento is None:
            continue
        nome = None
        if c.fornecedor_id:
            f = db.execute(select(Fornecedor).where(Fornecedor.id == c.fornecedor_id)).scalar_one_or_none()
            nome = f.nome if f else None
        entregas.append(
            EntregaEsperadaItem(
                compra_id=c.id,
                fornecedor_nome=nome or "Sem fornecedor",
                data_prevista_recebimento=c.data_prevista_recebimento,
                total=c.total or Decimal("0"),
            )
        )

    insumos_criticos = [InsumoCriticoItem(**i) for i in dr.insumos_abaixo_critico(db)]

    # Variações temporais derivadas de ultimos_30 (sem queries extras)
    fat_map_30 = {item.data: item.faturamento for item in ultimos_30}
    ontem = hoje - datetime.timedelta(days=1)
    faturamento_ontem = fat_map_30.get(ontem, 0.0)
    faturamento_7d = sum(fat_map_30.get(hoje - datetime.timedelta(days=i), 0.0) for i in range(7))
    faturamento_7d_anterior = sum(fat_map_30.get(hoje - datetime.timedelta(days=i), 0.0) for i in range(7, 14))

    primeiro_mes_atual = datetime.date(hoje.year, hoje.month, 1)
    ultimo_mes_ant = primeiro_mes_atual - datetime.timedelta(days=1)
    mes_ant = ultimo_mes_ant.month
    ano_ant = ultimo_mes_ant.year
    faturamento_mes_atual = dr.faturamento_mes(db, hoje.year, hoje.month)
    faturamento_mes_anterior = dr.faturamento_mes(db, ano_ant, mes_ant)

    return DashboardResponse(
        faturamento_hoje=faturamento_hoje,
        ticket_medio_hoje=ticket_medio,
        cmv_hoje=cmv,
        comandas_abertas=len(abertas_lista),
        comandas_fechadas_hoje=qtd_fechadas,
        lucro_estimado_hoje=lucro_estimado,
        faturamento_por_hora=faturamento_por_hora,
        top_10_produtos=top_10,
        ultimos_30_dias=ultimos_30,
        heatmap_mes=heatmap,
        comandas_abertas_lista=abertas_lista,
        contas_vencendo_7_dias_total=contas_vencendo_total,
        contas_vencendo_7_dias_qtd=contas_vencendo_qtd,
        entregas_esperadas_7_dias=entregas,
        insumos_criticos=insumos_criticos,
        faturamento_ontem=faturamento_ontem,
        faturamento_7d=faturamento_7d,
        faturamento_7d_anterior=faturamento_7d_anterior,
        faturamento_mes_atual=faturamento_mes_atual,
        faturamento_mes_anterior=faturamento_mes_anterior,
    )


def dashboard_historico(
    db: Session, inicio: datetime.date, fim: datetime.date
) -> list[DashboardHistoricoItem]:
    rows = dr.historico_periodo(db, inicio, fim)
    return [DashboardHistoricoItem(**r) for r in rows]


def dashboard_resumo_anual(db: Session, ano: int) -> list[DashboardResumoAnualItem]:
    rows = dr.resumo_anual(db, ano)
    return [DashboardResumoAnualItem(**r) for r in rows]
