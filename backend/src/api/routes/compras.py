from typing import Optional

from fastapi import APIRouter, Depends, File, Query, UploadFile, status
from sqlalchemy.orm import Session

from src.api.dependencies import (
    get_current_user,
    get_tenant_db,
    require_feature,
    require_permission,
)
from src.schemas.compras import (
    CompraCreateRequest,
    CompraPatchRequest,
    CompraResponse,
    ComprasPageResponse,
)
from src.schemas.nfe import NFeImportResponse
from src.services import compras_service, nfe_match_service, nfe_parser

router = APIRouter(dependencies=[Depends(require_feature("compras")), Depends(require_permission("compras"))])


@router.post("/importar-nfe", response_model=NFeImportResponse)
def importar_nfe(
    file: UploadFile = File(...),
    db: Session = Depends(get_tenant_db),
    _user: dict = Depends(get_current_user),
) -> NFeImportResponse:
    xml_bytes = file.file.read()
    data = nfe_parser.parse_nfe(xml_bytes)
    return nfe_match_service.match_nfe(db, data)


@router.post("", response_model=CompraResponse, status_code=status.HTTP_201_CREATED)
def create_compra(
    data: CompraCreateRequest,
    db: Session = Depends(get_tenant_db),
    _user: dict = Depends(get_current_user),
) -> CompraResponse:
    return compras_service.criar_compra(db, data)


@router.get("", response_model=ComprasPageResponse)
def list_compras(
    data_inicio: Optional[str] = Query(None),
    data_fim: Optional[str] = Query(None),
    fornecedor_id: Optional[int] = Query(None),
    status: Optional[str] = Query(None),
    tipo_compra: Optional[str] = Query(None),
    pagina: int = Query(1, ge=1),
    por_pagina: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_tenant_db),
    _user: dict = Depends(get_current_user),
) -> ComprasPageResponse:
    return compras_service.list_compras(  # type: ignore[return-value]
        db, data_inicio, data_fim, fornecedor_id, status, tipo_compra, pagina, por_pagina
    )


@router.get("/{compra_id}", response_model=CompraResponse)
def get_compra(
    compra_id: int,
    db: Session = Depends(get_tenant_db),
    _user: dict = Depends(get_current_user),
) -> CompraResponse:
    return compras_service.get_compra(db, compra_id)


@router.post("/{compra_id}/confirmar-recebimento", response_model=CompraResponse)
def confirmar_recebimento(
    compra_id: int,
    db: Session = Depends(get_tenant_db),
    _user: dict = Depends(get_current_user),
) -> CompraResponse:
    return compras_service.confirmar_recebimento(db, compra_id)


@router.post("/{compra_id}/cancelar", response_model=CompraResponse)
def cancelar_compra(
    compra_id: int,
    db: Session = Depends(get_tenant_db),
    _user: dict = Depends(get_current_user),
) -> CompraResponse:
    return compras_service.cancelar_compra(db, compra_id)


@router.patch("/{compra_id}", response_model=CompraResponse)
def patch_compra(
    compra_id: int,
    data: CompraPatchRequest,
    db: Session = Depends(get_tenant_db),
    _user: dict = Depends(get_current_user),
) -> CompraResponse:
    return compras_service.patch_compra(db, compra_id, data)
