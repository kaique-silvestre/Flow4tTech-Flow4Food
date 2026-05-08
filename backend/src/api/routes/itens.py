from fastapi import APIRouter
from fastapi.responses import JSONResponse

router = APIRouter()


def _gone() -> JSONResponse:
    return JSONResponse(
        status_code=404,
        content={"error": {"code": "NOT_FOUND", "message": "Endpoint /api/itens removido. Use /api/insumos ou /api/produtos.", "field": None}},
    )


@router.get("/top")
def top_itens_deprecated() -> JSONResponse:
    return _gone()


@router.get("/simples")
def list_simples_deprecated() -> JSONResponse:
    return _gone()


@router.get("")
def list_itens_deprecated() -> JSONResponse:
    return _gone()


@router.get("/{item_id}")
def get_item_deprecated(item_id: int) -> JSONResponse:
    return _gone()


@router.post("")
def create_item_deprecated() -> JSONResponse:
    return _gone()


@router.put("/{item_id}")
def update_item_deprecated(item_id: int) -> JSONResponse:
    return _gone()


@router.delete("/{item_id}")
def delete_item_deprecated(item_id: int) -> JSONResponse:
    return _gone()
