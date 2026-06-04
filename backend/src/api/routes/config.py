from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from src.api.dependencies import get_current_user, get_db, get_tenant_db, require_permission
from src.schemas.config_schemas import (
    AlterarSenhaRequest,
    EstabelecimentoResponse,
    EstabelecimentoUpdate,
)
from src.services import config_service

router = APIRouter(dependencies=[Depends(require_permission("configuracoes"))])


@router.get("/estabelecimento", response_model=EstabelecimentoResponse)
def get_estabelecimento(
    db: Session = Depends(get_tenant_db),
) -> EstabelecimentoResponse:
    return config_service.get_estabelecimento(db)


@router.patch("/estabelecimento", response_model=EstabelecimentoResponse)
def update_estabelecimento(
    body: EstabelecimentoUpdate,
    db: Session = Depends(get_tenant_db),
) -> EstabelecimentoResponse:
    return config_service.update_estabelecimento(db, body)


@router.patch("/senha", status_code=204)
def alterar_senha(
    body: AlterarSenhaRequest,
    db: Session = Depends(get_db),
    _user: dict = Depends(get_current_user),
) -> None:
    config_service.alterar_senha(db, body)
