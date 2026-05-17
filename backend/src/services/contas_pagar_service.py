import datetime
import math
from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.core.errors import AppError, ErrorCode
from src.models.fornecedores import Fornecedor
from src.repositories import contas_pagar_repository, notificacoes_repository
from src.schemas.contas_pagar_schemas import (
    ContaPagarResponse,
    ContasPagarPageResponse,
    ContasPagarResumoResponse,
    NotificacaoResponse,
    PagarContaRequest,
)


def _fornecedor_nome(db: Session, fornecedor_id: Optional[int]) -> Optional[str]:
    if not fornecedor_id:
        return None
    f = db.execute(select(Fornecedor).where(Fornecedor.id == fornecedor_id)).scalar_one_or_none()
    return f.nome if f else None


def _to_response(db: Session, conta: object) -> ContaPagarResponse:
    return ContaPagarResponse(
        id=conta.id,  # type: ignore[attr-defined]
        compra_id=conta.compra_id,  # type: ignore[attr-defined]
        fornecedor_id=conta.fornecedor_id,  # type: ignore[attr-defined]
        fornecedor_nome=_fornecedor_nome(db, conta.fornecedor_id),  # type: ignore[attr-defined]
        valor=conta.valor,  # type: ignore[attr-defined]
        data_vencimento=conta.data_vencimento,  # type: ignore[attr-defined]
        data_pagamento=conta.data_pagamento,  # type: ignore[attr-defined]
        status=conta.status,  # type: ignore[attr-defined]
        metodo_pagamento_id=conta.metodo_pagamento_id,  # type: ignore[attr-defined]
        observacao=conta.observacao,  # type: ignore[attr-defined]
        created_at=conta.created_at,  # type: ignore[attr-defined]
    )


def list_contas(
    db: Session,
    status: Optional[str] = None,
    data_vencimento_inicio: Optional[str] = None,
    data_vencimento_fim: Optional[str] = None,
    fornecedor_id: Optional[int] = None,
    pagina: int = 1,
    por_pagina: int = 20,
) -> ContasPagarPageResponse:
    di = datetime.date.fromisoformat(data_vencimento_inicio) if data_vencimento_inicio else None
    df = datetime.date.fromisoformat(data_vencimento_fim) if data_vencimento_fim else None

    contas, total, total_pendente, total_vencido = contas_pagar_repository.list_contas(
        db, status, di, df, fornecedor_id, pagina, por_pagina
    )
    return ContasPagarPageResponse(
        itens=[_to_response(db, c) for c in contas],
        total=total,
        pagina=pagina,
        por_pagina=por_pagina,
        total_paginas=max(1, math.ceil(total / por_pagina)),
        total_pendente=total_pendente,
        total_vencido=total_vencido,
    )


def pagar_conta(db: Session, conta_id: int, data: PagarContaRequest) -> ContaPagarResponse:
    conta = contas_pagar_repository.get_by_id(db, conta_id)
    if conta is None:
        raise AppError(ErrorCode.NOT_FOUND, "Conta não encontrada", http_status=404)
    if conta.status not in ("pendente", "vencido"):
        raise AppError(
            ErrorCode.CONFLICT,
            f"Conta com status '{conta.status}' não pode ser paga",
            http_status=409,
        )
    try:
        conta.status = "pago"
        conta.data_pagamento = data.data_pagamento
        conta.metodo_pagamento_id = data.metodo_pagamento_id
        conta.observacao = data.observacao
        db.commit()
    except Exception:
        db.rollback()
        raise
    db.refresh(conta)
    return _to_response(db, conta)


def resumo(db: Session) -> ContasPagarResumoResponse:
    hoje = datetime.date.today()
    r = contas_pagar_repository.resumo(db, hoje)
    return ContasPagarResumoResponse(**r)


def atualizar_vencidos(db: Session) -> int:
    hoje = datetime.date.today()
    pendentes_vencidos = contas_pagar_repository.get_pendentes_vencidos(db, hoje)
    for conta in pendentes_vencidos:
        conta.status = "vencido"
    db.commit()
    return len(pendentes_vencidos)


def list_notificacoes(db: Session) -> list[NotificacaoResponse]:
    notifs = notificacoes_repository.list_pendentes(db)
    return [NotificacaoResponse.model_validate(n) for n in notifs]


def marcar_notificacao_lida(db: Session, notificacao_id: int) -> None:
    n = notificacoes_repository.marcar_lida(db, notificacao_id)
    if n is None:
        raise AppError(ErrorCode.NOT_FOUND, "Notificação não encontrada", http_status=404)
    db.commit()
