import datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy.orm import Session

from src.repositories import relatorio_repository as rr
from src.schemas.relatorio_schemas import (
    ComandaRelatorioItem,
    FechamentoCaixaResponse,
    HistoricoResponse,
    PagamentoResumo,
    VendasDoDiaResponse,
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


def vendas_do_dia(db: Session) -> VendasDoDiaResponse:
    hoje = datetime.datetime.now(rr.TZ).date()
    start, end = rr._day_utc_range(hoje)
    comandas = rr.list_fechadas_no_periodo(db, start, end)
    garcom_names, cortesias_map, pagamentos_map, por_metodo = _aggregate(db, comandas)

    bruto = sum((c.total or Decimal("0") for c in comandas), Decimal("0"))
    descontos = sum((c.desconto_valor or Decimal("0") for c in comandas), Decimal("0"))
    cortesias_total = sum(cortesias_map.values(), Decimal("0"))

    return VendasDoDiaResponse(
        data=hoje,
        qtd_comandas=len(comandas),
        faturamento_bruto=bruto,
        total_descontos=descontos,
        total_cortesias=cortesias_total,
        faturamento_liquido=bruto - descontos,
        por_metodo=[PagamentoResumo(**p) for p in por_metodo],
        comandas=_build_comanda_items(comandas, garcom_names, cortesias_map, pagamentos_map),
    )


def historico_comandas(
    db: Session,
    data_inicio: datetime.date,
    data_fim: datetime.date,
    garcom_id: Optional[int] = None,
    busca: Optional[str] = None,
) -> HistoricoResponse:
    start, _ = rr._day_utc_range(data_inicio)
    _, end = rr._day_utc_range(data_fim)
    comandas = rr.list_fechadas_no_periodo(db, start, end, garcom_id, busca)
    garcom_names, cortesias_map, pagamentos_map, _ = _aggregate(db, comandas)
    return HistoricoResponse(
        total=len(comandas),
        comandas=_build_comanda_items(comandas, garcom_names, cortesias_map, pagamentos_map),
    )


def fechamento_caixa(db: Session, data: datetime.date) -> FechamentoCaixaResponse:
    start, end = rr._day_utc_range(data)
    comandas = rr.list_fechadas_no_periodo(db, start, end)
    garcom_names, cortesias_map, pagamentos_map, por_metodo = _aggregate(db, comandas)

    bruto = sum((c.total or Decimal("0") for c in comandas), Decimal("0"))
    descontos = sum((c.desconto_valor or Decimal("0") for c in comandas), Decimal("0"))
    cortesias_total = sum(cortesias_map.values(), Decimal("0"))

    return FechamentoCaixaResponse(
        data=data,
        qtd_comandas=len(comandas),
        faturamento_bruto=bruto,
        descontos=descontos,
        cortesias=cortesias_total,
        faturamento_liquido=bruto - descontos,
        por_metodo=[PagamentoResumo(**p) for p in por_metodo],
    )
