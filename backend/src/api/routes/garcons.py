
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from src.api.dependencies import get_current_user, get_db
from src.schemas.garcons import GarcomCreateRequest, GarcomResponse, GarcomUpdateRequest
from src.services import garcons_service

router = APIRouter()


@router.get("", response_model=list[GarcomResponse])
def list_garcons(
    db: Session = Depends(get_db),
    _user: dict = Depends(get_current_user),
) -> list[GarcomResponse]:
    return garcons_service.list_garcons(db)  # type: ignore[return-value]


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
