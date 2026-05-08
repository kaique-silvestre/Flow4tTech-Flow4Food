from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from src.api.dependencies import get_current_user, get_db
from src.schemas.dashboard_schemas import DashboardResponse
from src.services import dashboard_service

router = APIRouter()


@router.get("", response_model=DashboardResponse)
def dashboard(
    db: Session = Depends(get_db),
    _user: dict = Depends(get_current_user),
) -> DashboardResponse:
    return dashboard_service.dashboard(db)
