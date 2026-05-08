import io
import json
from datetime import date, datetime
from decimal import Decimal
from typing import Any

import openpyxl
from sqlalchemy import Table, select
from sqlalchemy.orm import Session

from src.core.database import Base
from src.models.comandas import Comanda
from src.models.insumos import Insumo
from src.models.movimentos_estoque import MovimentoEstoque


def _serialize(val: Any) -> Any:
    if isinstance(val, (datetime, date)):
        return val.isoformat()
    if isinstance(val, Decimal):
        return str(val)
    return val


def backup_json(db: Session) -> bytes:
    result: dict[str, list[dict[str, Any]]] = {}
    table: Table
    for table in Base.metadata.sorted_tables:
        rows = db.execute(select(table)).mappings().all()
        result[table.name] = [{k: _serialize(v) for k, v in row.items()} for row in rows]
    return json.dumps(result, ensure_ascii=False, indent=2).encode("utf-8")


def _table_rows(db: Session, cls: type) -> tuple[list[str], list[list[Any]]]:
    from sqlalchemy import inspect as sa_inspect
    from sqlalchemy.orm.mapper import Mapper

    insp: Mapper = sa_inspect(cls)  # type: ignore[assignment]
    cols: list[str] = [c.key for c in insp.columns]
    instances: list[Any] = list(db.execute(select(cls)).scalars().all())
    data: list[list[Any]] = [[_serialize(getattr(r, c)) for c in cols] for r in instances]
    return cols, data


def backup_xlsx(db: Session) -> bytes:
    wb = openpyxl.Workbook()
    wb.remove(wb.active)

    for sheet_name, cls in [
        ("comandas", Comanda),
        ("insumos", Insumo),
        ("movimento_estoque", MovimentoEstoque),
    ]:
        cols, data = _table_rows(db, cls)
        ws = wb.create_sheet(title=sheet_name)
        ws.append(cols)
        for row in data:
            ws.append(row)

    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()
