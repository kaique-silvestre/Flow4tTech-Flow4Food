import datetime
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from src.api.dependencies import get_current_user, get_tenant_db, require_permission
from src.schemas.consumo_interno import (
    ItemConsumoInternoResponse,
    LancarConsumoBatchRequest,
    LancarConsumoBatchResponse,
    LancarConsumoRequest,
    ResumoConsumidorResponse,
)
from src.services import consumo_interno_service

router = APIRouter(dependencies=[Depends(require_permission("consumo_interno"))])


@router.post("", response_model=ItemConsumoInternoResponse)
def lancar_item(
    data: LancarConsumoRequest,
    db: Session = Depends(get_tenant_db),
    _user: dict = Depends(get_current_user),
) -> ItemConsumoInternoResponse:
    return consumo_interno_service.lancar_item(db, data)


@router.post("/batch", response_model=LancarConsumoBatchResponse)
def lancar_batch(
    data: LancarConsumoBatchRequest,
    db: Session = Depends(get_tenant_db),
    _user: dict = Depends(get_current_user),
) -> LancarConsumoBatchResponse:
    itens = consumo_interno_service.lancar_batch(db, data)
    return LancarConsumoBatchResponse(itens=itens)


@router.get("", response_model=list[ItemConsumoInternoResponse])
def listar_items(
    consumidor_id: Optional[int] = Query(None),
    mes: Optional[int] = Query(None, ge=1, le=12),
    ano: Optional[int] = Query(None, ge=2020),
    data_inicio: Optional[datetime.date] = Query(None),
    data_fim: Optional[datetime.date] = Query(None),
    db: Session = Depends(get_tenant_db),
    _user: dict = Depends(get_current_user),
) -> list[ItemConsumoInternoResponse]:
    return consumo_interno_service.listar_items(db, consumidor_id, mes, ano, data_inicio, data_fim)


@router.get("/resumo", response_model=list[ResumoConsumidorResponse])
def resumo_mensal(
    mes: Optional[int] = Query(None, ge=1, le=12),
    ano: Optional[int] = Query(None, ge=2020),
    data_inicio: Optional[datetime.date] = Query(None),
    data_fim: Optional[datetime.date] = Query(None),
    db: Session = Depends(get_tenant_db),
    _user: dict = Depends(get_current_user),
) -> list[ResumoConsumidorResponse]:
    return consumo_interno_service.resumo_mensal(db, mes, ano, data_inicio, data_fim)


@router.delete("/{item_id}")
def estornar_item(
    item_id: int,
    db: Session = Depends(get_tenant_db),
    _user: dict = Depends(get_current_user),
) -> dict:
    return consumo_interno_service.estornar_item(db, item_id)
