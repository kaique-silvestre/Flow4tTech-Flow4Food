import sys; sys.path.insert(0, ".")
from src.core.database import engine
from sqlalchemy import text

with engine.connect() as conn:
    rows = conn.execute(text("SELECT id, nome, unidade_base, categoria_id, ativo, estoque_atual FROM insumos ORDER BY id")).fetchall()
    print(f"Total: {len(rows)} insumos\n")
    for r in rows:
        print(f"  id={r[0]} nome={r[1]!r} unidade={r[2]} cat={r[3]} ativo={r[4]} estoque={r[5]}")
