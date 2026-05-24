from typing import Optional

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from src.models.fornecedores import Fornecedor
from src.schemas.fornecedores import FornecedorCreateRequest, FornecedorUpdateRequest


def list_all(
    db: Session,
    busca: Optional[str] = None,
    pagina: int = 1,
    por_pagina: int = 500,
) -> tuple[list[Fornecedor], int]:
    stmt = select(Fornecedor).order_by(Fornecedor.nome)
    count_stmt = select(func.count()).select_from(Fornecedor)
    if busca:
        stmt = stmt.where(Fornecedor.nome.ilike(f"%{busca}%"))
        count_stmt = count_stmt.where(Fornecedor.nome.ilike(f"%{busca}%"))
    total = db.execute(count_stmt).scalar_one()
    offset = (pagina - 1) * por_pagina
    return list(db.execute(stmt.offset(offset).limit(por_pagina)).scalars().all()), total


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


def toggle_ativo(db: Session, fornecedor_id: int) -> Optional[Fornecedor]:
    obj = get_by_id(db, fornecedor_id)
    if obj is None:
        return None
    obj.ativo = not obj.ativo
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
