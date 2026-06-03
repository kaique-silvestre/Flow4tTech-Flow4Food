import os

os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
os.environ.setdefault("JWT_SECRET", "test-secret-only-for-tests")
os.environ.setdefault("ENV", "test")

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import StaticPool, create_engine
from sqlalchemy.orm import sessionmaker

from src.api.dependencies import get_current_user, get_db
from src.core.database import Base
from src.main import app

_SQLITE_URL = "sqlite:///:memory:"
_engine = create_engine(
    _SQLITE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
_TestingSession = sessionmaker(bind=_engine, autoflush=False, autocommit=False)


def _fake_user() -> dict:
    return {"sub": "1", "user_id": 1, "tenant_id": 1, "permissions": ["cadastros", "comandas", "compras", "configuracoes", "dashboard", "estoque", "gestao_usuarios", "relatorios"]}


@pytest.fixture(autouse=True)
def _setup_db():
    Base.metadata.create_all(_engine)
    yield
    Base.metadata.drop_all(_engine)


@pytest.fixture
def c():
    def override_get_db():
        db = _TestingSession()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = _fake_user
    with TestClient(app) as client:
        yield client
    app.dependency_overrides.clear()


def _criar_insumo(c, nome="Insumo A", unidade="un"):
    resp = c.post("/api/insumos", json={"nome": nome, "unidade_base": unidade})
    assert resp.status_code == 201
    return resp.json()


def _criar_categoria(c, nome="Cat"):
    resp = c.post("/api/categorias", json={"nome": nome})
    assert resp.status_code == 201
    return resp.json()


# ---------------------------------------------------------------------------
# GET /api/produtos
# ---------------------------------------------------------------------------


def test_list_produtos_vazio(c):
    resp = c.get("/api/produtos")
    assert resp.status_code == 200
    assert resp.json()["itens"] == []


# ---------------------------------------------------------------------------
# POST /api/produtos — sem ficha
# ---------------------------------------------------------------------------


def test_create_produto_sem_ficha(c):
    resp = c.post("/api/produtos", json={"nome": "Hamburguer", "preco_venda": "15.00"})
    assert resp.status_code == 201
    data = resp.json()
    assert data["nome"] == "Hamburguer"
    assert data["ativo"] is True
    assert data["ficha_tecnica"] is None


# ---------------------------------------------------------------------------
# POST /api/produtos — com ficha
# ---------------------------------------------------------------------------


def test_create_produto_com_ficha(c):
    insumo = _criar_insumo(c, "Carne", "g")  # noqa: valid enum value
    resp = c.post(
        "/api/produtos",
        json={
            "nome": "Hamburguer",
            "preco_venda": "20.00",
            "ficha_tecnica": [{"insumo_id": insumo["id"], "quantidade": "0.200"}],
        },
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["ficha_tecnica"] is not None
    assert len(data["ficha_tecnica"]) == 1
    assert data["ficha_tecnica"][0]["insumo_nome"] == "Carne"
    assert data["ficha_tecnica"][0]["unidade_base"] == "g"


# ---------------------------------------------------------------------------
# PUT /api/produtos/:id — editar nome, categoria, preço, ficha
# ---------------------------------------------------------------------------


def test_update_produto(c):
    cat = _criar_categoria(c)
    insumo = _criar_insumo(c)
    p = c.post("/api/produtos", json={"nome": "Original"}).json()

    resp = c.put(
        f"/api/produtos/{p['id']}",
        json={
            "nome": "Editado",
            "categoria_id": cat["id"],
            "preco_venda": "25.00",
            "ficha_tecnica": [{"insumo_id": insumo["id"], "quantidade": "1"}],
        },
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["nome"] == "Editado"
    assert data["categoria_id"] == cat["id"]
    assert float(data["preco_venda"]) == 25.0
    assert len(data["ficha_tecnica"]) == 1


# ---------------------------------------------------------------------------
# DELETE /api/produtos/:id — sem histórico = OK
# ---------------------------------------------------------------------------


def test_delete_produto_sem_historico(c):
    p = c.post("/api/produtos", json={"nome": "Deletável"}).json()
    resp = c.delete(f"/api/produtos/{p['id']}")
    assert resp.status_code == 204
    assert c.get(f"/api/produtos/{p['id']}").status_code == 404


# ---------------------------------------------------------------------------
# DELETE /api/produtos/:id — com histórico = 422
# ---------------------------------------------------------------------------


def test_delete_produto_com_historico_retorna_422(c):
    from decimal import Decimal as D

    from src.models.comandas import Comanda
    from src.models.itens_comanda import ItemComanda

    p = c.post("/api/produtos", json={"nome": "Produto Com Historia"}).json()

    # Inserir ItemComanda direto para simular histórico
    db = _TestingSession()
    try:
        comanda = Comanda(
            identificacao="M01",
            tipo_identificacao="mesa",
            garcom_id=1,
            status="aberta",
            total=D("0"),
            version=1,
        )
        db.add(comanda)
        db.flush()
        db.add(ItemComanda(
            comanda_id=comanda.id,
            produto_id=p["id"],
            quantidade=D("1"),
            preco_unitario=D("10"),
            cancelado=False,
            cortesia=False,
        ))
        db.commit()
    finally:
        db.close()

    resp = c.delete(f"/api/produtos/{p['id']}")
    assert resp.status_code == 422


# ---------------------------------------------------------------------------
# PATCH /api/produtos/:id/desativar — soft delete
# ---------------------------------------------------------------------------


def test_desativar_produto(c):
    p = c.post("/api/produtos", json={"nome": "Ativo"}).json()
    resp = c.patch(f"/api/produtos/{p['id']}/desativar")
    assert resp.status_code == 200
    assert resp.json()["ativo"] is False

    # Não aparece em GET /api/produtos?ativo=true (filtra apenas ativos)
    lista = c.get("/api/produtos", params={"ativo": "true"}).json()["itens"]
    assert not any(x["id"] == p["id"] for x in lista)


# ---------------------------------------------------------------------------
# Produto inativo não aparece no seletor de comandas
# ---------------------------------------------------------------------------


def test_produto_inativo_nao_aparece_em_list(c):
    p1 = c.post("/api/produtos", json={"nome": "Ativo"}).json()
    p2 = c.post("/api/produtos", json={"nome": "Inativo"}).json()
    c.patch(f"/api/produtos/{p2['id']}/desativar")

    # sem filtro → retorna todos (ativo e inativo)
    todos = c.get("/api/produtos").json()["itens"]
    ids_todos = [x["id"] for x in todos]
    assert p1["id"] in ids_todos
    assert p2["id"] in ids_todos

    # ativo=true → apenas ativos
    lista = c.get("/api/produtos", params={"ativo": "true"}).json()["itens"]
    ids = [x["id"] for x in lista]
    assert p1["id"] in ids
    assert p2["id"] not in ids


# ---------------------------------------------------------------------------
# FichaTecnicaItemResponse inclui custo_medio_insumo
# ---------------------------------------------------------------------------


def test_ficha_inclui_custo_medio_insumo(c):
    insumo = _criar_insumo(c, "Queijo", "g")  # noqa: valid enum value
    p = c.post(
        "/api/produtos",
        json={
            "nome": "X-Queijo",
            "ficha_tecnica": [{"insumo_id": insumo["id"], "quantidade": "0.100"}],
        },
    ).json()
    ficha = p["ficha_tecnica"][0]
    assert "custo_medio_insumo" in ficha
    # insumo sem custo = None
    assert ficha["custo_medio_insumo"] is None
