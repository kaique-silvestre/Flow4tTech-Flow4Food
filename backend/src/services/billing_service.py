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
