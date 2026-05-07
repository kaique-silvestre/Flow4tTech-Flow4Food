from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.models.fornecedores import Fornecedor
from src.schemas.fornecedores import FornecedorCreateRequest, FornecedorUpdateRequest


def list_all(db: Session) -> list[Fornecedor]:
    return list(db.execute(select(Fornecedor).order_by(Fornecedor.nome)).scalars().all())


def get_by_id(db: Session, fornecedor_id: int) -> Optional[Fornecedor]:
    return db.execute(select(Fornecedor).where(Fornecedor.id == fornecedor_id)).scalar_one_or_none()


def create(db: Session, data: FornecedorCreateRequest) -> Fornecedor:
    obj = Fornecedor(nome=data.nome, telefone=data.telefone, email=data.email)
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


def update(db: Session, fornecedor_id: int, data: FornecedorUpdateRequest) -> Optional[Fornecedor]:
    obj = get_by_id(db, fornecedor_id)
    if obj is None:
        return None
    obj.nome = data.nome
    obj.telefone = data.telefone
    obj.email = data.email
    db.commit()
    db.refresh(obj)
    return obj


def delete(db: Session, fornecedor_id: int) -> bool:
    obj = get_by_id(db, fornecedor_id)
    if obj is None:
        return False
    db.delete(obj)
    db.commit()
    return True
