import datetime
from decimal import Decimal
from zoneinfo import ZoneInfo

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from src.models.comandas import Comanda, StatusComanda
from src.models.itens_comanda import ItemComanda
from src.models.produtos import Produto
from src.repositories.relatorio_repository import _day_utc_range, cmv_total

TZ = ZoneInfo("America/Sao_Paulo")


def _today_sp() -> datetime.date:
    return datetime.datetime.now(TZ).date()


def _now_utc() -> datetime.datetime:
    return datetime.datetime.utcnow()


def _local_date(dt_utc: datetime.datetime) -> datetime.date:
    return dt_utc.replace(tzinfo=datetime.timezone.utc).astimezone(TZ).date()


def _local_hour(dt_utc: datetime.datetime) -> int:
    return dt_utc.replace(tzinfo=datetime.timezone.utc).astimezone(TZ).hour


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
    rows = db.execute(
        select(Comanda.data_fechamento, Comanda.total).where(Comanda.id.in_(comanda_ids))
    ).all()
    buckets = [Decimal("0")] * 24
    for r in rows:
        if r.data_fechamento:
            hora = _local_hour(r.data_fechamento)
            buckets[hora] += r.total or Decimal("0")
    return [{"hora": h, "faturamento": buckets[h]} for h in range(24)]


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
        .order_by(func.sum(ItemComanda.quantidade).desc())
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


def faturamento_ultimos_30d(db: Session) -> list[dict]:
    today = _today_sp()
    start_date = today - datetime.timedelta(days=29)
    start, _ = _day_utc_range(start_date)
    _, end = _day_utc_range(today)
    rows = db.execute(
        select(Comanda.data_fechamento, Comanda.total).where(
            Comanda.status == StatusComanda.FECHADA.value,
            Comanda.data_fechamento >= start,
            Comanda.data_fechamento <= end,
        )
    ).all()
    dia_map: dict[datetime.date, Decimal] = {}
    for r in rows:
        if r.data_fechamento:
            d = _local_date(r.data_fechamento)
            dia_map[d] = dia_map.get(d, Decimal("0")) + (r.total or Decimal("0"))
    result = []
    for i in range(30):
        d = start_date + datetime.timedelta(days=i)
        result.append({"data": d, "faturamento": dia_map.get(d, Decimal("0"))})
    return result


def heatmap_mes_atual(db: Session) -> list[dict]:
    today = _today_sp()
    primeiro = datetime.date(today.year, today.month, 1)
    if today.month == 12:
        ultimo = datetime.date(today.year + 1, 1, 1) - datetime.timedelta(days=1)
    else:
        ultimo = datetime.date(today.year, today.month + 1, 1) - datetime.timedelta(days=1)
    start, _ = _day_utc_range(primeiro)
    _, end = _day_utc_range(ultimo)
    rows = db.execute(
        select(Comanda.data_fechamento, Comanda.total).where(
            Comanda.status == StatusComanda.FECHADA.value,
            Comanda.data_fechamento >= start,
            Comanda.data_fechamento <= end,
        )
    ).all()
    dia_map: dict[datetime.date, Decimal] = {}
    for r in rows:
        if r.data_fechamento:
            d = _local_date(r.data_fechamento)
            dia_map[d] = dia_map.get(d, Decimal("0")) + (r.total or Decimal("0"))
    result = []
    d = primeiro
    while d <= ultimo:
        result.append({"data": d, "faturamento": dia_map.get(d, Decimal("0"))})
        d += datetime.timedelta(days=1)
    return result


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
