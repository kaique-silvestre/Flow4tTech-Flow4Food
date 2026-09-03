import datetime
import math
import re
from decimal import ROUND_HALF_UP, Decimal
from typing import Optional

from sqlalchemy.orm import Session

from src.core.errors import AppError, ErrorCode
from src.repositories import relatorio_repository as rr
from src.schemas.relatorio_schemas import (
    CMVPorProdutoResponse,
    CMVProdutoItem,
    ComandaRelatorioItem,
    DREResponse,
    FechamentoCaixaResponse,
    HistoricoResponse,
    HorarioPicoItem,
    ItemSemCusto,
    PagamentoResumo,
    PerdasCortesiasResponse,
    PerdasGrupo,
    PicoVendasHorarioResponse,
    ProdutoMaisVendidoItem,
    ProdutosMaisVendidosResponse,
    VendasDoDiaResponse,
    VendasGarcomItem,
    VendasPorGarcomResponse,
    VendasPorProdutoItem,
    VendasPorProdutoResponse,
)


def _build_comanda_items(
    comandas: list,
    garcom_names: dict[int, str],
    cortesias_map: dict[int, Decimal],
    pagamentos_map: dict[int, list[dict]],
) -> list[ComandaRelatorioItem]:
    items = []
    for c in comandas:
        pagamentos = [PagamentoResumo(**p) for p in pagamentos_map.get(c.id, [])]
        items.append(
            ComandaRelatorioItem(
                id=c.id,
                identificacao=c.identificacao,
                garcom_nome=garcom_names.get(c.garcom_id, "—"),
                total=c.total or Decimal("0"),
                desconto_percentual=c.desconto_percentual,
                desconto_valor=c.desconto_valor,
                cortesias=cortesias_map.get(c.id, Decimal("0")),
                data_fechamento=c.data_fechamento,
                pagamentos=pagamentos,
            )
        )
    return items


def _aggregate(
    db: Session,
    comandas: list,
) -> tuple[dict, dict, dict, list[dict]]:
    ids = [c.id for c in comandas]
    garcom_names = rr._garcom_names(db, list({c.garcom_id for c in comandas}))
    cortesias_map = rr._cortesias_por_comanda(db, ids)
    pagamentos_map = rr._pagamentos_por_comanda(db, ids)
    por_metodo = rr._build_por_metodo(db, ids)
    return garcom_names, cortesias_map, pagamentos_map, por_metodo


def vendas_do_dia(db: Session, data: Optional[datetime.date] = None) -> VendasDoDiaResponse:
    hoje = data if data is not None else datetime.datetime.now(rr.TZ).date()
    start, end = rr._day_utc_range(hoje)
    comandas = rr.list_fechadas_no_periodo(db, start, end)
    garcom_names, cortesias_map, pagamentos_map, por_metodo = _aggregate(db, comandas)

    ids = [c.id for c in comandas]
    net = sum((c.total or Decimal("0") for c in comandas), Decimal("0"))
    descontos = sum((c.desconto_valor or Decimal("0") for c in comandas), Decimal("0"))
    cortesias_total = sum(cortesias_map.values(), Decimal("0"))
    comissoes = rr.comissoes_total_por_comanda_ids(db, ids)

    return VendasDoDiaResponse(
        data=hoje,
        qtd_comandas=len(comandas),
        faturamento_bruto=net + descontos,
        total_descontos=descontos,
        total_cortesias=cortesias_total,
        total_comissoes=comissoes,
        faturamento_liquido=net,
        por_metodo=[PagamentoResumo(**p) for p in por_metodo],
        comandas=_build_comanda_items(comandas, garcom_names, cortesias_map, pagamentos_map),
    )


def historico_comandas(
    db: Session,
    data_inicio: datetime.date,
    data_fim: datetime.date,
    garcom_id: Optional[int] = None,
    busca: Optional[str] = None,
    pagina: int = 1,
    por_pagina: int = 50,
) -> HistoricoResponse:
    _validar_periodo(data_inicio, data_fim)
    start, _ = rr._day_utc_range(data_inicio)
    _, end = rr._day_utc_range(data_fim)
    total = rr.count_fechadas_no_periodo(db, start, end, garcom_id, busca)
    comandas = rr.list_fechadas_no_periodo_paginada(db, start, end, garcom_id, busca, pagina, por_pagina)
    garcom_names, cortesias_map, pagamentos_map, _ = _aggregate(db, comandas)
    return HistoricoResponse(
        total=total,
        pagina=pagina,
        por_pagina=por_pagina,
        total_paginas=max(1, math.ceil(total / por_pagina)),
        comandas=_build_comanda_items(comandas, garcom_names, cortesias_map, pagamentos_map),
    )


