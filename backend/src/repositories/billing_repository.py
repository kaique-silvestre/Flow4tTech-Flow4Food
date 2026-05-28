import datetime
from decimal import Decimal
from typing import Optional

import sqlalchemy as sa
from sqlalchemy.orm import Session

from src.models.assinaturas import Assinatura
from src.models.billing import PagamentoAssinatura, Plano


def list_planos(db: Session) -> list[Plano]:
    return db.query(Plano).order_by(Plano.nome).all()


def get_plano_by_id(db: Session, plano_id: int) -> Optional[Plano]:
    return db.query(Plano).filter(Plano.id == plano_id).first()


def create_plano(db: Session, nome: str, descricao: Optional[str], preco_mensal: Decimal) -> Plano:
    plano = Plano(nome=nome, descricao=descricao, preco_mensal=preco_mensal)
    db.add(plano)
    db.commit()
    db.refresh(plano)
    return plano


def create_pagamento(
    db: Session,
    tenant_id: int,
    valor: Decimal,
    data_pagamento: datetime.date,
    data_vencimento: Optional[datetime.date],
    gateway_ref: Optional[str],
) -> PagamentoAssinatura:
    pag = PagamentoAssinatura(
        tenant_id=tenant_id,
        valor=valor,
        data_pagamento=data_pagamento,
        data_vencimento=data_vencimento,
        gateway_ref=gateway_ref,
    )
    db.add(pag)
    db.commit()
    db.refresh(pag)
    return pag


def get_assinatura_by_tenant(db: Session, tenant_id: int) -> Optional[Assinatura]:
    return db.query(Assinatura).filter(Assinatura.tenant_id == tenant_id).first()


def update_assinatura_status(
    db: Session,
    assinatura: Assinatura,
    status: str,
    data_vencimento: Optional[datetime.date],
) -> Assinatura:
    assinatura.status = status
    if data_vencimento is not None:
        assinatura.data_vencimento = datetime.datetime.combine(data_vencimento, datetime.time.min, tzinfo=datetime.timezone.utc)
    assinatura.updated_at = datetime.datetime.now(datetime.timezone.utc)
    db.commit()
    db.refresh(assinatura)
    return assinatura


def marcar_vencidas(db: Session) -> int:
    hoje = datetime.date.today()
    now = datetime.datetime.now(datetime.timezone.utc)
    vencidas = (
        db.query(Assinatura)
        .filter(
            Assinatura.status == "ativa",
            Assinatura.data_vencimento.isnot(None),
            sa.cast(Assinatura.data_vencimento, sa.Date) < hoje,
        )
        .all()
    )
    for row in vencidas:
        row.status = "vencida"
        row.updated_at = now
    db.commit()
    return len(vencidas)
