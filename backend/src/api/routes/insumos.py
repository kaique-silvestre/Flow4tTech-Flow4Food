from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from src.api.dependencies import get_current_user, get_tenant_db, require_permission
from src.schemas.insumos import (
    InsumoCreateRequest,
    InsumoPageResponse,
    InsumoResponse,
    InsumoUpdateRequest,
)
from src.services import insumos_service

router = APIRouter(dependencies=[Depends(require_permission("estoque"))])


@router.get("", response_model=InsumoPageResponse)
def list_insumos(
    categoria_id: Optional[int] = Query(None),
    busca: Optional[str] = Query(None),
    incluir_inativos: bool = Query(False),
    pagina: int = Query(1, ge=1),
    por_pagina: int = Query(500, ge=1, le=500),
    db: Session = Depends(get_tenant_db),
    _user: dict = Depends(get_current_user),
) -> InsumoPageResponse:
    if incluir_inativos:
        return insumos_service.list_all_insumos(db, busca, pagina, por_pagina)  # type: ignore[return-value]
    return insumos_service.list_insumos(db, categoria_id, busca, pagina, por_pagina)  # type: ignore[return-value]


@router.get("/{insumo_id}", response_model=InsumoResponse)
def get_insumo(
    insumo_id: int,
    db: Session = Depends(get_tenant_db),
    _user: dict = Depends(get_current_user),
) -> InsumoResponse:
    return insumos_service.get_insumo(db, insumo_id)  # type: ignore[return-value]


@router.post("", response_model=InsumoResponse, status_code=201)
def create_insumo(
    body: InsumoCreateRequest,
    db: Session = Depends(get_tenant_db),
    _user: dict = Depends(get_current_user),
) -> InsumoResponse:
    return insumos_service.create_insumo(db, body)  # type: ignore[return-value]


@router.put("/{insumo_id}", response_model=InsumoResponse)
def update_insumo(
    insumo_id: int,
    body: InsumoUpdateRequest,
    db: Session = Depends(get_tenant_db),
    _user: dict = Depends(get_current_user),
) -> InsumoResponse:
    return insumos_service.update_insumo(db, insumo_id, body)  # type: ignore[return-value]


@router.patch("/{insumo_id}/toggle-ativo", response_model=InsumoResponse)
def toggle_ativo(
    insumo_id: int,
    db: Session = Depends(get_tenant_db),
    _user: dict = Depends(get_current_user),
) -> InsumoResponse:
    return insumos_service.toggle_insumo_ativo(db, insumo_id)  # type: ignore[return-value]


@router.delete("/{insumo_id}", status_code=204)
def delete_insumo(
    insumo_id: int,
    db: Session = Depends(get_tenant_db),
    _user: dict = Depends(get_current_user),
) -> None:
    insumos_service.delete_insumo(db, insumo_id)
