from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.models.insumos import Insumo
from src.schemas.insumos import InsumoCreateRequest, InsumoUpdateRequest


def list_ativos(
    db: Session,
    categoria_id: Optional[int] = None,
    busca: Optional[str] = None,
) -> list[Insumo]:
    stmt = select(Insumo).where(Insumo.ativo == True)  # noqa: E712
    if categoria_id is not None:
        stmt = stmt.where(Insumo.categoria_id == categoria_id)
    if busca:
        stmt = stmt.where(Insumo.nome.ilike(f"%{busca}%"))
    stmt = stmt.order_by(Insumo.nome)
    return list(db.execute(stmt).scalars().all())


def get_by_id(db: Session, insumo_id: int) -> Optional[Insumo]:
    return db.execute(select(Insumo).where(Insumo.id == insumo_id)).scalar_one_or_none()


def create(db: Session, data: InsumoCreateRequest) -> Insumo:
    obj = Insumo(
        nome=data.nome,
        categoria_id=data.categoria_id,
        unidade_base=data.unidade_base,
        quantidade_caixa=data.quantidade_caixa,
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