def fechamento_caixa(db: Session, data: datetime.date) -> FechamentoCaixaResponse:
    start, end = rr._day_utc_range(data)
    comandas = rr.list_fechadas_no_periodo(db, start, end)
    garcom_names, cortesias_map, pagamentos_map, por_metodo = _aggregate(db, comandas)

    ids = [c.id for c in comandas]
    net = sum((c.total or Decimal("0") for c in comandas), Decimal("0"))
    descontos = sum((c.desconto_valor or Decimal("0") for c in comandas), Decimal("0"))
    cortesias_total = sum(cortesias_map.values(), Decimal("0"))
    comissoes = rr.comissoes_total_por_comanda_ids(db, ids)

    return FechamentoCaixaResponse(
        data=data,
        qtd_comandas=len(comandas),
        faturamento_bruto=net + descontos,
        descontos=descontos,
        cortesias=cortesias_total,
        total_comissoes=comissoes,
        faturamento_liquido=net,
        por_metodo=[PagamentoResumo(**p) for p in por_metodo],
    )


def dre(db: Session, mes: str) -> DREResponse:
    _validar_mes(mes)
    start, end = rr._month_utc_range(mes)
    comandas = rr.list_fechadas_no_periodo(db, start, end)
    ids = [c.id for c in comandas]

    net = sum((c.total or Decimal("0") for c in comandas), Decimal("0"))
    descontos = sum((c.desconto_valor or Decimal("0") for c in comandas), Decimal("0"))
    cortesias_val = rr.cortesias_valor_total(db, ids)
    faturamento_bruto = net + descontos  # pré-desconto; cortesias têm preco=0 e não entram
    faturamento_liquido = net  # caixa efetivo recebido

    cmv = rr.cmv_total(db, ids)
    perdas = rr.perdas_total(db, start, end)
    comissoes = rr.comissoes_total_por_comanda_ids(db, ids)
    total_custos = cmv + perdas + comissoes
    lucro_bruto = faturamento_liquido - total_custos
    margem = (
        (lucro_bruto / faturamento_liquido * Decimal("100")).quantize(Decimal("0.01"))
        if faturamento_liquido > 0
        else Decimal("0")
    )

    sem_custo = [ItemSemCusto(**p) for p in rr.produtos_sem_custo(db, ids)]

    return DREResponse(
        mes=mes,
        faturamento_bruto=faturamento_bruto,
        descontos=descontos,
        cortesias_valor=cortesias_val,
        faturamento_liquido=faturamento_liquido,
        cmv=cmv,
        perdas=perdas,
        comissoes=comissoes,
        total_custos=total_custos,
        lucro_bruto=lucro_bruto,
        margem_percentual=margem,
        produtos_sem_custo=sem_custo,
    )


def cmv_por_produto(db: Session) -> CMVPorProdutoResponse:
    produtos = rr.todos_produtos_ativos(db)
    custos = rr.calcular_custos_produtos(db, [p.id for p in produtos])
    resultado = []
    for produto in produtos:
        custo = custos.get(produto.id)
        if custo is None or produto.preco_venda is None:
            resultado.append(
                CMVProdutoItem(
                    item_id=produto.id,
                    nome=produto.nome,
                    preco_venda=produto.preco_venda,
                    custo_medio=None,
                    margem_valor=None,
                    margem_percentual=None,
                    classificacao="sem_custo",
                )
            )
        else:
            margem_val = produto.preco_venda - custo
            margem_pct = (margem_val / produto.preco_venda * Decimal("100")).quantize(Decimal("0.01"))
            if margem_pct > Decimal("40"):
                classif = "verde"
            elif margem_pct >= Decimal("20"):
                classif = "amarelo"
            else:
                classif = "vermelho"
            resultado.append(
                CMVProdutoItem(
                    item_id=produto.id,
                    nome=produto.nome,
                    preco_venda=produto.preco_venda,
                    custo_medio=custo,
                    margem_valor=margem_val,
                    margem_percentual=margem_pct,
                    classificacao=classif,
                )
            )
    return CMVPorProdutoResponse(itens=resultado)


def perdas_cortesias(
    db: Session, data_inicio: datetime.date, data_fim: datetime.date
) -> PerdasCortesiasResponse:
    _validar_periodo(data_inicio, data_fim)
    start, _ = rr._day_utc_range(data_inicio)
    _, end = rr._day_utc_range(data_fim)
    grupos_raw = rr.perdas_no_periodo(db, start, end)
    grupos = [
        PerdasGrupo(motivo=g["motivo"], qtd_movimentos=g["qtd"], total_valor=g["total"])
        for g in grupos_raw
    ]
    total = sum((g.total_valor for g in grupos), Decimal("0"))
    return PerdasCortesiasResponse(
        data_inicio=data_inicio,
        data_fim=data_fim,
        total_geral=total,
        grupos=grupos,
    )


