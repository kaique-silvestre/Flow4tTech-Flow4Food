import datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from src.models.compras import Compra, ItemCompra


def create_compra(
    db: Session,
    fornecedor_id: Optional[int],
    data_compra: datetime.date,
    numero_nota: Optional[str],
    total: Decimal,
) -> Compra:
    compra = Compra(
        fornecedor_id=fornecedor_id,
        data_compra=data_compra,
        numero_nota=numero_nota,
        total=total,
        status="ativa",
    )
    db.add(compra)
    db.flush()
    return compra


def add_item_compra(
    db: Session,
    compra_id: int,
    insumo_id: int,
    quantidade: Decimal,
    custo_unitario: Decimal,
    custo_total: Decimal,
) -> ItemCompra:
    item = ItemCompra(
        compra_id=compra_id,
        insumo_id=insumo_id,
        quantidade=quantidade,
        custo_unitario=custo_unitario,
        custo_total=custo_total,
    )
    db.add(item)
    return item


def list_compras(
    db: Session,
    data_inicio: Optional[datetime.date] = None,
    data_fim: Optional[datetime.date] = None,
    fornecedor_id: Optional[int] = None,
    status: Optional[str] = None,
    pagina: int = 1,
    por_pagina: int = 10,
) -> tuple[list[Compra], int, Decimal]:
    stmt = select(Compra).order_by(Compra.data_compra.desc(), Compra.created_at.desc())
    count_stmt = select(func.count()).select_from(Compra)
    sum_stmt = select(func.sum(Compra.total)).select_from(Compra)
    if data_inicio is not None:
        stmt = stmt.where(Compra.data_compra >= data_inicio)
        count_stmt = count_stmt.where(Compra.data_compra >= data_inicio)
        sum_stmt = sum_stmt.where(Compra.data_compra >= data_inicio)
    if data_fim is not None:
        stmt = stmt.where(Compra.data_compra <= data_fim)
        count_stmt = count_stmt.where(Compra.data_compra <= data_fim)
        sum_stmt = sum_stmt.where(Compra.data_compra <= data_fim)
    if fornecedor_id is not None:
        stmt = stmt.where(Compra.fornecedor_id == fornecedor_id)
        count_stmt = count_stmt.where(Compra.fornecedor_id == fornecedor_id)
        sum_stmt = sum_stmt.where(Compra.fornecedor_id == fornecedor_id)
    if status is not None:
        stmt = stmt.where(Compra.status == status)
        count_stmt = count_stmt.where(Compra.status == status)
        sum_stmt = sum_stmt.where(Compra.status == status)
    total = db.execute(count_stmt).scalar_one()
    total_periodo = db.execute(sum_stmt).scalar_one() or Decimal("0")
    offset = (pagina - 1) * por_pagina
    compras = list(db.execute(stmt.offset(offset).limit(por_pagina)).scalars().all())
    return compras, total, total_periodo


def get_compra_by_id(db: Session, compra_id: int) -> Optional[Compra]:
    return db.execute(select(Compra).where(Compra.id == compra_id)).scalar_one_or_none()


def get_itens_compra(db: Session, compra_id: int) -> list[ItemCompra]:
    stmt = select(ItemCompra).where(ItemCompra.compra_id == compra_id)
    return list(db.execute(stmt).scalars().all())
