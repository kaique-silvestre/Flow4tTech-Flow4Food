import datetime
from decimal import Decimal
from zoneinfo import ZoneInfo

from sqlalchemy import and_, case, func, select
from sqlalchemy.orm import Session

from src.models.comandas import Comanda, StatusComanda
from src.models.comissoes_garcom import ComissaoGarcom
from src.models.compras import Compra
from src.models.fornecedores import Fornecedor
from src.models.garcons import Garcom
from src.models.insumos import Insumo
from src.models.itens_comanda import ItemComanda
from src.models.metodos_pagamento import MetodoPagamento
from src.models.pagamentos import Pagamento
from src.models.produtos import Produto
from src.repositories.relatorio_repository import _day_utc_range, cmv_total

TZ = ZoneInfo("America/Sao_Paulo")


def compras_agendadas_com_fornecedor(db: Session, data_limite: datetime.date) -> list[dict]:
    rows = db.execute(
        select(Compra, Fornecedor.nome.label("fornecedor_nome"))
        .outerjoin(Fornecedor, Compra.fornecedor_id == Fornecedor.id)
        .where(Compra.status == "confirmado", Compra.data_prevista_recebimento <= data_limite)
    ).all()
    return [{"compra": row.Compra, "fornecedor_nome": row.fornecedor_nome} for row in rows]


def _today_sp() -> datetime.date:
    return datetime.datetime.now(TZ).date()


def _now_utc() -> datetime.datetime:
    return datetime.datetime.utcnow()


def _bucket_case(column, boundaries: list[datetime.datetime]):
    """Expressão SQL que mapeia `column` pro índice do bucket [boundaries[i], boundaries[i+1]).

    Evita `AT TIME ZONE`/funções específicas de dialect: os limites (já em UTC,
    calculados via `_day_utc_range`/equivalente) carregam a conversão de fuso
    horário, então a comparação em si é portável entre SQLite e Postgres.
    Usado pra empurrar `GROUP BY`/`func.sum` pro SQL em vez de somar linha a
    linha em Python.
    """
    return case(
        *[
            (and_(column >= boundaries[i], column < boundaries[i + 1]), i)
            for i in range(len(boundaries) - 1)
        ],
        else_=None,
    )


def comandas_fechadas_hoje(db: Session) -> list[Comanda]:
    today = _today_sp()
    start, end = _day_utc_range(today)
    return list(
        db.execute(
            select(Comanda).where(
                Comanda.status == StatusComanda.FECHADA.value,
                Comanda.data_fechamento >= start,
                Comanda.data_fechamento <= end,
            )
        )
        .scalars()
        .all()
    )


def cmv_hoje(db: Session, comanda_ids: list[int]) -> Decimal:
    return cmv_total(db, comanda_ids)


def faturamento_por_hora_hoje(db: Session, comanda_ids: list[int]) -> list[dict]:
    if not comanda_ids:
        return [{"hora": h, "faturamento": Decimal("0")} for h in range(24)]
    today = _today_sp()
    hour_starts = [
        datetime.datetime.combine(today, datetime.time(hour=h), tzinfo=TZ)
        .astimezone(datetime.timezone.utc)
        .replace(tzinfo=None)
        for h in range(24)
    ]
    hour_starts.append(hour_starts[0] + datetime.timedelta(days=1))
    bucket = _bucket_case(Comanda.data_fechamento, hour_starts)
    rows = db.execute(
        select(bucket.label("hora"), func.sum(Comanda.total).label("faturamento"))
        .where(Comanda.id.in_(comanda_ids))
        .group_by(bucket)
    ).all()
    fat_by_bucket = {int(r.hora): (r.faturamento or Decimal("0")) for r in rows if r.hora is not None}
    return [{"hora": h, "faturamento": fat_by_bucket.get(h, Decimal("0"))} for h in range(24)]


