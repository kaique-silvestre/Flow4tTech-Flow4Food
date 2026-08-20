from sqlalchemy.orm import Session

from src.repositories import estabelecimento_repository
from src.schemas.config_schemas import (
    EstabelecimentoResponse,
    EstabelecimentoUpdate,
)


def _tenant_to_response(tenant) -> EstabelecimentoResponse:
    return EstabelecimentoResponse(
        id=tenant.id,
        nome=tenant.nome_fantasia,
        cnpj=tenant.cnpj,
        endereco=tenant.endereco,
        telefone=tenant.telefone,
    )


def get_estabelecimento(db: Session, tenant_id: int) -> EstabelecimentoResponse:
    tenant = estabelecimento_repository.get_estabelecimento(db, tenant_id)
    if tenant is None:
        return EstabelecimentoResponse(
            id=tenant_id, nome="Estabelecimento", cnpj=None, endereco=None, telefone=None
        )
    return _tenant_to_response(tenant)


def update_estabelecimento(
    db: Session, tenant_id: int, body: EstabelecimentoUpdate
) -> EstabelecimentoResponse:
    tenant = estabelecimento_repository.upsert_estabelecimento(
        db,
        tenant_id=tenant_id,
        nome=body.nome,
        cnpj=body.cnpj,
        endereco=body.endereco,
        telefone=body.telefone,
    )
    return _tenant_to_response(tenant)
