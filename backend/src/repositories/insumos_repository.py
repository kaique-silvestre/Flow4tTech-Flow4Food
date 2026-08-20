from typing import Optional

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from src.models.insumos import Insumo
from src.schemas.insumos import InsumoCreateRequest, InsumoUpdateRequest


def list_ativos(
    db: Session,
    categoria_id: Optional[int] = None,
    busca: Optional[str] = None,
    pagina: int = 1,
    por_pagina: int = 500,
) -> tuple[list[Insumo], int]:
    stmt = select(Insumo).where(Insumo.ativo == True)  # noqa: E712
    count_stmt = select(func.count()).select_from(Insumo).where(Insumo.ativo == True)  # noqa: E712
    if categoria_id is not None:
        stmt = stmt.where(Insumo.categoria_id == categoria_id)
        count_stmt = count_stmt.where(Insumo.categoria_id == categoria_id)
    if busca:
        stmt = stmt.where(Insumo.nome.ilike(f"%{busca}%"))
        count_stmt = count_stmt.where(Insumo.nome.ilike(f"%{busca}%"))
    stmt = stmt.order_by(Insumo.nome)
    total = db.execute(count_stmt).scalar_one()
    offset = (pagina - 1) * por_pagina
    return list(db.execute(stmt.offset(offset).limit(por_pagina)).scalars().all()), total


def list_all(
    db: Session,
    busca: Optional[str] = None,
    pagina: int = 1,
    por_pagina: int = 500,
) -> tuple[list[Insumo], int]:
    stmt = select(Insumo)
    count_stmt = select(func.count()).select_from(Insumo)
    if busca:
        stmt = stmt.where(Insumo.nome.ilike(f"%{busca}%"))
        count_stmt = count_stmt.where(Insumo.nome.ilike(f"%{busca}%"))
    stmt = stmt.order_by(Insumo.nome)
    total = db.execute(count_stmt).scalar_one()
    offset = (pagina - 1) * por_pagina
    return list(db.execute(stmt.offset(offset).limit(por_pagina)).scalars().all()), total


def get_by_id(db: Session, insumo_id: int) -> Optional[Insumo]:
    return db.execute(select(Insumo).where(Insumo.id == insumo_id)).scalar_one_or_none()


def create(db: Session, data: InsumoCreateRequest) -> Insumo:
    obj = Insumo(
        nome=data.nome,
        categoria_id=data.categoria_id,
        unidade_base=data.unidade_base,
        quantidade_caixa=data.quantidade_caixa,
        ean=data.ean,
    )
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


def update(db: Session, insumo_id: int, data: InsumoUpdateRequest) -> Optional[Insumo]:
    obj = get_by_id(db, insumo_id)
    if obj is None:
        return None
    obj.nome = data.nome
    obj.categoria_id = data.categoria_id
    obj.unidade_base = data.unidade_base
    obj.quantidade_caixa = data.quantidade_caixa
    obj.nivel_critico = data.nivel_critico
    obj.ean = data.ean
    db.commit()
    db.refresh(obj)
    return obj


def get_by_ean(db: Session, ean: str) -> Optional[Insumo]:
    return db.execute(
        select(Insumo).where(Insumo.ean == ean, Insumo.ativo == True).limit(1)  # noqa: E712
    ).scalars().first()


def toggle_ativo(db: Session, insumo_id: int) -> Optional[Insumo]:
    obj = get_by_id(db, insumo_id)
    if obj is None:
        return None
    obj.ativo = not obj.ativo
    db.commit()
    db.refresh(obj)
    return obj


def soft_delete(db: Session, insumo_id: int) -> bool:
    obj = get_by_id(db, insumo_id)
    if obj is None:
        return False
    obj.ativo = False
    db.commit()
    return True


def hard_delete(db: Session, insumo_id: int) -> bool:
    obj = get_by_id(db, insumo_id)
    if obj is None:
        return False
    db.delete(obj)
    db.commit()
    return True


def is_referenced_in_ficha(db: Session, insumo_id: int) -> bool:
    from src.models.ficha_tecnica import FichaTecnica
    result = db.execute(
        select(FichaTecnica).where(FichaTecnica.insumo_id == insumo_id).limit(1)
    ).scalar_one_or_none()
    return result is not None


def is_referenced_in_movimentos(db: Session, insumo_id: int) -> bool:
    from src.models.movimentos_estoque import MovimentoEstoque
    result = db.execute(
        select(MovimentoEstoque).where(MovimentoEstoque.insumo_id == insumo_id).limit(1)
    ).scalar_one_or_none()
    return result is not None


def is_referenced_in_compras(db: Session, insumo_id: int) -> bool:
    from src.models.compras import ItemCompra
    result = db.execute(
        select(ItemCompra).where(ItemCompra.insumo_id == insumo_id).limit(1)
    ).scalar_one_or_none()
    return result is not None
