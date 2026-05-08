import datetime
from decimal import Decimal
from typing import Optional
from zoneinfo import ZoneInfo

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from src.models.comandas import Comanda, StatusComanda
from src.models.garcons import Garcom
from src.models.itens import Item
from src.models.itens_comanda import ItemComanda
from src.models.metodos_pagamento import MetodoPagamento
from src.models.movimentos_estoque import MovimentoEstoque, TipoMovimento
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


def _month_utc_range(mes: str) -> tuple[datetime.datetime, datetime.datetime]:
    """mes='YYYY-MM' → range UTC naive do primeiro ao último dia do mês."""
    year, month = int(mes[:4]), int(mes[5:7])
    first = datetime.date(year, month, 1)
    if month == 12:
        last = datetime.date(year + 1, 1, 1) - datetime.timedelta(days=1)
    else:
        last = datetime.date(year, month + 1, 1) - datetime.timedelta(days=1)
    return _day_utc_range(first)[0], _day_utc_range(last)[1]


def cmv_total(db: Session, comanda_ids: list[int]) -> Decimal:
    if not comanda_ids:
        return Decimal("0")
    row = db.execute(
        select(func.sum(Item.custo_medio * ItemComanda.quantidade))
        .select_from(ItemComanda)
        .join(Item, ItemComanda.item_id == Item.id)
        .where(
            ItemComanda.comanda_id.in_(comanda_ids),
            ItemComanda.cancelado.is_(False),
            Item.custo_medio.isnot(None),
        )
    ).scalar()
    return row or Decimal("0")


def cortesias_valor_total(db: Session, comanda_ids: list[int]) -> Decimal:
    """Soma Item.preco_venda * quantidade para itens cortesia (receita perdida)."""
    if not comanda_ids:
        return Decimal("0")
    row = db.execute(
        select(func.sum(Item.preco_venda * ItemComanda.quantidade))
        .select_from(ItemComanda)
        .join(Item, ItemComanda.item_id == Item.id)
        .where(
            ItemComanda.comanda_id.in_(comanda_ids),
            ItemComanda.cortesia.is_(True),
            ItemComanda.cancelado.is_(False),
            Item.preco_venda.isnot(None),
        )
    ).scalar()
    return row or Decimal("0")


def perdas_no_periodo(
    db: Session, start_utc: datetime.datetime, end_utc: datetime.datetime
) -> list[dict]:
    rows = db.execute(
        select(
            MovimentoEstoque.motivo,
            func.count(MovimentoEstoque.id).label("qtd"),
            func.sum(MovimentoEstoque.quantidade * MovimentoEstoque.custo_unitario).label("total"),
        )
        .where(
            MovimentoEstoque.tipo == TipoMovimento.SAIDA_PERDA.value,
            MovimentoEstoque.created_at >= start_utc,
            MovimentoEstoque.created_at <= end_utc,
        )
        .group_by(MovimentoEstoque.motivo)
    ).all()
    return [
        {"motivo": r.motivo or "outro", "qtd": r.qtd, "total": r.total or Decimal("0")}
        for r in rows
    ]


def perdas_total(db: Session, start_utc: datetime.datetime, end_utc: datetime.datetime) -> Decimal:
    row = db.execute(
        select(func.sum(MovimentoEstoque.quantidade * MovimentoEstoque.custo_unitario))
        .where(
            MovimentoEstoque.tipo == TipoMovimento.SAIDA_PERDA.value,
            MovimentoEstoque.created_at >= start_utc,
            MovimentoEstoque.created_at <= end_utc,
            MovimentoEstoque.custo_unitario.isnot(None),
        )
    ).scalar()
    return row or Decimal("0")


def produtos_sem_custo(db: Session, comanda_ids: list[int]) -> list[dict]:
    if not comanda_ids:
        return []
    rows = db.execute(
        select(Item.id, Item.nome)
        .select_from(ItemComanda)
        .join(Item, ItemComanda.item_id == Item.id)
        .where(
            ItemComanda.comanda_id.in_(comanda_ids),
            ItemComanda.cancelado.is_(False),
            Item.custo_medio.is_(None),
        )
        .distinct()
    ).all()
    return [{"item_id": r.id, "nome": r.nome} for r in rows]


def todos_itens_vendaveis(db: Session) -> list[Item]:
    return list(
        db.execute(select(Item).where(Item.vendavel.is_(True), Item.ativo.is_(True)).order_by(Item.nome))
        .scalars()
        .all()
    )


def vendas_por_garcom_periodo(
    db: Session, start_utc: datetime.datetime, end_utc: datetime.datetime
) -> list[dict]:
    rows = db.execute(
        select(
            Comanda.garcom_id,
            func.count(Comanda.id).label("qtd"),
            func.sum(Comanda.total).label("faturamento"),
        )
        .where(
            Comanda.status == StatusComanda.FECHADA.value,
            Comanda.data_fechamento >= start_utc,
            Comanda.data_fechamento <= end_utc,
        )
        .group_by(Comanda.garcom_id)
        .order_by(func.sum(Comanda.total).desc())
    ).all()
    return [
        {
            "garcom_id": r.garcom_id,
            "qtd_comandas": r.qtd,
            "faturamento": r.faturamento or Decimal("0"),
        }
        for r in rows
    ]
