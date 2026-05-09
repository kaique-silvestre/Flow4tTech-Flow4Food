from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.models.categorias import Categoria


def list_all(db: Session) -> list[Categoria]:
    return list(db.execute(select(Categoria).order_by(Categoria.nome)).scalars().all())


def get_by_id(db: Session, categoria_id: int) -> Optional[Categoria]:
    return db.execute(select(Categoria).where(Categoria.id == categoria_id)).scalar_one_or_none()


def has_children(db: Session, categoria_id: int) -> bool:
    result = db.execute(
        select(Categoria.id).where(Categoria.parent_id == categoria_id).limit(1)
    ).first()
    return result is not None


def create(db: Session, nome: str, parent_id: Optional[int] = None) -> Categoria:
    obj = Categoria(nome=nome, parent_id=parent_id)
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


def update(
    db: Session, categoria_id: int, nome: str, parent_id: Optional[int] = None
) -> Optional[Categoria]:
    obj = get_by_id(db, categoria_id)
    if obj is None:
        return None
    obj.nome = nome
    obj.parent_id = parent_id
    db.commit()
    db.refresh(obj)
    return obj


def delete(db: Session, categoria_id: int) -> bool:
    obj = get_by_id(db, categoria_id)
    if obj is None:
        return False
    db.delete(obj)
    db.commit()
    return True
