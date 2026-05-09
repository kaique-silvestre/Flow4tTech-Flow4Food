import datetime

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from src.api.dependencies import get_current_user, get_db
from src.schemas.dashboard_schemas import (
    DashboardHistoricoItem,
    DashboardResponse,
    DashboardResumoAnualItem,
)
from src.services import dashboard_service

router = APIRouter()


@router.get("", response_model=DashboardResponse)
def dashboard(
    db: Session = Depends(get_db),
    _user: dict = Depends(get_current_user),
) -> DashboardResponse:
    return dashboard_service.dashboard(db)


@router.get("/historico", response_model=list[DashboardHistoricoItem])
def historico(
    inicio: datetime.date = Query(...),
    fim: datetime.date = Query(...),
    db: Session = Depends(get_db),
    _user: dict = Depends(get_current_user),
) -> list[DashboardHistoricoItem]:
    return dashboard_service.dashboard_historico(db, inicio, fim)


@router.get("/resumo-anual", response_model=list[DashboardResumoAnualItem])
def resumo_anual(
    ano: int = Query(...),
    db: Session = Depends(get_db),
    _user: dict = Depends(get_current_user),
) -> list[DashboardResumoAnualItem]:
    return dashboard_service.dashboard_resumo_anual(db, ano)
