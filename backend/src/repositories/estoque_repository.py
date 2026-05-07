import datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from src.models.itens import Item, TipoItem
from src.models.movimentos_estoque import MovimentoEstoque, TipoMovimento


def get_item_for_update(db: Session, item_id: int) -> Optional[Item]:
    return db.execute(select(Item).where(Item.id == item_id)).scalar_one_or_none()


def update_estoque_e_custo(
    db: Session,
    item_id: int,
    novo_estoque: Decimal,
    novo_custo_medio: Optional[Decimal],
) -> None:
    item = db.execute(select(Item).where(Item.id == item_id)).scalar_one_or_none()
    if item is not None:
        item.estoque_atual = novo_estoque
        item.custo_medio = novo_custo_medio


def registrar_movimento(
    db: Session,
    item_id: int,
    tipo: TipoMovimento,
    quantidade: Decimal,
    custo_unitario: Optional[Decimal],
    saldo_apos: Decimal,
    motivo: Optional[str] = None,
    observacao: Optional[str] = None,
    compra_id: Optional[int] = None,
) -> MovimentoEstoque:
    mov = MovimentoEstoque(
        item_id=item_id,
        tipo=tipo.value,
        quantidade=quantidade,
        custo_unitario=custo_unitario,
        saldo_apos=saldo_apos,
        motivo=motivo,
        observacao=observacao,
        compra_id=compra_id,
    )
    db.add(mov)
    db.flush()
    return mov


def list_saldo(
    db: Session,
    categoria_id: Optional[int] = None,
    busca: Optional[str] = None,
) -> list[Item]:
    stmt = (
        select(Item)
        .where(Item.tipo == TipoItem.SIMPLES.value)
        .where(Item.ativo == True)  # noqa: E712
        .order_by(Item.nome)
    )
    if categoria_id is not None:
        stmt = stmt.where(Item.categoria_id == categoria_id)
    if busca:
        stmt = stmt.where(Item.nome.ilike(f"%{busca}%"))
    return list(db.execute(stmt).scalars().all())


def list_movimentos(
    db: Session,
    item_id: Optional[int] = None,
    tipo: Optional[str] = None,
    data_inicio: Optional[datetime.date] = None,
    data_fim: Optional[datetime.date] = None,
    pagina: int = 1,
    por_pagina: int = 50,
) -> tuple[list[MovimentoEstoque], int]:
    stmt = select(MovimentoEstoque).order_by(MovimentoEstoque.created_at.desc(), MovimentoEstoque.id.desc())
    count_stmt = select(func.count()).select_from(MovimentoEstoque)

    if item_id is not None:
        stmt = stmt.where(MovimentoEstoque.item_id == item_id)
        count_stmt = count_stmt.where(MovimentoEstoque.item_id == item_id)
    if tipo is not None:
        stmt = stmt.where(MovimentoEstoque.tipo == tipo)
        count_stmt = count_stmt.where(MovimentoEstoque.tipo == tipo)
    if data_inicio is not None:
        stmt = stmt.where(func.date(MovimentoEstoque.created_at) >= data_inicio)
        count_stmt = count_stmt.where(func.date(MovimentoEstoque.created_at) >= data_inicio)
    if data_fim is not None:
        stmt = stmt.where(func.date(MovimentoEstoque.created_at) <= data_fim)
        count_stmt = count_stmt.where(func.date(MovimentoEstoque.created_at) <= data_fim)

    total = db.execute(count_stmt).scalar_one()
    offset = (pagina - 1) * por_pagina
    resultados = list(db.execute(stmt.offset(offset).limit(por_pagina)).scalars().all())
    return resultados, total
