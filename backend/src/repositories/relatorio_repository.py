import datetime
from decimal import Decimal
from typing import Optional
from zoneinfo import ZoneInfo

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from src.models.comandas import Comanda, StatusComanda
from src.models.garcons import Garcom
from src.models.itens_comanda import ItemComanda
from src.models.metodos_pagamento import MetodoPagamento
from src.models.pagamentos import Pagamento

TZ = ZoneInfo("America/Sao_Paulo")


def _day_utc_range(data: datetime.date) -> tuple[datetime.datetime, datetime.datetime]:
    """Converte dia local (Sao_Paulo) para intervalo UTC naive (sem tzinfo) para comparar com DB."""
    utc = datetime.timezone.utc
    start = datetime.datetime.combine(data, datetime.time.min, tzinfo=TZ)
    end = datetime.datetime.combine(data, datetime.time.max, tzinfo=TZ)
    return start.astimezone(utc).replace(tzinfo=None), end.astimezone(utc).replace(tzinfo=None)


def _build_por_metodo(db: Session, comanda_ids: list[int]) -> list[dict]:
    if not comanda_ids:
        return []
    rows = db.execute(
        select(
            MetodoPagamento.id,
            MetodoPagamento.nome,
            func.sum(Pagamento.valor).label("total"),
            func.count(Pagamento.id).label("qtd"),
        )
        .join(MetodoPagamento, Pagamento.metodo_id == MetodoPagamento.id)
        .where(Pagamento.comanda_id.in_(comanda_ids))
        .group_by(MetodoPagamento.id, MetodoPagamento.nome)
        .order_by(func.sum(Pagamento.valor).desc())
    ).all()
    return [
        {"metodo_id": r.id, "metodo_nome": r.nome, "total": r.total or Decimal("0"), "qtd": r.qtd}
        for r in rows
    ]


def _cortesias_por_comanda(db: Session, comanda_ids: list[int]) -> dict[int, Decimal]:
    if not comanda_ids:
        return {}
    rows = db.execute(
        select(
            ItemComanda.comanda_id,
            func.sum(ItemComanda.preco_unitario * ItemComanda.quantidade).label("total"),
        )
        .where(
            ItemComanda.comanda_id.in_(comanda_ids),
            ItemComanda.cortesia.is_(True),
            ItemComanda.cancelado.is_(False),
        )
        .group_by(ItemComanda.comanda_id)
    ).all()
    return {r.comanda_id: r.total or Decimal("0") for r in rows}


def _pagamentos_por_comanda(db: Session, comanda_ids: list[int]) -> dict[int, list[dict]]:
    if not comanda_ids:
        return {}
    rows = db.execute(
        select(
            Pagamento.comanda_id,
            MetodoPagamento.id,
            MetodoPagamento.nome,
            func.sum(Pagamento.valor).label("total"),
            func.count(Pagamento.id).label("qtd"),
        )
        .join(MetodoPagamento, Pagamento.metodo_id == MetodoPagamento.id)
        .where(Pagamento.comanda_id.in_(comanda_ids))
        .group_by(Pagamento.comanda_id, MetodoPagamento.id, MetodoPagamento.nome)
    ).all()
    result: dict[int, list[dict]] = {}
    for r in rows:
        result.setdefault(r.comanda_id, []).append(
            {"metodo_id": r.id, "metodo_nome": r.nome, "total": r.total or Decimal("0"), "qtd": r.qtd}
        )
    return result


def _garcom_names(db: Session, garcom_ids: list[int]) -> dict[int, str]:
    if not garcom_ids:
        return {}
    rows = db.execute(select(Garcom.id, Garcom.nome).where(Garcom.id.in_(garcom_ids))).all()
    return {r.id: r.nome for r in rows}


def list_fechadas_no_periodo(
    db: Session,
    start_utc: datetime.datetime,
    end_utc: datetime.datetime,
    garcom_id: Optional[int] = None,
    busca: Optional[str] = None,
) -> list[Comanda]:
    q = db.query(Comanda).filter(
        Comanda.status == StatusComanda.FECHADA.value,
        Comanda.data_fechamento >= start_utc,
        Comanda.data_fechamento <= end_utc,
    )
    if garcom_id is not None:
        q = q.filter(Comanda.garcom_id == garcom_id)
    if busca:
        q = q.filter(Comanda.identificacao.ilike(f"%{busca}%"))
    return q.order_by(Comanda.data_fechamento.desc()).all()