def produtos_mais_vendidos(
    db: Session, data_inicio: datetime.date, data_fim: datetime.date
) -> ProdutosMaisVendidosResponse:
    _validar_periodo(data_inicio, data_fim)
    start, _ = rr._day_utc_range(data_inicio)
    _, end = rr._day_utc_range(data_fim)
    rows = rr.produtos_mais_vendidos(db, start, end)

    receita_total = sum((r["receita_total"] for r in rows), Decimal("0"))
    itens = []
    for r in rows:
        pct = (
            (r["receita_total"] / receita_total * Decimal("100")).quantize(Decimal("0.1"))
            if receita_total > 0
            else Decimal("0")
        )
        itens.append(
            ProdutoMaisVendidoItem(
                produto_id=r["produto_id"],
                produto_nome=r["produto_nome"],
                categoria_nome=r["categoria_nome"],
                quantidade_total=r["quantidade_total"],
                receita_total=r["receita_total"],
                percentual_receita=pct,
            )
        )
    return ProdutosMaisVendidosResponse(
        data_inicio=data_inicio,
        data_fim=data_fim,
        receita_total_periodo=receita_total,
        itens=itens,
    )


def pico_vendas_horario(
    db: Session, data_inicio: datetime.date, data_fim: datetime.date
) -> PicoVendasHorarioResponse:
    _validar_periodo(data_inicio, data_fim)
    start, _ = rr._day_utc_range(data_inicio)
    _, end = rr._day_utc_range(data_fim)
    horarios_raw = rr.vendas_por_hora(db, start, end)

    horarios = [HorarioPicoItem(**h) for h in horarios_raw]
    total_comandas = sum(h.total_comandas for h in horarios)
    receita_total = sum((h.receita_total for h in horarios), Decimal("0"))

    hora_pico: Optional[int] = None
    ativos = [h for h in horarios if h.total_comandas > 0]
    if ativos:
        hora_pico = max(ativos, key=lambda h: h.total_comandas).hora

    return PicoVendasHorarioResponse(
        data_inicio=data_inicio,
        data_fim=data_fim,
        horarios=horarios,
        hora_pico=hora_pico,
        total_comandas_periodo=total_comandas,
        receita_total_periodo=receita_total,
    )


def vendas_por_garcom(
    db: Session, data_inicio: datetime.date, data_fim: datetime.date
) -> VendasPorGarcomResponse:
    _validar_periodo(data_inicio, data_fim)
    start, _ = rr._day_utc_range(data_inicio)
    _, end = rr._day_utc_range(data_fim)
    rows = rr.vendas_por_garcom_periodo(db, start, end)
    garcom_ids = [r["garcom_id"] for r in rows]
    nomes = rr._garcom_names(db, garcom_ids)
    comissoes_map = rr.comissoes_por_garcom_periodo(db, start, end)
    garcons = []
    for r in rows:
        fat = r["faturamento"]
        qtd = r["qtd_comandas"]
        ticket = (fat / qtd).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP) if qtd > 0 else Decimal("0")
        garcons.append(
            VendasGarcomItem(
                garcom_id=r["garcom_id"],
                garcom_nome=nomes.get(r["garcom_id"], "—"),
                qtd_comandas=qtd,
                faturamento=fat,
                ticket_medio=ticket,
                comissao=comissoes_map.get(r["garcom_id"], Decimal("0")),
            )
        )
    return VendasPorGarcomResponse(
        data_inicio=data_inicio,
        data_fim=data_fim,
        garcons=garcons,
    )


def vendas_por_produto(
    db: Session, data_inicio: datetime.date, data_fim: datetime.date
) -> VendasPorProdutoResponse:
    _validar_periodo(data_inicio, data_fim)
    start, _ = rr._day_utc_range(data_inicio)
    _, end = rr._day_utc_range(data_fim)
    rows = rr.vendas_por_produto_periodo(db, start, end)
    itens = []
    for r in rows:
        qtd = r["qtd_vendida"]
        fat = r["faturamento"]
        ticket = (fat / qtd).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP) if qtd > 0 else Decimal("0")
        itens.append(
            VendasPorProdutoItem(
                produto_id=r["produto_id"],
                produto_nome=r["produto_nome"],
                categoria_nome=r["categoria_nome"],
                qtd_vendida=qtd,
                qtd_cortesias=r["qtd_cortesias"],
                faturamento=fat,
                ticket_medio=ticket,
            )
        )
    total = sum(i.faturamento for i in itens) or Decimal("0")
    return VendasPorProdutoResponse(
        data_inicio=data_inicio,
        data_fim=data_fim,
        total_faturamento=total,
        itens=itens,
    )


def _validar_periodo(data_inicio: datetime.date, data_fim: datetime.date) -> None:
    if data_inicio > data_fim:
        raise AppError(ErrorCode.VALIDATION_ERROR, "A data inicial não pode ser posterior à data final.", "data_inicio")
    if (data_fim - data_inicio).days > 366:
        raise AppError(ErrorCode.VALIDATION_ERROR, "O período máximo permitido é de 366 dias.", "data_fim")


def _validar_mes(mes: str) -> None:
    if not re.fullmatch(r"\d{4}-(0[1-9]|1[0-2])", mes):
        raise AppError(ErrorCode.VALIDATION_ERROR, "Informe o mês no formato YYYY-MM.", "mes")
