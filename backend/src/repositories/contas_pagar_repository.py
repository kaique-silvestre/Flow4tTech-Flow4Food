import datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from src.models.contas_pagar import ContaPagar


def create_conta(
    db: Session,
    compra_id: Optional[int],
    fornecedor_id: Optional[int],
    valor: Decimal,
    data_vencimento: datetime.date,
) -> ContaPagar:
    conta = ContaPagar(
        compra_id=compra_id,
        fornecedor_id=fornecedor_id,
        valor=valor,
        data_vencimento=data_vencimento,
        status="pendente",
    )
    db.add(conta)
    db.flush()
    return conta


def get_by_id(db: Session, conta_id: int) -> Optional[ContaPagar]:
    return db.execute(select(ContaPagar).where(ContaPagar.id == conta_id)).scalar_one_or_none()


def list_contas(
    db: Session,
    status: Optional[str] = None,
    data_vencimento_inicio: Optional[datetime.date] = None,
    data_vencimento_fim: Optional[datetime.date] = None,
    fornecedor_id: Optional[int] = None,
    pagina: int = 1,
    por_pagina: int = 20,
) -> tuple[list[ContaPagar], int, Decimal, Decimal]:
    stmt = select(ContaPagar).order_by(ContaPagar.data_vencimento.asc())
    count_stmt = select(func.count()).select_from(ContaPagar)

    filters = []
    if status:
        filters.append(ContaPagar.status == status)
    if data_vencimento_inicio:
        filters.append(ContaPagar.data_vencimento >= data_vencimento_inicio)
    if data_vencimento_fim:
        filters.append(ContaPagar.data_vencimento <= data_vencimento_fim)
    if fornecedor_id:
        filters.append(ContaPagar.fornecedor_id == fornecedor_id)

    for f in filters:
        stmt = stmt.where(f)
        count_stmt = count_stmt.where(f)

    total = db.execute(count_stmt).scalar_one()

    total_pendente = db.execute(
        select(func.sum(ContaPagar.valor)).where(ContaPagar.status == "pendente")
    ).scalar_one() or Decimal("0")

    total_vencido = db.execute(
        select(func.sum(ContaPagar.valor)).where(ContaPagar.status == "vencido")
    ).scalar_one() or Decimal("0")

    offset = (pagina - 1) * por_pagina
    contas = list(db.execute(stmt.offset(offset).limit(por_pagina)).scalars().all())
    return contas, total, total_pendente, total_vencido


def cancelar_por_compra(db: Session, compra_id: int) -> None:
    contas = list(
        db.execute(
            select(ContaPagar).where(
                ContaPagar.compra_id == compra_id,
                ContaPagar.status.in_(["pendente", "vencido"]),
            )
        ).scalars().all()
    )
    for conta in contas:
        conta.status = "cancelado"


def get_pendentes_vencidos(db: Session, hoje: datetime.date) -> list[ContaPagar]:
    return list(
        db.execute(
            select(ContaPagar).where(
                ContaPagar.status == "pendente",
                ContaPagar.data_vencimento < hoje,
            )
        ).scalars().all()
    )


def resumo(db: Session, hoje: datetime.date) -> dict:
    pendente = db.execute(
        select(func.count()).select_from(ContaPagar).where(
            ContaPagar.status.in_(["pendente", "vencido"]),
            ContaPagar.data_vencimento <= hoje,
        )
    ).scalar_one()

    vencido = db.execute(
        select(func.count()).select_from(ContaPagar).where(ContaPagar.status == "vencido")
    ).scalar_one()

    total_vencido = db.execute(
        select(func.sum(ContaPagar.valor)).where(ContaPagar.status == "vencido")
    ).scalar_one() or Decimal("0")

    return {"pendente": pendente, "vencido": vencido, "total_vencido": total_vencido}
