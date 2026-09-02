import datetime

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from src.core.errors import AppError, ErrorCode
from src.models.caixa import CaixaSessao, TipoMovimentoCaixa
from src.repositories import caixa_repository
from src.schemas.caixa import (
    AbrirCaixaRequest,
    CaixaMovimentoResponse,
    CaixaSessaoResponse,
    FecharCaixaRequest,
    MovimentoCaixaRequest,
)


def _build_sessao_response(db: Session, sessao: CaixaSessao) -> CaixaSessaoResponse:
    movimentos = caixa_repository.list_movimentos(db, sessao.id)
    return CaixaSessaoResponse(
        id=sessao.id,
        status=sessao.status,
        valor_abertura=sessao.valor_abertura,
        valor_informado=sessao.valor_informado,
        valor_esperado=sessao.valor_esperado,
        diferenca=sessao.diferenca,
        aberto_por_user_id=sessao.aberto_por_user_id,
        fechado_por_user_id=sessao.fechado_por_user_id,
        opened_at=sessao.opened_at,
        closed_at=sessao.closed_at,
        observacao=sessao.observacao,
        created_at=sessao.created_at,
        movimentos=[CaixaMovimentoResponse.model_validate(m) for m in movimentos],
    )


def abrir_caixa(db: Session, body: AbrirCaixaRequest, user_id: int) -> CaixaSessaoResponse:
    sessao_existente = caixa_repository.get_sessao_aberta(db)
    if sessao_existente is not None:
        raise AppError(
            code=ErrorCode.CONFLICT,
            message="Já existe uma sessão de caixa aberta",
            http_status=409,
        )
    try:
        sessao = caixa_repository.criar_sessao(db, body.valor_abertura, user_id)
        db.commit()
    except IntegrityError:
        db.rollback()
        raise AppError(
            code=ErrorCode.CONFLICT,
            message="Já existe uma sessão de caixa aberta",
            http_status=409,
        ) from None
    db.refresh(sessao)
    return _build_sessao_response(db, sessao)


def fechar_caixa(
    db: Session, body: FecharCaixaRequest, user_id: int
) -> CaixaSessaoResponse:
    sessao = caixa_repository.get_sessao_aberta(db)
    if sessao is None:
        raise AppError(
            code=ErrorCode.NOT_FOUND,
            message="Nenhuma sessão de caixa aberta",
            http_status=404,
        )
    now = datetime.datetime.utcnow()
    suprimentos = caixa_repository.sum_movimentos_tipo(
        db, sessao.id, TipoMovimentoCaixa.SUPRIMENTO.value
    )
    sangrias = caixa_repository.sum_movimentos_tipo(
        db, sessao.id, TipoMovimentoCaixa.SANGRIA.value
    )
    pagamentos_dinheiro = caixa_repository.sum_pagamentos_dinheiro(db, sessao.opened_at, now)
    valor_esperado = sessao.valor_abertura + pagamentos_dinheiro + suprimentos - sangrias

    sessao_fechada = caixa_repository.fechar_sessao(
        db,
        sessao_id=sessao.id,
        valor_informado=body.valor_informado,
        valor_esperado=valor_esperado,
        user_id=user_id,
        observacao=body.observacao,
    )
    if sessao_fechada is None:
        db.rollback()
        raise AppError(
            code=ErrorCode.CAIXA_JA_FECHADO,
            message="Caixa já foi fechado por outra operação",
            http_status=409,
        )
    db.commit()
    db.refresh(sessao_fechada)
    return _build_sessao_response(db, sessao_fechada)


def registrar_movimento(
    db: Session, body: MovimentoCaixaRequest, user_id: int
) -> CaixaMovimentoResponse:
    # Locks the session row so a concurrent `fechar_caixa` can't close the
    # session between this check and the insert below, which would let the
    # movement land after closing without being reflected in valor_esperado.
    sessao = caixa_repository.get_sessao_aberta(db, for_update=True)
    if sessao is None:
        raise AppError(
            code=ErrorCode.NOT_FOUND,
            message="Nenhuma sessão de caixa aberta",
            http_status=404,
        )
    mov = caixa_repository.criar_movimento(
        db,
        sessao_id=sessao.id,
        tipo=body.tipo,
        valor=body.valor,
        motivo=body.motivo,
        user_id=user_id,
    )
    db.commit()
    db.refresh(mov)
    return CaixaMovimentoResponse.model_validate(mov)


def get_sessao_aberta(db: Session) -> CaixaSessaoResponse:
    sessao = caixa_repository.get_sessao_aberta(db)
    if sessao is None:
        raise AppError(
            code=ErrorCode.NOT_FOUND,
            message="Nenhuma sessão de caixa aberta",
            http_status=404,
        )
    return _build_sessao_response(db, sessao)