def top_10_produtos_30d(db: Session) -> list[dict]:
    today = _today_sp()
    start_date = today - datetime.timedelta(days=29)
    start, _ = _day_utc_range(start_date)
    _, end = _day_utc_range(today)
    rows = db.execute(
        select(
            Produto.id,
            Produto.nome,
            func.sum(ItemComanda.quantidade).label("quantidade"),
            func.sum(ItemComanda.preco_unitario * ItemComanda.quantidade).label("faturamento"),
        )
        .select_from(ItemComanda)
        .join(Comanda, ItemComanda.comanda_id == Comanda.id)
        .join(Produto, ItemComanda.produto_id == Produto.id)
        .where(
            Comanda.status == StatusComanda.FECHADA.value,
            Comanda.data_fechamento >= start,
            Comanda.data_fechamento <= end,
            ItemComanda.cancelado.is_(False),
            ItemComanda.cortesia.is_(False),
        )
        .group_by(Produto.id, Produto.nome)
        .order_by(func.sum(ItemComanda.preco_unitario * ItemComanda.quantidade).desc())
        .limit(10)
    ).all()
    return [
        {
            "item_id": r.id,
            "nome": r.nome,
            "quantidade": int(r.quantidade or 0),
            "faturamento": r.faturamento or Decimal("0"),
        }
        for r in rows
    ]


def _day_boundaries(inicio: datetime.date, fim: datetime.date) -> list[datetime.datetime]:
    """Limites UTC de cada dia local (`America/Sao_Paulo`) entre `inicio` e `fim`, inclusive.

    `boundaries[i]` é o início (UTC) do dia `inicio + i`; o último elemento é o
    início do dia seguinte a `fim`, usado como limite superior exclusivo.
    """
    n_dias = (fim - inicio).days + 1
    return [_day_utc_range(inicio + datetime.timedelta(days=i))[0] for i in range(n_dias + 1)]


def faturamento_ultimos_30d(db: Session) -> list[dict]:
    today = _today_sp()
    start_date = today - datetime.timedelta(days=29)
    day_starts = _day_boundaries(start_date, today)
    bucket = _bucket_case(Comanda.data_fechamento, day_starts)
    rows = db.execute(
        select(bucket.label("dia"), func.sum(Comanda.total).label("faturamento"))
        .where(
            Comanda.status == StatusComanda.FECHADA.value,
            Comanda.data_fechamento >= day_starts[0],
            Comanda.data_fechamento < day_starts[-1],
        )
        .group_by(bucket)
    ).all()
    fat_by_bucket = {int(r.dia): (r.faturamento or Decimal("0")) for r in rows if r.dia is not None}
    return [
        {"data": start_date + datetime.timedelta(days=i), "faturamento": fat_by_bucket.get(i, Decimal("0"))}
        for i in range(30)
    ]


def heatmap_mes_atual(db: Session) -> list[dict]:
    today = _today_sp()
    primeiro = datetime.date(today.year, today.month, 1)
    if today.month == 12:
        ultimo = datetime.date(today.year + 1, 1, 1) - datetime.timedelta(days=1)
    else:
        ultimo = datetime.date(today.year, today.month + 1, 1) - datetime.timedelta(days=1)
    day_starts = _day_boundaries(primeiro, ultimo)
    bucket = _bucket_case(Comanda.data_fechamento, day_starts)
    rows = db.execute(
        select(bucket.label("dia"), func.sum(Comanda.total).label("faturamento"))
        .where(
            Comanda.status == StatusComanda.FECHADA.value,
            Comanda.data_fechamento >= day_starts[0],
            Comanda.data_fechamento < day_starts[-1],
        )
        .group_by(bucket)
    ).all()
    fat_by_bucket = {int(r.dia): (r.faturamento or Decimal("0")) for r in rows if r.dia is not None}
    return [
        {"data": primeiro + datetime.timedelta(days=i), "faturamento": fat_by_bucket.get(i, Decimal("0"))}
        for i in range(len(day_starts) - 1)
    ]


