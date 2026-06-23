import os

os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
os.environ.setdefault("JWT_SECRET", "test-secret-only-for-tests")
os.environ.setdefault("ENV", "test")

from datetime import date
from decimal import Decimal

import sqlalchemy as sa
import pytest
from sqlalchemy import StaticPool, create_engine
from sqlalchemy.orm import sessionmaker

from src.core.database import Base
from src.models.fornecedores import Fornecedor
from src.models.insumos import Insumo
from src.services.nfe_match_service import match_nfe
from src.services.nfe_parser import NFeData, NFeItem

_SQLITE_URL = "sqlite:///:memory:"
_engine = create_engine(
    _SQLITE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
_Session = sessionmaker(bind=_engine, autoflush=False, autocommit=False)

# Patch tenant_id server_default for SQLite
for _table in Base.metadata.tables.values():
    for _col in _table.columns:
        if _col.name == "tenant_id" and _col.server_default is not None:
            _col.server_default = sa.schema.DefaultClause(sa.text("1"))


@pytest.fixture(autouse=True)
def _setup_db():
    Base.metadata.create_all(_engine)
    yield
    Base.metadata.drop_all(_engine)


@pytest.fixture
def db():
    session = _Session()
    try:
        yield session
    finally:
        session.close()


def _nfe_data(cnpj="12345678000195", itens=None) -> NFeData:
    return NFeData(
        numero_nota="1",
        data_emissao=date(2024, 3, 15),
        cnpj_emitente=cnpj,
        nome_emitente="Fornecedor Teste",
        itens=itens or [],
    )


def _nfe_item(nome="Arroz", ean=None) -> NFeItem:
    return NFeItem(nome=nome, ean=ean, quantidade=Decimal("10"), unidade_xml="kg", custo_unitario=Decimal("5"), custo_total=Decimal("50"))


def test_cnpj_match_returns_fornecedor_id(db):
    f = Fornecedor(nome="Dist ABC", cnpj="12345678000195")
    db.add(f)
    db.commit()
    db.refresh(f)

    result = match_nfe(db, _nfe_data(cnpj="12345678000195"))
    assert result.fornecedor_id == f.id


def test_cnpj_no_match_returns_none(db):
    result = match_nfe(db, _nfe_data(cnpj="00000000000000"))
    assert result.fornecedor_id is None


def test_ean_match_returns_insumo(db):
    ins = Insumo(nome="Feijão Preto", unidade_base="kg", ean="7891234567890", estoque_atual=Decimal("0"))
    db.add(ins)
    db.commit()
    db.refresh(ins)

    item = _nfe_item(nome="Feijao Preto", ean="7891234567890")
    result = match_nfe(db, _nfe_data(itens=[item]))
    assert result.itens[0].insumo_id == ins.id
    assert result.itens[0].insumo_nome == "Feijão Preto"


def test_name_case_insensitive_accent_match(db):
    ins = Insumo(nome="Açúcar Cristal", unidade_base="kg", estoque_atual=Decimal("0"))
    db.add(ins)
    db.commit()
    db.refresh(ins)

    item = _nfe_item(nome="ACUCAR CRISTAL", ean=None)
    result = match_nfe(db, _nfe_data(itens=[item]))
    assert result.itens[0].insumo_id == ins.id


def test_no_match_returns_none(db):
    item = _nfe_item(nome="Produto Inexistente", ean="9999999999999")
    result = match_nfe(db, _nfe_data(itens=[item]))
    assert result.itens[0].insumo_id is None
    assert result.itens[0].insumo_nome is None


def test_response_fields(db):
    result = match_nfe(db, _nfe_data(cnpj="11111111000111", itens=[]))
    assert result.numero_nota == "1"
    assert result.data_compra == date(2024, 3, 15)
    assert result.cnpj_xml == "11111111000111"
    assert result.fornecedor_nome_xml == "Fornecedor Teste"
    assert result.itens == []
