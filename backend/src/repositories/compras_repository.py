import datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy import select
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
    )
    db.add(compra)
    db.flush()
    return compra


def add_item_compra(
    db: Session,
    compra_id: int,
    item_id: int,
    quantidade: Decimal,
    custo_unitario: Decimal,
    custo_total: Decimal,
) -> ItemCompra:
    item = ItemCompra(
        compra_id=compra_id,
        item_id=item_id,
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
) -> list[Compra]:
    stmt = select(Compra).order_by(Compra.data_compra.desc(), Compra.created_at.desc())
    if data_inicio is not None:
        stmt = stmt.where(Compra.data_compra >= data_inicio)
    if data_fim is not None:
        stmt = stmt.where(Compra.data_compra <= data_fim)
    if fornecedor_id is not None:
        stmt = stmt.where(Compra.fornecedor_id == fornecedor_id)
    return list(db.execute(stmt).scalars().all())


def get_compra_by_id(db: Session, compra_id: int) -> Optional[Compra]:
    return db.execute(select(Compra).where(Compra.id == compra_id)).scalar_one_or_none()


def get_itens_compra(db: Session, compra_id: int) -> list[ItemCompra]:
    stmt = select(ItemCompra).where(ItemCompra.compra_id == compra_id)
    return list(db.execute(stmt).scalars().all())
