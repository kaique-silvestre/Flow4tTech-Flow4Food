import os
from decimal import Decimal

os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
os.environ.setdefault("JWT_SECRET", "test-secret-only-for-tests")
os.environ.setdefault("ENV", "test")

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import StaticPool, create_engine, update
from sqlalchemy.orm import Session, sessionmaker

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
    return {
        "sub": "1",
        "user_id": 1,
        "tenant_id": 1,
        "permissions": [
            "cadastros", "comandas", "compras", "configuracoes",
            "dashboard", "estoque", "gestao_usuarios", "relatorios",
            "consumo_interno",
        ],
    }


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


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _criar_consumidor(nome: str = "Funcionario Teste") -> int:
    """Insere Profile + SystemUser diretamente no banco e retorna o ID do user."""
    import datetime as _dt
    from src.models.profiles import Profile
    from src.models.system_users import SystemUser

    now = _dt.datetime.utcnow()
    db: Session = _TestingSession()
    try:
        profile = Profile(
            name="Perfil Teste",
            tenant_id=1,
            created_at=now,
            updated_at=now,
        )
        db.add(profile)
        db.flush()

        user = SystemUser(
            tenant_id=1,
            profile_id=profile.id,
            name=nome,
            username=nome.lower().replace(" ", "_"),
            password_hash="$2b$12$fakehashfortesting",
            created_at=now,
            updated_at=now,
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        return user.id
    finally:
        db.close()


def _criar_produto(c, nome: str = "Produto Teste", preco: str = "30.00") -> dict:
    resp = c.post("/api/produtos", json={"nome": nome, "preco_venda": preco})
    assert resp.status_code == 201, resp.text
    return resp.json()


def _criar_insumo(c, nome: str = "Insumo Teste") -> dict:
    resp = c.post("/api/insumos", json={"nome": nome, "unidade_base": "un"})
    assert resp.status_code == 201, resp.text
    return resp.json()


def _set_custo_medio(insumo_id: int, custo: Decimal) -> None:
    from src.models.insumos import Insumo
    db: Session = _TestingSession()
    try:
        db.execute(update(Insumo).where(Insumo.id == insumo_id).values(custo_medio=custo))
        db.commit()
    finally:
        db.close()


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_batch_cria_itens_e_retorna_response(c):
    """Batch com 2 produtos distintos cria 2 itens e retorna schema correto."""
    consumidor_id = _criar_consumidor()
    p1 = _criar_produto(c, "Produto A", "20.00")
    p2 = _criar_produto(c, "Produto B", "15.00")

    resp = c.post("/api/consumo-interno/batch", json={
        "consumidor_id": consumidor_id,
        "itens": [
            {"produto_id": p1["id"], "quantidade": "2"},
            {"produto_id": p2["id"], "quantidade": "1"},
        ],
    })
    assert resp.status_code == 200, resp.text
    data = resp.json()

    assert len(data["itens"]) == 2
    produto_ids = {item["produto_id"] for item in data["itens"]}
    assert p1["id"] in produto_ids
    assert p2["id"] in produto_ids

    for item in data["itens"]:
        assert item["consumidor_id"] == consumidor_id
        assert "custo_unitario" in item
        assert "subtotal" in item
        assert "created_at" in item


def test_batch_calcula_custo_por_ficha_tecnica(c):
    """Custo unitário é calculado da ficha técnica (qtd_insumo * custo_medio)."""
    consumidor_id = _criar_consumidor()
    insumo = _criar_insumo(c, "Insumo Custo")
    _set_custo_medio(insumo["id"], Decimal("5.00"))

    produto = c.post("/api/produtos", json={
        "nome": "Produto com Ficha",
        "preco_venda": "25.00",
        "ficha_tecnica": [{"insumo_id": insumo["id"], "quantidade": "2"}],
    }).json()

    resp = c.post("/api/consumo-interno/batch", json={
        "consumidor_id": consumidor_id,
        "itens": [{"produto_id": produto["id"], "quantidade": "3"}],
    })
    assert resp.status_code == 200, resp.text
    item = resp.json()["itens"][0]

    # custo_unitario = 2 * 5.00 = 10.00
    assert float(item["custo_unitario"]) == pytest.approx(10.0)
    # subtotal = 10.00 * 3 = 30.00
    assert float(item["subtotal"]) == pytest.approx(30.0)


def test_batch_consumidor_inexistente_retorna_404(c):
    """Consumidor não encontrado → 404."""
    p = _criar_produto(c)
    resp = c.post("/api/consumo-interno/batch", json={
        "consumidor_id": 9999,
        "itens": [{"produto_id": p["id"], "quantidade": "1"}],
    })
    assert resp.status_code == 404


def test_batch_produto_inexistente_retorna_404(c):
    """Produto não encontrado → 404."""
    consumidor_id = _criar_consumidor()
    resp = c.post("/api/consumo-interno/batch", json={
        "consumidor_id": consumidor_id,
        "itens": [{"produto_id": 9999, "quantidade": "1"}],
    })
    assert resp.status_code == 404


def test_listar_retorna_itens_lancados(c):
    """GET / retorna os itens lançados pelo batch."""
    consumidor_id = _criar_consumidor()
    p = _criar_produto(c)

    c.post("/api/consumo-interno/batch", json={
        "consumidor_id": consumidor_id,
        "itens": [{"produto_id": p["id"], "quantidade": "2"}],
    })

    resp = c.get("/api/consumo-interno/")
    assert resp.status_code == 200, resp.text
    itens = resp.json()
    assert len(itens) == 1
    assert itens[0]["consumidor_id"] == consumidor_id
    assert itens[0]["produto_id"] == p["id"]


def test_listar_filtra_por_consumidor(c):
    """GET /?consumidor_id= retorna só os itens desse consumidor."""
    c1 = _criar_consumidor("Consumidor 1")
    c2 = _criar_consumidor("Consumidor 2")
    p = _criar_produto(c)

    c.post("/api/consumo-interno/batch", json={
        "consumidor_id": c1,
        "itens": [{"produto_id": p["id"], "quantidade": "1"}],
    })
    c.post("/api/consumo-interno/batch", json={
        "consumidor_id": c2,
        "itens": [{"produto_id": p["id"], "quantidade": "1"}],
    })

    resp = c.get(f"/api/consumo-interno/?consumidor_id={c1}")
    assert resp.status_code == 200, resp.text
    itens = resp.json()
    assert all(item["consumidor_id"] == c1 for item in itens)
    assert len(itens) == 1


def test_resumo_agrupa_por_consumidor(c):
    """GET /resumo retorna um item por consumidor com totais corretos."""
    c1 = _criar_consumidor("Consumidor A")
    c2 = _criar_consumidor("Consumidor B")
    insumo = _criar_insumo(c, "Insumo Resumo")
    _set_custo_medio(insumo["id"], Decimal("4.00"))

    produto = c.post("/api/produtos", json={
        "nome": "Produto Resumo",
        "preco_venda": "10.00",
        "ficha_tecnica": [{"insumo_id": insumo["id"], "quantidade": "1"}],
    }).json()

    # c1 lança 3 unidades → subtotal = 3 * 4.00 = 12.00
    c.post("/api/consumo-interno/batch", json={
        "consumidor_id": c1,
        "itens": [{"produto_id": produto["id"], "quantidade": "3"}],
    })
    # c2 lança 1 unidade → subtotal = 1 * 4.00 = 4.00
    c.post("/api/consumo-interno/batch", json={
        "consumidor_id": c2,
        "itens": [{"produto_id": produto["id"], "quantidade": "1"}],
    })

    resp = c.get("/api/consumo-interno/resumo")
    assert resp.status_code == 200, resp.text
    resumo = {r["consumidor_id"]: r for r in resp.json()}

    assert c1 in resumo
    assert c2 in resumo
    assert float(resumo[c1]["total"]) == pytest.approx(12.0)
    assert float(resumo[c2]["total"]) == pytest.approx(4.0)
    assert resumo[c1]["itens_no_mes"] == 1
    assert resumo[c2]["itens_no_mes"] == 1


def test_estornar_remove_item_da_lista(c):
    """DELETE /{id} remove o item da listagem."""
    consumidor_id = _criar_consumidor()
    p = _criar_produto(c)

    batch_resp = c.post("/api/consumo-interno/batch", json={
        "consumidor_id": consumidor_id,
        "itens": [{"produto_id": p["id"], "quantidade": "1"}],
    })
    item_id = batch_resp.json()["itens"][0]["id"]

    del_resp = c.delete(f"/api/consumo-interno/{item_id}")
    assert del_resp.status_code == 200, del_resp.text

    lista = c.get("/api/consumo-interno/").json()
    assert all(item["id"] != item_id for item in lista)


def test_batch_lista_vazia_retorna_422(c):
    """Batch sem itens → 422 (validação Pydantic min_length=1)."""
    consumidor_id = _criar_consumidor()
    resp = c.post("/api/consumo-interno/batch", json={
        "consumidor_id": consumidor_id,
        "itens": [],
    })
    assert resp.status_code == 422
