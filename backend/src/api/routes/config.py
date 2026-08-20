from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from src.api.dependencies import (
    get_current_user,
    get_db,
    get_tenant_db,
    require_feature,
    require_permission,
)
from src.schemas.config_schemas import (
    EstabelecimentoResponse,
    EstabelecimentoUpdate,
)
from src.services import config_service

router = APIRouter(dependencies=[Depends(require_feature("configuracoes")), Depends(require_permission("configuracoes"))])


@router.get("/estabelecimento", response_model=EstabelecimentoResponse)
def get_estabelecimento(
    db: Session = Depends(get_tenant_db),
    payload: dict = Depends(get_current_user),
) -> EstabelecimentoResponse:
    return config_service.get_estabelecimento(db, payload["tenant_id"])


@router.patch("/estabelecimento", response_model=EstabelecimentoResponse)
def update_estabelecimento(
    body: EstabelecimentoUpdate,
    db: Session = Depends(get_db),
    payload: dict = Depends(get_current_user),
) -> EstabelecimentoResponse:
    # Uses superuser connection (get_db) because app_user has only SELECT on tenants.
    # tenant_id from JWT ensures the user can only update their own tenant.
    return config_service.update_estabelecimento(db, payload["tenant_id"], body)
