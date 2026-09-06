from datetime import datetime, timezone
from typing import Optional

from sqlalchemy.orm import Session

from src.core.errors import AppError, ErrorCode
from src.repositories import billing_repository
from src.schemas.billing import (
    AssinaturaUpdate,
    PagamentoCreate,
    PagamentoInfo,
    PlanoCreate,
    PlanoInfo,
)
from src.schemas.tenants import AssinaturaInfo

_BLOCKED_STATUSES = {"suspensa", "cancelada"}


def evaluate_subscription_block(
    status: str, data_vencimento: Optional[datetime]
) -> Optional[dict]:
    """Decide whether a subscription should block access.

    Pure business rule — no DB/FastAPI dependency — extracted out of
    api/dependencies.check_subscription so the "what counts as blocked" logic
    lives with the rest of billing. The DB fetch and HTTPException raising
    stay in dependencies.py: check_subscription is wired into a Depends()
    chain (get_current_user -> check_subscription -> get_tenant_db) and
    moving the session lookup there too would mean either duplicating that
    chain here or making this module depend on FastAPI's Depends, which
    isn't worth it for a two-line query.

    Returns a dict with the blocking status (for the 402 detail payload) or
    None if the subscription is fine.
    """
    now = datetime.now(timezone.utc)
    dv = data_vencimento
    if dv is not None and dv.tzinfo is None:
        dv = dv.replace(tzinfo=timezone.utc)
    trial_expired = status == "trial" and dv is not None and dv < now
    if status in _BLOCKED_STATUSES or trial_expired:
        return {"status": status}
    return None


def listar_planos(db: Session) -> list[PlanoInfo]:
    return [PlanoInfo.model_validate(p) for p in billing_repository.list_planos(db)]


def criar_plano(db: Session, data: PlanoCreate) -> PlanoInfo:
    plano = billing_repository.create_plano(db, data.nome, data.descricao, data.preco_mensal)
    return PlanoInfo.model_validate(plano)


def registrar_pagamento(db: Session, tenant_id: int, data: PagamentoCreate) -> PagamentoInfo:
    pag = billing_repository.create_pagamento(
        db,
        tenant_id=tenant_id,
        valor=data.valor,
        data_pagamento=data.data_pagamento,
        data_vencimento=data.data_vencimento,
        gateway_ref=data.gateway_ref,
    )
    return PagamentoInfo.model_validate(pag)


def atualizar_assinatura(db: Session, tenant_id: int, data: AssinaturaUpdate) -> AssinaturaInfo:
    assinatura = billing_repository.get_assinatura_by_tenant(db, tenant_id)
    if assinatura is None:
        raise AppError(code=ErrorCode.NOT_FOUND, message="Assinatura não encontrada", http_status=404)
    assinatura = billing_repository.update_assinatura_status(
        db, assinatura, data.status, data.data_vencimento
    )
    return AssinaturaInfo(
        id=assinatura.id,
        status=assinatura.status,
        data_inicio=assinatura.data_inicio,
        data_vencimento=assinatura.data_vencimento,
    )


def marcar_assinaturas_vencidas(db: Session) -> int:
    return billing_repository.marcar_vencidas(db)
