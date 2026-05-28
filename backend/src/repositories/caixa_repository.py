import datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from src.models.caixa import CaixaMovimento, CaixaSessao, StatusCaixa
from src.models.metodos_pagamento import MetodoPagamento
from src.models.pagamentos import Pagamento


def get_sessao_aberta(db: Session) -> Optional[CaixaSessao]:
    return db.execute(
        select(CaixaSessao).where(CaixaSessao.status == StatusCaixa.ABERTA.value)
    ).scalar_one_or_none()


def criar_sessao(db: Session, valor_abertura: Decimal, user_id: int) -> CaixaSessao:
    sessao = CaixaSessao(
        valor_abertura=valor_abertura,
        aberto_por_user_id=user_id,
        status=StatusCaixa.ABERTA.value,
    )
    db.add(sessao)
    db.flush()
    return sessao


def fechar_sessao(
    db: Session,
    sessao: CaixaSessao,
    valor_informado: Decimal,
    valor_esperado: Decimal,
    user_id: int,
    observacao: Optional[str] = None,
) -> CaixaSessao:
    sessao.status = StatusCaixa.FECHADA.value
    sessao.valor_informado = valor_informado
    sessao.valor_esperado = valor_esperado
    sessao.diferenca = valor_informado - valor_esperado
    sessao.fechado_por_user_id = user_id
    sessao.closed_at = datetime.datetime.utcnow()
    sessao.observacao = observacao
    db.flush()
    return sessao


def criar_movimento(
    db: Session,
    sessao_id: int,
    tipo: str,
    valor: Decimal,
    motivo: str,
    user_id: int,
) -> CaixaMovimento:
    mov = CaixaMovimento(
        sessao_id=sessao_id,
        tipo=tipo,
        valor=valor,
        motivo=motivo,
        user_id=user_id,
    )
    db.add(mov)
    db.flush()
    return mov


def list_movimentos(db: Session, sessao_id: int) -> list[CaixaMovimento]:
    return list(
        db.execute(
            select(CaixaMovimento)
            .where(CaixaMovimento.sessao_id == sessao_id)
            .order_by(CaixaMovimento.created_at)
        ).scalars().all()
    )


def sum_movimentos_tipo(db: Session, sessao_id: int, tipo: str) -> Decimal:
    result = db.execute(
        select(func.sum(CaixaMovimento.valor)).where(
            CaixaMovimento.sessao_id == sessao_id,
            CaixaMovimento.tipo == tipo,
        )
    ).scalar_one()
    return result or Decimal("0")


def sum_pagamentos_dinheiro(
    db: Session, opened_at: datetime.datetime, closed_at: Optional[datetime.datetime] = None
) -> Decimal:
    stmt = (
        select(func.sum(Pagamento.valor))
        .join(MetodoPagamento, Pagamento.metodo_id == MetodoPagamento.id)
        .where(
            MetodoPagamento.tipo == "dinheiro",
            Pagamento.created_at >= opened_at,
        )
    )
    if closed_at is not None:
        stmt = stmt.where(Pagamento.created_at <= closed_at)
    result = db.execute(stmt).scalar_one()
    return result or Decimal("0")
