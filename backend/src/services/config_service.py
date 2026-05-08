from sqlalchemy.orm import Session

from src.core.errors import AppError, ErrorCode
from src.repositories import auth_repository, estabelecimento_repository
from src.schemas.config_schemas import (
    AlterarSenhaRequest,
    EstabelecimentoResponse,
    EstabelecimentoUpdate,
)
from src.services.auth_service import hash_password, verify_password


def get_estabelecimento(db: Session) -> EstabelecimentoResponse:
    est = estabelecimento_repository.get_estabelecimento(db)
    if est is None:
        return EstabelecimentoResponse(
            id=1, nome="Estabelecimento", cnpj=None, endereco=None, telefone=None
        )
    return EstabelecimentoResponse.model_validate(est)


def update_estabelecimento(
    db: Session, body: EstabelecimentoUpdate
) -> EstabelecimentoResponse:
    est = estabelecimento_repository.upsert_estabelecimento(
        db,
        nome=body.nome,
        cnpj=body.cnpj,
        endereco=body.endereco,
        telefone=body.telefone,
    )
    return EstabelecimentoResponse.model_validate(est)


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
