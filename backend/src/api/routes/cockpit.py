from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from src.api.dependencies import get_current_user, get_tenant_db, require_permission
from src.schemas.cockpit import CockpitItem
from src.services import cockpit_service

router = APIRouter(dependencies=[Depends(require_permission("calendario"))])


@router.get("", response_model=list[CockpitItem])
def get_consolidado(
    mes: Optional[str] = Query(None, description="Formato YYYY-MM"),
    db: Session = Depends(get_tenant_db),
    user: dict = Depends(get_current_user),
) -> list[CockpitItem]:
    permissions: list[str] = user.get("permissions", [])
    return cockpit_service.list_consolidado(db, mes, permissions)
