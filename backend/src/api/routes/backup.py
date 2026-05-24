from fastapi import APIRouter, Depends
from fastapi.responses import Response
from sqlalchemy.orm import Session

from src.api.dependencies import get_current_user, get_db, require_permission
from src.core.errors import AppError, ErrorCode
from src.services import backup_service

router = APIRouter(dependencies=[Depends(require_permission("configuracoes"))])


@router.get("")
def backup(
    formato: str = "json",
    db: Session = Depends(get_db),
    _user: dict = Depends(get_current_user),
) -> Response:
    if formato == "json":
        data = backup_service.backup_json(db)
        return Response(
            content=data,
            media_type="application/json",
            headers={"Content-Disposition": 'attachment; filename="backup.json"'},
        )
    if formato == "xlsx":
        data = backup_service.backup_xlsx(db)
        return Response(
            content=data,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": 'attachment; filename="backup.xlsx"'},
        )
    raise AppError(
        code=ErrorCode.VALIDATION_ERROR,
        message="formato deve ser 'json' ou 'xlsx'",
        http_status=422,
    )
