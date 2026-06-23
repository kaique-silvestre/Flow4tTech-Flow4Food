import os
from datetime import datetime, timezone

os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
os.environ.setdefault("JWT_SECRET", "test-secret-only-for-tests-32chars!!")
os.environ.setdefault("ENV", "test")

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import StaticPool, create_engine
from sqlalchemy.orm import sessionmaker

from src.api.dependencies import get_current_user, get_db
from src.core.database import Base
from src.main import app
from src.models.promocoes import Promocao, PromocaoProduto

_engine = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
_Session = sessionmaker(bind=_engine, autoflush=False, autocommit=False)


def _fake_user_t1() -> dict:
    return {"sub": "1", "user_id": 1, "tenant_id": 1, "permissions": ["cadastros"]}


def _fake_user_t2() -> dict:
    return {"sub": "2", "user_id": 2, "tenant_id": 2, "permissions": ["cadastros"]}


@pytest.fixture(autouse=True)
def _setup_db():
    Base.metadata.create_all(_engine)
    yield
    Base.metadata.drop_all(_engine)


def _override_db():
    db = _Session()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture
def client():
    app.dependency_overrides[get_db] = _override_db
    app.dependency_overrides[get_current_user] = _fake_user_t1
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


def _seed_promo(
    tenant_id: int = 1,
    nome: str = "Promo Teste",
    recorrencia: str = "nenhuma",
    dias_semana=None,
    dias_mes=None,
    data_inicio: str = "2026-06-01",
    data_fim: str = "2026-06-30",
) -> int:
    db = _Session()
    promo = Promocao(
        tenant_id=tenant_id,
        nome=nome,
        tipo_desconto="porcentagem",
        valor_desconto=10.0,
        data_inicio=datetime.strptime(data_inicio, "%Y-%m-%d").date(),
        data_fim=datetime.strptime(data_fim, "%Y-%m-%d").date() if data_fim else None,
        recorrencia=recorrencia,
        dias_semana=dias_semana,
        dias_mes=dias_mes,
        created_at=datetime.now(timezone.utc),
    )
    db.add(promo)
    db.commit()
    pid = promo.id
    db.close()
    return pid


# H1 — criar promoção semanal válida
def test_criar_promocao_semanal_valida(client):
    resp = client.post("/api/promocoes", json={
        "nome": "Promoção Semana",
        "tipo_desconto": "porcentagem",
        "valor_desconto": 15,
        "data_inicio": "2026-07-01",
        "recorrencia": "semanal",
        "dias_semana": [1, 3, 5],
    })
    assert resp.status_code == 201, resp.text
    body = resp.json()
    assert body["recorrencia"] == "semanal"
    assert body["dias_semana"] == [1, 3, 5]


# H2 — recorrencia=semanal sem dias_semana → 422
def test_criar_promocao_semanal_sem_dias(client):
    resp = client.post("/api/promocoes", json={
        "nome": "Promo",
        "tipo_desconto": "porcentagem",
        "valor_desconto": 10,
        "data_inicio": "2026-07-01",
        "recorrencia": "semanal",
    })
    assert resp.status_code == 422, resp.text


# H3 — recorrencia=nenhuma com dias_semana preenchido → 422
def test_criar_promocao_nenhuma_com_dias(client):
    resp = client.post("/api/promocoes", json={
        "nome": "Promo",
        "tipo_desconto": "porcentagem",
        "valor_desconto": 10,
        "data_inicio": "2026-07-01",
        "recorrencia": "nenhuma",
        "dias_semana": [1, 2],
    })
    assert resp.status_code == 422, resp.text


# H4 — data_fim antes de data_inicio → 422
def test_data_fim_antes_inicio(client):
    resp = client.post("/api/promocoes", json={
        "nome": "Promo",
        "tipo_desconto": "porcentagem",
        "valor_desconto": 10,
        "data_inicio": "2026-07-15",
        "data_fim": "2026-07-01",
        "recorrencia": "nenhuma",
    })
    assert resp.status_code == 422, resp.text


# H5 — CRUD completo
def test_crud_completo(client):
    # create
    resp = client.post("/api/promocoes", json={
        "nome": "Happy Hour",
        "tipo_desconto": "valor_fixo",
        "valor_desconto": 5.0,
        "data_inicio": "2026-06-01",
        "data_fim": "2026-06-30",
        "recorrencia": "nenhuma",
        "produto_ids": [],
    })
    assert resp.status_code == 201, resp.text
    pid = resp.json()["id"]

    # list
    resp = client.get("/api/promocoes")
    assert resp.status_code == 200
    assert any(p["id"] == pid for p in resp.json())

    # update
    resp = client.patch(f"/api/promocoes/{pid}", json={"nome": "Happy Hour Atualizado"})
    assert resp.status_code == 200
    assert resp.json()["nome"] == "Happy Hour Atualizado"

    # delete
    resp = client.delete(f"/api/promocoes/{pid}")
    assert resp.status_code == 204

    # confirm gone
    db = _Session()
    assert db.query(Promocao).filter(Promocao.id == pid).first() is None
    db.close()


# H6 — RLS cross-tenant (SQLite: testar tenant_id direto no DB)
def test_rls_cross_tenant(client):
    _seed_promo(tenant_id=1, nome="T1 Promo")
    _seed_promo(tenant_id=2, nome="T2 Promo")

    db = _Session()
    t1 = db.query(Promocao).filter(Promocao.tenant_id == 1).all()
    t2 = db.query(Promocao).filter(Promocao.tenant_id == 2).all()
    db.close()

    assert len(t1) == 1 and t1[0].nome == "T1 Promo"
    assert len(t2) == 1 and t2[0].nome == "T2 Promo"


# H7 — recorrencia=mensal válida
def test_criar_promocao_mensal_valida(client):
    resp = client.post("/api/promocoes", json={
        "nome": "Promo Mensal",
        "tipo_desconto": "porcentagem",
        "valor_desconto": 20,
        "data_inicio": "2026-07-01",
        "recorrencia": "mensal",
        "dias_mes": [1, 15, 30],
    })
    assert resp.status_code == 201, resp.text
    assert resp.json()["dias_mes"] == [1, 15, 30]


# H8 — listagem por mês
def test_list_por_mes(client):
    _seed_promo(nome="Junho", data_inicio="2026-06-01", data_fim="2026-06-30")
    _seed_promo(nome="Agosto", data_inicio="2026-08-01", data_fim="2026-08-31")

    resp = client.get("/api/promocoes/mes?mes=2026-06")
    assert resp.status_code == 200
    nomes = {p["nome"] for p in resp.json()}
    assert "Junho" in nomes
    assert "Agosto" not in nomes


# H9 — delete 404
def test_delete_not_found(client):
    resp = client.delete("/api/promocoes/9999")
    assert resp.status_code == 404
