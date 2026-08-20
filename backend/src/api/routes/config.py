from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from src.api.dependencies import (
    check_subscription,
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
    payload: dict = Depends(check_subscription),
) -> EstabelecimentoResponse:
    # Uses superuser connection (get_db) because app_user has only SELECT on tenants
    # (see alembic 0050_create_app_user_role.py and 0069_merge_estabelecimento_into_tenants.py —
    # UPDATE on tenants is intentionally NOT granted to app_user). Swapping to get_tenant_db
    # would SET ROLE app_user and cause every request to fail with a Postgres permission
    # error. tenant_id comes only from the signed JWT payload (never from the request body
    # or path — see EstabelecimentoUpdate), so it cannot be manipulated by the caller.
    # check_subscription (normally only reached via get_tenant_db) is applied explicitly
    # here so suspended/cancelled/expired tenants are blocked from this write too.
    return config_service.update_estabelecimento(db, payload["tenant_id"], body)
