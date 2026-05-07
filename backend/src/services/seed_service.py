from sqlalchemy import select
from sqlalchemy.orm import Session

from src.models.categorias import Categoria
from src.models.metodos_pagamento import MetodoPagamento

_CATEGORIAS_SEED = ["Geral"]
_METODOS_SEED = ["PIX", "Crédito", "Débito", "Dinheiro"]


def run_seed(db: Session) -> None:
    for nome in _CATEGORIAS_SEED:
        cat = db.execute(select(Categoria).where(Categoria.nome == nome)).scalar_one_or_none()
        if cat is None:
            db.add(Categoria(nome=nome))

    for nome in _METODOS_SEED:
        metodo = db.execute(select(MetodoPagamento).where(MetodoPagamento.nome == nome)).scalar_one_or_none()
        if metodo is None:
            db.add(MetodoPagamento(nome=nome, ativo=True))

    db.commit()
