"""Helpers pequenos compartilhados entre múltiplos services.

Este módulo reúne funções utilitárias duplicadas entre services de domínios
diferentes (ex.: resolução de nome de fornecedor, parsing de mês). Não é um
"catch-all" — só deve crescer quando uma lógica idêntica aparecer em mais de
um service.
"""

import datetime
from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.core.errors import AppError, ErrorCode
from src.models.fornecedores import Fornecedor


def get_fornecedor_nome(db: Session, fornecedor_id: Optional[int]) -> Optional[str]:  # noqa: UP045
    if fornecedor_id is None:
        return None
    f = db.execute(select(Fornecedor).where(Fornecedor.id == fornecedor_id)).scalar_one_or_none()
    return f.nome if f else None


def parse_mes_ano(mes: Optional[str]) -> tuple[int, int]:  # noqa: UP045
    """Resolve uma string `YYYY-MM` para (ano, mês); usa o mês atual quando `mes` é vazio."""
    if mes:
        try:
            dt = datetime.datetime.strptime(mes, "%Y-%m")
        except ValueError as exc:
            raise AppError(code=ErrorCode.VALIDATION_ERROR, message="Formato de mês inválido. Use YYYY-MM.", http_status=400) from exc
        return dt.year, dt.month
    now = datetime.datetime.now()
    return now.year, now.month