def historico_periodo(db: Session, inicio: datetime.date, fim: datetime.date) -> list[dict]:
    day_starts = _day_boundaries(inicio, fim)
    bucket = _bucket_case(Comanda.data_fechamento, day_starts)
    rows_fat = db.execute(
        select(bucket.label("dia"), func.sum(Comanda.total).label("faturamento"))
        .where(
            Comanda.status == StatusComanda.FECHADA.value,
            Comanda.data_fechamento >= day_starts[0],
            Comanda.data_fechamento < day_starts[-1],
        )
        .group_by(bucket)
    ).all()
    fat_map = {
        inicio + datetime.timedelta(days=int(r.dia)): (r.faturamento or Decimal("0"))
        for r in rows_fat
        if r.dia is not None
    }
    rows_compras = db.execute(
        select(Compra.data_compra, func.sum(Compra.total).label("total"))
        .where(Compra.data_compra >= inicio, Compra.data_compra <= fim)
        .group_by(Compra.data_compra)
    ).all()
    compras_map = {r.data_compra: (r.total or Decimal("0")) for r in rows_compras}
    result = []
    for i in range(len(day_starts) - 1):
        current = inicio + datetime.timedelta(days=i)
        result.append(
            {
                "data": current,
                "faturamento": fat_map.get(current, Decimal("0")),
                "total_compras": compras_map.get(current, Decimal("0")),
            }
        )
    return result


def resumo_anual(db: Session, ano: int) -> list[dict]:
    month_starts = [_day_utc_range(datetime.date(ano, m, 1))[0] for m in range(1, 13)]
    month_starts.append(_day_utc_range(datetime.date(ano + 1, 1, 1))[0])
    bucket = _bucket_case(Comanda.data_fechamento, month_starts)
    rows_fat = db.execute(
        select(bucket.label("mes"), func.sum(Comanda.total).label("faturamento"))
        .where(
            Comanda.status == StatusComanda.FECHADA.value,
            Comanda.data_fechamento >= month_starts[0],
            Comanda.data_fechamento < month_starts[-1],
        )
        .group_by(bucket)
    ).all()
    fat_map = {int(r.mes) + 1: (r.faturamento or Decimal("0")) for r in rows_fat if r.mes is not None}

    mes_expr = func.extract("month", Compra.data_compra)
    rows_compras = db.execute(
        select(mes_expr.label("mes"), func.sum(Compra.total).label("total"))
        .where(
            Compra.data_compra >= datetime.date(ano, 1, 1),
            Compra.data_compra <= datetime.date(ano, 12, 31),
        )
        .group_by(mes_expr)
    ).all()
    compras_map = {int(r.mes): (r.total or Decimal("0")) for r in rows_compras}

    return [
        {
            "mes": m,
            "faturamento": fat_map.get(m, Decimal("0")),
            "total_compras": compras_map.get(m, Decimal("0")),
        }
        for m in range(1, 13)
    ]


def faturamento_mes(db: Session, ano: int, mes: int) -> Decimal:
    primeiro = datetime.date(ano, mes, 1)
    if mes == 12:
        ultimo = datetime.date(ano + 1, 1, 1) - datetime.timedelta(days=1)
    else:
        ultimo = datetime.date(ano, mes + 1, 1) - datetime.timedelta(days=1)
    start, _ = _day_utc_range(primeiro)
    _, end = _day_utc_range(ultimo)
    total = db.execute(
        select(func.sum(Comanda.total)).where(
            Comanda.status == StatusComanda.FECHADA.value,
            Comanda.data_fechamento >= start,
            Comanda.data_fechamento <= end,
        )
    ).scalar()
    return total or Decimal("0")


