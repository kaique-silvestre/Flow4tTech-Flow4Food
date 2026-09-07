import datetime
from decimal import ROUND_HALF_UP, Decimal

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from src.models.contas_pagar import ContaPagar
from src.core.errors import AppError, ErrorCode
from src.repositories import dashboard_repository as dr
from src.schemas.dashboard_schemas import (
    ComandaAbertaItem,
    ComissaoGarcomResumo,
    DashboardHistoricoItem,
    DashboardResponse,
    DashboardResumoAnualItem,
    DiaFaturamento,
    EntregaEsperadaItem,
    HoraBucket,
    InsumoCriticoItem,
    MotivoPerdaResumo,
    ProdutoTop,
)
from src.schemas.estoque import SaldoItemResponse
from src.schemas.relatorio_schemas import PagamentoResumo
from src.services import estoque_service, relatorio_service

_QTD_INSUMOS_MENOR_ESTOQUE = 5


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
    top_10 = _montar_top_10_produtos(db)
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

    entregas = []
    for compra_agendada in dr.compras_agendadas_com_fornecedor(db, em_7_dias):
        c = compra_agendada["compra"]
        if c.data_prevista_recebimento is None:
            continue
        entregas.append(
            EntregaEsperadaItem(
                compra_id=c.id,
                fornecedor_nome=compra_agendada["fornecedor_nome"] or "Sem fornecedor",
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

    por_metodo_pagamento_hoje = [PagamentoResumo(**p) for p in dr.pagamentos_hoje_por_metodo(db)]

    top_garcons_hoje = relatorio_service.vendas_por_garcom(db, hoje, hoje).garcons[:3]

    perdas_mes = relatorio_service.perdas_cortesias(db, primeiro_mes_atual, hoje)
    perdas_cortesias_mes_total = perdas_mes.total_geral
    perdas_cortesias_mes_por_motivo = [
        MotivoPerdaResumo(motivo=g.motivo, valor=g.total_valor) for g in perdas_mes.grupos
    ]

    comissoes_pendentes = [
        ComissaoGarcomResumo(garcom_id=c["garcom_id"], nome=c["nome"], valor_pendente=c["valor_pendente"])
        for c in dr.comissoes_pendentes_por_garcom(db)
    ]
    comissoes_a_pagar_total = sum((c.valor_pendente for c in comissoes_pendentes), Decimal("0"))

    insumos_menor_estoque = _montar_insumos_menor_estoque(db, insumos_criticos)

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
        por_metodo_pagamento_hoje=por_metodo_pagamento_hoje,
        top_garcons_hoje=top_garcons_hoje,
        perdas_cortesias_mes_total=perdas_cortesias_mes_total,
        perdas_cortesias_mes_por_motivo=perdas_cortesias_mes_por_motivo,
        comissoes_a_pagar_total=comissoes_a_pagar_total,
        comissoes_a_pagar_por_garcom=comissoes_pendentes,
        insumos_menor_estoque=insumos_menor_estoque,
    )


def _montar_top_10_produtos(db: Session) -> list[ProdutoTop]:
    """Top 10 por faturamento (30d), enriquecido com CMV% reusando a classificação
    de `relatorio_service.cmv_por_produto` (mesmo tratamento de produto sem ficha
    técnica: `classificacao="sem_custo"`, sem percentual)."""
    cmv_por_item = {i.item_id: i for i in relatorio_service.cmv_por_produto(db).itens}
    resultado = []
    for p in dr.top_10_produtos_30d(db):
        cmv_item = cmv_por_item.get(p["item_id"])
        cmv_percentual = None
        classificacao_cmv = "sem_custo"
        if cmv_item is not None:
            classificacao_cmv = cmv_item.classificacao
            if cmv_item.margem_percentual is not None:
                cmv_percentual = float(Decimal("100") - cmv_item.margem_percentual)
        resultado.append(
            ProdutoTop(
                **p,
                cmv_percentual=cmv_percentual,
                classificacao_cmv=classificacao_cmv,
            )
        )
    return resultado


def _montar_insumos_menor_estoque(
    db: Session, insumos_criticos: list[InsumoCriticoItem]
) -> list[SaldoItemResponse]:
    """Exatamente 5 insumos com menor `estoque_disponivel`, excluindo os já
    presentes em `insumos_criticos` (críticos e "menor estoque" não se
    sobrepõem no mesmo card)."""
    nomes_criticos = {i.nome for i in insumos_criticos}
    pagina = estoque_service.get_saldo_list(db, ordenar_por_disponivel_asc=True)
    itens = [item for item in pagina.itens if item.nome not in nomes_criticos]
    return itens[:_QTD_INSUMOS_MENOR_ESTOQUE]


def dashboard_historico(
    db: Session, inicio: datetime.date, fim: datetime.date
) -> list[DashboardHistoricoItem]:
    _validar_periodo(inicio, fim)
    rows = dr.historico_periodo(db, inicio, fim)
    return [DashboardHistoricoItem(**r) for r in rows]


def dashboard_resumo_anual(db: Session, ano: int) -> list[DashboardResumoAnualItem]:
    _validar_ano(ano)
    rows = dr.resumo_anual(db, ano)
    return [DashboardResumoAnualItem(**r) for r in rows]


def _validar_periodo(inicio: datetime.date, fim: datetime.date) -> None:
    if inicio > fim:
        raise AppError(ErrorCode.VALIDATION_ERROR, "A data inicial não pode ser posterior à data final.", "inicio")
    if (fim - inicio).days > 366:
        raise AppError(ErrorCode.VALIDATION_ERROR, "O período máximo permitido é de 366 dias.", "fim")


def _validar_ano(ano: int) -> None:
    ano_atual = datetime.date.today().year
    if not 2000 <= ano <= ano_atual + 1:
        raise AppError(ErrorCode.VALIDATION_ERROR, "Informe um ano entre 2000 e o próximo ano.", "ano")
