import datetime

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.orm import Session

from src.api.dependencies import (
    get_current_user,
    get_tenant_db,
    require_feature,
    require_permission,
)
from src.core.limiter import limiter
from src.schemas.dashboard_schemas import (
    DashboardHistoricoItem,
    DashboardResponse,
    DashboardResumoAnualItem,
)
from src.services import dashboard_service

router = APIRouter(dependencies=[Depends(require_feature("dashboard")), Depends(require_permission("dashboard"))])

_REPORT_RATE_LIMIT = "60/minute"


@router.get("", response_model=DashboardResponse)
@limiter.limit(_REPORT_RATE_LIMIT)
def dashboard(
    request: Request,
    db: Session = Depends(get_tenant_db),
    _user: dict = Depends(get_current_user),
) -> DashboardResponse:
    return dashboard_service.dashboard(db)


@router.get("/historico", response_model=list[DashboardHistoricoItem])
@limiter.limit(_REPORT_RATE_LIMIT)
def historico(
    request: Request,
    inicio: datetime.date = Query(...),
    fim: datetime.date = Query(...),
    db: Session = Depends(get_tenant_db),
    _user: dict = Depends(get_current_user),
) -> list[DashboardHistoricoItem]:
    return dashboard_service.dashboard_historico(db, inicio, fim)


@router.get("/resumo-anual", response_model=list[DashboardResumoAnualItem])
@limiter.limit(_REPORT_RATE_LIMIT)
def resumo_anual(
    request: Request,
    ano: int = Query(...),
    db: Session = Depends(get_tenant_db),
    _user: dict = Depends(get_current_user),
) -> list[DashboardResumoAnualItem]:
    return dashboard_service.dashboard_resumo_anual(db, ano)