def insumos_abaixo_critico(db: Session) -> list[dict]:
    rows = db.execute(
        select(Insumo.nome, Insumo.estoque_atual, Insumo.nivel_critico, Insumo.unidade_base)
        .where(
            Insumo.ativo.is_(True),
            Insumo.nivel_critico.isnot(None),
            Insumo.estoque_atual <= Insumo.nivel_critico,
        )
        .order_by(Insumo.nome)
    ).all()
    return [
        {
            "nome": r.nome,
            "estoque_atual": float(r.estoque_atual),
            "nivel_critico": float(r.nivel_critico),
            "unidade_base": r.unidade_base,
        }
        for r in rows
    ]


def pagamentos_hoje_por_metodo(db: Session) -> list[dict]:
    """Pagamentos recebidos hoje por método, independente do status da comanda.

    Deliberadamente não reusa `_build_por_metodo` (que filtra por
    `comanda_id.in_(comandas_fechadas_hoje)`) — esse filtro excluiria um
    pagamento parcial já recebido numa comanda ainda aberta ou reaberta,
    escondendo dinheiro/pix que já está fisicamente em caixa hoje.
    """
    today = _today_sp()
    start, end = _day_utc_range(today)
    rows = db.execute(
        select(
            MetodoPagamento.id,
            MetodoPagamento.nome,
            func.sum(Pagamento.valor).label("total"),
            func.count(Pagamento.id).label("qtd"),
        )
        .join(MetodoPagamento, Pagamento.metodo_id == MetodoPagamento.id)
        .where(Pagamento.created_at >= start, Pagamento.created_at <= end)
        .group_by(MetodoPagamento.id, MetodoPagamento.nome)
        .order_by(func.sum(Pagamento.valor).desc())
    ).all()
    return [
        {"metodo_id": r.id, "metodo_nome": r.nome, "total": r.total or Decimal("0"), "qtd": r.qtd}
        for r in rows
    ]


def comissoes_pendentes_por_garcom(db: Session) -> list[dict]:
    """Comissões com `pago=False`, agregadas por garçom — sem filtro de data
    (é uma dívida em aberto, não um corte por período)."""
    rows = db.execute(
        select(
            ComissaoGarcom.garcom_id,
            Garcom.nome,
            func.sum(ComissaoGarcom.valor).label("valor_pendente"),
        )
        .join(Garcom, ComissaoGarcom.garcom_id == Garcom.id)
        .where(ComissaoGarcom.pago.is_(False))
        .group_by(ComissaoGarcom.garcom_id, Garcom.nome)
        .order_by(func.sum(ComissaoGarcom.valor).desc())
    ).all()
    return [
        {"garcom_id": r.garcom_id, "nome": r.nome, "valor_pendente": r.valor_pendente or Decimal("0")}
        for r in rows
    ]


def comandas_abertas_com_detalhes(db: Session) -> list[dict]:
    now_utc = _now_utc()
    comandas = list(
        db.execute(
            select(Comanda)
            .where(Comanda.status.in_([StatusComanda.ABERTA.value, StatusComanda.REABERTA.value]))
            .order_by(Comanda.created_at.asc())
        )
        .scalars()
        .all()
    )
    if not comandas:
        return []
    ids = [c.id for c in comandas]
    counts_rows = db.execute(
        select(ItemComanda.comanda_id, func.sum(ItemComanda.quantidade).label("qtd"))
        .where(ItemComanda.comanda_id.in_(ids), ItemComanda.cancelado.is_(False))
        .group_by(ItemComanda.comanda_id)
    ).all()
    count_map = {r.comanda_id: int(r.qtd or 0) for r in counts_rows}
    result = []
    for comanda in comandas:
        delta = now_utc - comanda.created_at
        minutos = max(0, int(delta.total_seconds() / 60))
        result.append(
            {
                "id": comanda.id,
                "identificacao": comanda.identificacao,
                "qtd_itens": count_map.get(comanda.id, 0),
                "total": comanda.total or Decimal("0"),
                "aberta_ha_minutos": minutos,
            }
        )
    return result
