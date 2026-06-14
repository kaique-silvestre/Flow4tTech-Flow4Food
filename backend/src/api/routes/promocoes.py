from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from src.api.dependencies import (
    get_current_user,
    get_tenant_db,
    require_feature,
    require_permission,
)
from src.schemas.promocoes import PromoçaoCreate, PromoçaoResponse, PromoçaoUpdate
from src.services import promocoes_service

router = APIRouter(dependencies=[Depends(require_feature("cadastros")), Depends(require_permission("cadastros"))])


@router.get("/mes", response_model=list[PromoçaoResponse])
def list_por_mes(
    mes: Optional[str] = Query(None),
    db: Session = Depends(get_tenant_db),
    _user: dict = Depends(get_current_user),
) -> list[PromoçaoResponse]:
    return promocoes_service.list_by_month(db, mes)  # type: ignore[return-value]


@router.get("", response_model=list[PromoçaoResponse])
def list_promocoes(
    status: Optional[str] = Query("todas"),
    db: Session = Depends(get_tenant_db),
    _user: dict = Depends(get_current_user),
) -> list[PromoçaoResponse]:
    return promocoes_service.list_promocoes(db, status)  # type: ignore[return-value]


@router.post("", response_model=PromoçaoResponse, status_code=201)
def create_promocao(
    body: PromoçaoCreate,
    db: Session = Depends(get_tenant_db),
    user: dict = Depends(get_current_user),
) -> PromoçaoResponse:
    criado_por = user.get("user_id")
    return promocoes_service.criar_promocao(db, body, criado_por)  # type: ignore[return-value]


@router.patch("/{promocao_id}", response_model=PromoçaoResponse)
def update_promocao(
    promocao_id: int,
    body: PromoçaoUpdate,
    db: Session = Depends(get_tenant_db),
    _user: dict = Depends(get_current_user),
) -> PromoçaoResponse:
    return promocoes_service.update_promocao(db, promocao_id, body)  # type: ignore[return-value]


@router.delete("/{promocao_id}", status_code=204)
def delete_promocao(
    promocao_id: int,
    db: Session = Depends(get_tenant_db),
    _user: dict = Depends(get_current_user),
) -> None:
    promocoes_service.delete_promocao(db, promocao_id)
