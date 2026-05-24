from decimal import Decimal
from typing import Optional

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from src.models.ficha_tecnica import FichaTecnica
from src.models.produtos import Produto
from src.schemas.produtos import FichaTecnicaItemRequest, ProdutoCreateRequest, ProdutoUpdateRequest


def list_ativos(
    db: Session,
    categoria_id: Optional[int] = None,
    busca: Optional[str] = None,
    ativo: Optional[bool] = None,
    pagina: int = 1,
    por_pagina: int = 500,
) -> tuple[list[Produto], int]:
    stmt = select(Produto)
    count_stmt = select(func.count()).select_from(Produto)
    if ativo is not None:
        stmt = stmt.where(Produto.ativo == ativo)
        count_stmt = count_stmt.where(Produto.ativo == ativo)
    if categoria_id is not None:
        stmt = stmt.where(Produto.categoria_id == categoria_id)
        count_stmt = count_stmt.where(Produto.categoria_id == categoria_id)
    if busca:
        stmt = stmt.where(Produto.nome.ilike(f"%{busca}%"))
        count_stmt = count_stmt.where(Produto.nome.ilike(f"%{busca}%"))
    stmt = stmt.order_by(Produto.nome)
    total = db.execute(count_stmt).scalar_one()
    offset = (pagina - 1) * por_pagina
    return list(db.execute(stmt.offset(offset).limit(por_pagina)).scalars().all()), total


def get_by_id(db: Session, produto_id: int) -> Optional[Produto]:
    return db.execute(select(Produto).where(Produto.id == produto_id)).scalar_one_or_none()


def create(db: Session, data: ProdutoCreateRequest) -> Produto:
    obj = Produto(
        nome=data.nome,
        categoria_id=data.categoria_id,
        preco_venda=data.preco_venda,
    )
    db.add(obj)
    db.flush()
    return obj


def update(db: Session, produto_id: int, data: ProdutoUpdateRequest) -> Optional[Produto]:
    obj = get_by_id(db, produto_id)
    if obj is None:
        return None
    obj.nome = data.nome
    obj.categoria_id = data.categoria_id
    obj.preco_venda = data.preco_venda
    db.flush()
    return obj


def soft_delete(db: Session, produto_id: int) -> bool:
    obj = get_by_id(db, produto_id)
    if obj is None:
        return False
    obj.ativo = False
    db.commit()
    return True


def is_referenced_in_comanda(db: Session, produto_id: int) -> bool:
    from src.models.itens_comanda import ItemComanda
    result = db.execute(
        select(ItemComanda).where(ItemComanda.produto_id == produto_id).limit(1)
    ).scalar_one_or_none()
    return result is not None


def get_ficha(db: Session, produto_id: int) -> list[FichaTecnica]:
    return list(
        db.execute(
            select(FichaTecnica).where(FichaTecnica.produto_id == produto_id)
        ).scalars().all()
    )


def upsert_ficha(
    db: Session,
    produto_id: int,
    componentes: list[FichaTecnicaItemRequest],
) -> None:
    existing = db.execute(
        select(FichaTecnica).where(FichaTecnica.produto_id == produto_id)
    ).scalars().all()
    for e in existing:
        db.delete(e)
    db.flush()
    for comp in componentes:
        db.add(FichaTecnica(
            produto_id=produto_id,
            insumo_id=comp.insumo_id,
            quantidade=comp.quantidade,
        ))
    db.flush()


def calcular_custo(db: Session, produto_id: int) -> Optional[Decimal]:
    from src.models.insumos import Insumo
    componentes = get_ficha(db, produto_id)
    if not componentes:
        return None
    total = Decimal("0")
    for comp in componentes:
        insumo = db.execute(select(Insumo).where(Insumo.id == comp.insumo_id)).scalar_one_or_none()
        if insumo is None or insumo.custo_medio is None:
            return None
        total += comp.quantidade * insumo.custo_medio
    return total
