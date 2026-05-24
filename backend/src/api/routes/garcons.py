
from decimal import Decimal
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from src.api.dependencies import get_current_user, get_db, require_permission
from src.models.comandas import Comanda
from src.models.comissoes_garcom import ComissaoGarcom
from src.schemas.comissoes import ComissaoResponse, ComissaoUpdateRequest, GarcomStatsResponse
from src.schemas.garcons import (
    GarcomCreateRequest,
    GarcomPageResponse,
    GarcomResponse,
    GarcomUpdateRequest,
)
from src.services import garcons_service

router = APIRouter(dependencies=[Depends(require_permission("cadastros"))])


@router.get("", response_model=GarcomPageResponse)
def list_garcons(
    busca: Optional[str] = Query(None),
    pagina: int = Query(1, ge=1),
    por_pagina: int = Query(500, ge=1, le=500),
    db: Session = Depends(get_db),
    _user: dict = Depends(get_current_user),
) -> GarcomPageResponse:
    return garcons_service.list_garcons(db, busca=busca, pagina=pagina, por_pagina=por_pagina)  # type: ignore[return-value]


@router.post("", response_model=GarcomResponse, status_code=201)
def create_garcom(
    body: GarcomCreateRequest,
    db: Session = Depends(get_db),
    _user: dict = Depends(get_current_user),
) -> GarcomResponse:
    return garcons_service.create_garcom(db, body)  # type: ignore[return-value]


@router.put("/{garcom_id}", response_model=GarcomResponse)
def update_garcom(
    garcom_id: int,
    body: GarcomUpdateRequest,
    db: Session = Depends(get_db),
    _user: dict = Depends(get_current_user),
) -> GarcomResponse:
    return garcons_service.update_garcom(db, garcom_id, body)  # type: ignore[return-value]


@router.patch("/{garcom_id}/toggle-ativo", response_model=GarcomResponse)
def toggle_ativo_garcom(
    garcom_id: int,
    db: Session = Depends(get_db),
    _user: dict = Depends(get_current_user),
) -> GarcomResponse:
    return garcons_service.toggle_ativo_garcom(db, garcom_id)  # type: ignore[return-value]


@router.get("/{garcom_id}/stats", response_model=GarcomStatsResponse)
def get_garcom_stats(
    garcom_id: int,
    db: Session = Depends(get_db),
    _user: dict = Depends(get_current_user),
) -> GarcomStatsResponse:
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
    db: Session = Depends(get_db),
    _user: dict = Depends(get_current_user),
) -> ComissaoResponse:
    comissao = db.get(ComissaoGarcom, comissao_id)
    if comissao is None:
        raise HTTPException(status_code=404, detail="Comissão não encontrada")
    comissao.valor = body.valor
    db.commit()
    db.refresh(comissao)
    return ComissaoResponse.model_validate(comissao)


@router.patch("/comissoes/{comissao_id}/toggle-pago", response_model=ComissaoResponse)
def toggle_pago_comissao(
    comissao_id: int,
    db: Session = Depends(get_db),
    _user: dict = Depends(get_current_user),
) -> ComissaoResponse:
    comissao = db.get(ComissaoGarcom, comissao_id)
    if comissao is None:
        raise HTTPException(status_code=404, detail="Comissão não encontrada")
    comissao.pago = not comissao.pago
    db.commit()
    db.refresh(comissao)
    return ComissaoResponse.model_validate(comissao)


@router.delete("/comissoes/{comissao_id}", status_code=204)
def delete_comissao(
    comissao_id: int,
    db: Session = Depends(get_db),
    _user: dict = Depends(get_current_user),
) -> None:
    comissao = db.get(ComissaoGarcom, comissao_id)
    if comissao is None:
        raise HTTPException(status_code=404, detail="Comissão não encontrada")
    db.delete(comissao)
    db.commit()
