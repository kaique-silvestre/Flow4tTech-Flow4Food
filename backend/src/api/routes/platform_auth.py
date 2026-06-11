from fastapi import APIRouter, Depends, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from src.api.dependencies import require_platform_admin
from src.core.database import get_platform_db
from src.services import platform_auth_service


class PlatformLoginRequest(BaseModel):
    email: str
    password: str


class PlatformLoginResponse(BaseModel):
    access_token: str


# Public router — login endpoint has no auth dependency
_public_router = APIRouter()

# Protected router — all routes require platform admin token
router = APIRouter(dependencies=[Depends(require_platform_admin)])


@_public_router.post(
    "/auth/login",
    response_model=PlatformLoginResponse,
    status_code=status.HTTP_200_OK,
    tags=["platform"],
)
def platform_login(
    body: PlatformLoginRequest,
    db: Session = Depends(get_platform_db),
) -> PlatformLoginResponse:
    token = platform_auth_service.login(db, body.email, body.password)
    return PlatformLoginResponse(access_token=token)
