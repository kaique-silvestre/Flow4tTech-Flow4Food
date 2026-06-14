from typing import Optional

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from src.api.dependencies import (
    get_current_user,
    get_tenant_db,
    require_feature,
    require_permission,
)
from src.schemas.eventos import EventoCreate, EventoPatch, EventoResponse
from src.services import eventos_service

router = APIRouter(dependencies=[Depends(require_feature("calendario")), Depends(require_permission("calendario"))])


@router.get("", response_model=list[EventoResponse])
def list_eventos(
    mes: Optional[str] = Query(None, description="Formato YYYY-MM"),
    db: Session = Depends(get_tenant_db),
    _user: dict = Depends(get_current_user),
) -> list[EventoResponse]:
    return eventos_service.list_by_month(db, mes)


@router.post("", response_model=EventoResponse, status_code=status.HTTP_201_CREATED)
def create_evento(
    data: EventoCreate,
    db: Session = Depends(get_tenant_db),
    user: dict = Depends(get_current_user),
) -> EventoResponse:
    criado_por = user.get("user_id")
    return eventos_service.criar_evento(db, data, criado_por)


@router.patch("/{evento_id}", response_model=EventoResponse)
def patch_evento(
    evento_id: int,
    data: EventoPatch,
    db: Session = Depends(get_tenant_db),
    _user: dict = Depends(get_current_user),
) -> EventoResponse:
    return eventos_service.patch_evento(db, evento_id, data)


@router.delete("/{evento_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_evento(
    evento_id: int,
    db: Session = Depends(get_tenant_db),
    _user: dict = Depends(get_current_user),
) -> None:
    eventos_service.delete_evento(db, evento_id)
