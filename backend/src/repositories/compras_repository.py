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
    status: str = "recebido",
    tipo_compra: str = "imediata",
    data_prevista_recebimento: Optional[datetime.date] = None,
    data_prevista_pagamento: Optional[datetime.date] = None,
) -> Compra:
    compra = Compra(
        fornecedor_id=fornecedor_id,
        data_compra=data_compra,
        numero_nota=numero_nota,
        total=total,
        status=status,
        tipo_compra=tipo_compra,
        data_prevista_recebimento=data_prevista_recebimento,
        data_prevista_pagamento=data_prevista_pagamento,
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
    tipo_compra: Optional[str] = None,
    pagina: int = 1,
    por_pagina: int = 10,
) -> tuple[list[Compra], int, Decimal]:
    stmt = select(Compra).order_by(Compra.data_compra.desc(), Compra.created_at.desc())
    count_stmt = select(func.count()).select_from(Compra)
    sum_stmt = select(func.sum(Compra.total)).select_from(Compra)

    filters = []
    if data_inicio is not None:
        filters.append(Compra.data_compra >= data_inicio)
    if data_fim is not None:
        filters.append(Compra.data_compra <= data_fim)
    if fornecedor_id is not None:
        filters.append(Compra.fornecedor_id == fornecedor_id)
    if status is not None:
        filters.append(Compra.status == status)
    if tipo_compra is not None:
        filters.append(Compra.tipo_compra == tipo_compra)

    for f in filters:
        stmt = stmt.where(f)
        count_stmt = count_stmt.where(f)
        sum_stmt = sum_stmt.where(f)

    total = db.execute(count_stmt).scalar_one()
    total_periodo = db.execute(sum_stmt).scalar_one() or Decimal("0")
    offset = (pagina - 1) * por_pagina
    compras = list(db.execute(stmt.offset(offset).limit(por_pagina)).scalars().all())
    return compras, total, total_periodo


def list_confirmadas_com_entrega_prevista(
    db: Session, ate: datetime.date
) -> list[Compra]:
    return list(
        db.execute(
            select(Compra).where(
                Compra.status == "confirmado",
                Compra.data_prevista_recebimento <= ate,
            )
        ).scalars().all()
    )


def find_by_numero_nota(db: Session, numero_nota: str) -> Optional[Compra]:
    return db.execute(select(Compra).where(Compra.numero_nota == numero_nota)).scalar_one_or_none()


def get_compra_by_id(db: Session, compra_id: int) -> Optional[Compra]:
    return db.execute(select(Compra).where(Compra.id == compra_id)).scalar_one_or_none()


def get_itens_compra(db: Session, compra_id: int) -> list[ItemCompra]:
    stmt = select(ItemCompra).where(ItemCompra.compra_id == compra_id)
    return list(db.execute(stmt).scalars().all())
