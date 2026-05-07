from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.models.categorias import Categoria


def list_all(db: Session) -> list[Categoria]:
    return list(db.execute(select(Categoria).order_by(Categoria.nome)).scalars().all())


def get_by_id(db: Session, categoria_id: int) -> Optional[Categoria]:
    return db.execute(select(Categoria).where(Categoria.id == categoria_id)).scalar_one_or_none()


def create(db: Session, nome: str) -> Categoria:
    obj = Categoria(nome=nome)
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


def update(db: Session, categoria_id: int, nome: str) -> Optional[Categoria]:
    obj = get_by_id(db, categoria_id)
    if obj is None:
        return None
    obj.nome = nome
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
