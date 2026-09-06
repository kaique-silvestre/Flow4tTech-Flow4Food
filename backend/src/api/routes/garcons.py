
from decimal import Decimal
from typing import Optional

from fastapi import APIRouter, BackgroundTasks, Depends, Query, Request
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from src.api.dependencies import (
    get_current_user,
    get_tenant_db,
    require_feature,
    require_permission,
)
from src.core.limiter import limiter
from src.models.comandas import Comanda
from src.models.comissoes_garcom import ComissaoGarcom
from src.schemas.comissoes import ComissaoResponse, ComissaoUpdateRequest, GarcomStatsResponse
from src.schemas.garcons import (
    GarcomCreateRequest,
    GarcomPageResponse,
    GarcomResponse,
    GarcomUpdateRequest,
)
from src.services import audit_service, garcons_service

router = APIRouter(dependencies=[Depends(require_feature("cadastros")), Depends(require_permission("cadastros"))])

_COMISSAO_RATE_LIMIT = "30/minute"


@router.get("", response_model=GarcomPageResponse)
def list_garcons(
    busca: Optional[str] = Query(None),
    pagina: int = Query(1, ge=1),
    por_pagina: int = Query(500, ge=1, le=500),
    db: Session = Depends(get_tenant_db),
    _user: dict = Depends(get_current_user),
) -> GarcomPageResponse:
    return garcons_service.list_garcons(db, busca=busca, pagina=pagina, por_pagina=por_pagina)  # type: ignore[return-value]


@router.post("", response_model=GarcomResponse, status_code=201)
def create_garcom(
    body: GarcomCreateRequest,
    db: Session = Depends(get_tenant_db),
    _user: dict = Depends(get_current_user),
) -> GarcomResponse:
    return garcons_service.create_garcom(db, body)  # type: ignore[return-value]


@router.put("/{garcom_id}", response_model=GarcomResponse)
def update_garcom(
    garcom_id: int,
    body: GarcomUpdateRequest,
    db: Session = Depends(get_tenant_db),
    _user: dict = Depends(get_current_user),
) -> GarcomResponse:
    return garcons_service.update_garcom(db, garcom_id, body)  # type: ignore[return-value]


@router.patch("/{garcom_id}/toggle-ativo", response_model=GarcomResponse)
def toggle_ativo_garcom(
    garcom_id: int,
    db: Session = Depends(get_tenant_db),
    _user: dict = Depends(get_current_user),
) -> GarcomResponse:
    return garcons_service.toggle_ativo_garcom(db, garcom_id)  # type: ignore[return-value]


@router.get("/{garcom_id}/stats", response_model=GarcomStatsResponse)
def get_garcom_stats(
    garcom_id: int,
    db: Session = Depends(get_tenant_db),
    _user: dict = Depends(get_current_user),
) -> GarcomStatsResponse:
    garcons_service.get_garcom(db, garcom_id)

    total_comandas = db.execute(
        select(func.count()).select_from(Comanda).where(Comanda.garcom_id == garcom_id)
    ).scalar_one()

    comandas_fechadas = db.execute(
        select(func.count())
        .select_from(Comanda)
        .where(Comanda.garcom_id == garcom_id, Comanda.status == "fechada")
    ).scalar_one()

    comissao_pendente = db.execute(
        select(func.coalesce(func.sum(ComissaoGarcom.valor), Decimal("0")))
        .where(ComissaoGarcom.garcom_id == garcom_id, ComissaoGarcom.pago == False)  # noqa: E712
    ).scalar_one()

    comissoes_db = db.execute(
        select(ComissaoGarcom)
        .where(ComissaoGarcom.garcom_id == garcom_id)
        .order_by(ComissaoGarcom.created_at.desc())
    ).scalars().all()

    return GarcomStatsResponse(
        garcom_id=garcom_id,
        total_comandas=total_comandas,
        comandas_fechadas=comandas_fechadas,
        comissao_pendente=Decimal(str(comissao_pendente)),
        comissoes=[ComissaoResponse.model_validate(c) for c in comissoes_db],
    )


@router.patch("/comissoes/{comissao_id}", response_model=ComissaoResponse)
def update_comissao(
    comissao_id: int,
    body: ComissaoUpdateRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_tenant_db),
    payload: dict = Depends(get_current_user),
) -> ComissaoResponse:
    valor_antes, comissao = garcons_service.update_comissao(
        db,
        comissao_id,
        body.valor,
        tenant_id=payload.get("tenant_id"),
        user_id=payload.get("user_id"),
    )
    background_tasks.add_task(
        audit_service.log_background,
        "comissao.valor.alterar",
        tenant_id=payload.get("tenant_id"),
        user_id=payload.get("user_id"),
        entity="ComissaoGarcom",
        entity_id=comissao_id,
        before={"valor": str(valor_antes)},
        after={"valor": str(comissao.valor)},
        impersonated_by=payload.get("impersonated_by"),
    )
    return ComissaoResponse.model_validate(comissao)


@router.patch("/comissoes/{comissao_id}/toggle-pago", response_model=ComissaoResponse)
@limiter.limit(_COMISSAO_RATE_LIMIT)
def toggle_pago_comissao(
    request: Request,
    comissao_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_tenant_db),
    payload: dict = Depends(get_current_user),
) -> ComissaoResponse:
    pago_antes = db.get(ComissaoGarcom, comissao_id)
    estado_antes = pago_antes.pago if pago_antes is not None else None
    comissao = garcons_service.toggle_pago_comissao(
        db,
        comissao_id,
        tenant_id=payload.get("tenant_id"),
        user_id=payload.get("user_id"),
    )
    background_tasks.add_task(
        audit_service.log_background,
        "comissao.pago.alternar",
        tenant_id=payload.get("tenant_id"),
        user_id=payload.get("user_id"),
        entity="ComissaoGarcom",
        entity_id=comissao_id,
        before={"pago": estado_antes} if estado_antes is not None else None,
        after={"pago": comissao.pago},
        impersonated_by=payload.get("impersonated_by"),
    )
    return ComissaoResponse.model_validate(comissao)


@router.delete("/comissoes/{comissao_id}", status_code=204)
@limiter.limit(_COMISSAO_RATE_LIMIT)
def delete_comissao(
    request: Request,
    comissao_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_tenant_db),
    payload: dict = Depends(get_current_user),
) -> None:
    comissao_antes = db.get(ComissaoGarcom, comissao_id)
    snapshot = (
        {
            "garcom_id": comissao_antes.garcom_id,
            "comanda_id": comissao_antes.comanda_id,
            "valor": str(comissao_antes.valor),
            "pago": comissao_antes.pago,
        }
        if comissao_antes is not None
        else None
    )
    garcons_service.delete_comissao(
        db,
        comissao_id,
        tenant_id=payload.get("tenant_id"),
        user_id=payload.get("user_id"),
    )
    background_tasks.add_task(
        audit_service.log_background,
        "comissao.remover",
        tenant_id=payload.get("tenant_id"),
        user_id=payload.get("user_id"),
        entity="ComissaoGarcom",
        entity_id=comissao_id,
        before=snapshot,
        after=None,
        impersonated_by=payload.get("impersonated_by"),
    )
