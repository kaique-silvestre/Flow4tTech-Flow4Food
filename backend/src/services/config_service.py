from sqlalchemy.orm import Session

from src.core.errors import AppError, ErrorCode
from src.repositories import auth_repository, estabelecimento_repository
from src.schemas.config_schemas import (
    AlterarSenhaRequest,
    EstabelecimentoResponse,
    EstabelecimentoUpdate,
)
from src.services.auth_service import hash_password, verify_password


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


def alterar_senha(db: Session, body: AlterarSenhaRequest) -> None:
    # MVP: sem revogação de JWT — tokens emitidos antes da troca continuam válidos.
    config = auth_repository.get_config(db)
    if config is None or not verify_password(body.senha_atual, config.senha_hash):
        raise AppError(
            code=ErrorCode.SENHA_INCORRETA,
            message="Senha atual incorreta",
            http_status=401,
        )
    auth_repository.upsert_config(db, hash_password(body.nova_senha))
