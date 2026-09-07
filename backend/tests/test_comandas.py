
import os
from decimal import Decimal

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
def crud_client():
    def override_get_db():
        db = _TestingSession()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = _fake_user
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _criar_garcom(c, nome="Joao", ativo=True):
    resp = c.post("/api/garcons", json={"nome": nome})
    assert resp.status_code == 201, resp.text
    garcom = resp.json()
    if not ativo:
        resp2 = c.put(f"/api/garcons/{garcom['id']}", json={"nome": nome, "ativo": False})
        assert resp2.status_code == 200, resp2.text
        return resp2.json()
    return garcom


def _criar_item_vendavel(c, nome="Coca", preco="10.00"):
    resp = c.post("/api/produtos", json={
        "nome": nome,
        "preco_venda": preco,
    })
    assert resp.status_code == 201, resp.text
    return resp.json()


def _abrir_comanda(c, garcom_id, identificacao="Mesa 1", tipo="mesa"):
    resp = c.post("/api/comandas", json={
        "identificacao": identificacao,
        "tipo_identificacao": tipo,
        "garcom_id": garcom_id,
        "pessoas": ["Cliente 1"],
    })
    assert resp.status_code == 201, resp.text
    return resp.json()


def _lancar_item(c, comanda_id, item_id, version, quantidade=1, cortesia=False):
    resp = c.post(f"/api/comandas/{comanda_id}/itens", json={
        "item_id": item_id,
        "quantidade": quantidade,
        "cortesia": cortesia,
        "version": version,
    })
    return resp


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_abrir_comanda(crud_client):
    garcom = _criar_garcom(crud_client)
    resp = crud_client.post("/api/comandas", json={
        "identificacao": "Mesa 5",
        "tipo_identificacao": "mesa",
        "garcom_id": garcom["id"],
        "pessoas": ["Ana", "Bob"],
    })
    assert resp.status_code == 201
    body = resp.json()
    assert body["status"] == "aberta"
    assert body["version"] == 1
    assert body["pessoas"] == ["Ana", "Bob"]
    assert body["garcom_nome"] == "Joao"


def test_garcom_inativo_bloqueado(crud_client):
    garcom = _criar_garcom(crud_client, ativo=False)
    resp = crud_client.post("/api/comandas", json={
        "identificacao": "Mesa 1",
        "tipo_identificacao": "mesa",
        "garcom_id": garcom["id"],
        "pessoas": ["Cliente 1"],
    })
    assert resp.status_code == 400
    assert resp.json()["error"]["code"] == "GARCOM_INATIVO"


def test_lancar_item_snapshot_preco(crud_client):
    garcom = _criar_garcom(crud_client)
    item = _criar_item_vendavel(crud_client, preco="15.50")
    comanda = _abrir_comanda(crud_client, garcom["id"])

    resp = _lancar_item(crud_client, comanda["id"], item["id"], comanda["version"])
    assert resp.status_code == 200
    body = resp.json()
    itens = body["itens_ativos"]
    assert len(itens) == 1
    assert Decimal(itens[0]["preco_unitario"]) == Decimal("15.50")


def test_cortesia_preco_zero(crud_client):
    garcom = _criar_garcom(crud_client)
    item = _criar_item_vendavel(crud_client, preco="20.00")
    comanda = _abrir_comanda(crud_client, garcom["id"])

    resp = _lancar_item(crud_client, comanda["id"], item["id"], comanda["version"], cortesia=True)
    assert resp.status_code == 200
    body = resp.json()
    itens = body["itens_ativos"]
    assert Decimal(itens[0]["preco_unitario"]) == Decimal("0")
    assert Decimal(itens[0]["subtotal"]) == Decimal("0")


def test_lancar_incrementa_version(crud_client):
    garcom = _criar_garcom(crud_client)
    item = _criar_item_vendavel(crud_client)
    comanda = _abrir_comanda(crud_client, garcom["id"])
    assert comanda["version"] == 1

    resp = _lancar_item(crud_client, comanda["id"], item["id"], 1)
    assert resp.status_code == 200
    assert resp.json()["version"] == 2


def test_version_conflict_retorna_409(crud_client):
    garcom = _criar_garcom(crud_client)
    item = _criar_item_vendavel(crud_client)
    comanda = _abrir_comanda(crud_client, garcom["id"])

    resp = _lancar_item(crud_client, comanda["id"], item["id"], version=999)
    assert resp.status_code == 409
    assert resp.json()["error"]["code"] == "COMANDA_DESATUALIZADA"


def test_editar_item(crud_client):
    garcom = _criar_garcom(crud_client)
    item = _criar_item_vendavel(crud_client)
    comanda = _abrir_comanda(crud_client, garcom["id"])

    resp = _lancar_item(crud_client, comanda["id"], item["id"], comanda["version"], quantidade=2)
    assert resp.status_code == 200
    body = resp.json()
    item_id = body["itens_ativos"][0]["id"]
    version = body["version"]

    resp2 = crud_client.patch(
        f"/api/comandas/{comanda['id']}/itens/{item_id}",
        json={"quantidade": 5, "version": version},
    )
    assert resp2.status_code == 200
    assert Decimal(resp2.json()["itens_ativos"][0]["quantidade"]) == Decimal("5")


def test_cancelar_item(crud_client):
    garcom = _criar_garcom(crud_client)
    item = _criar_item_vendavel(crud_client, preco="10.00")
    comanda = _abrir_comanda(crud_client, garcom["id"])

    resp = _lancar_item(crud_client, comanda["id"], item["id"], comanda["version"])
    body = resp.json()
    item_c_id = body["itens_ativos"][0]["id"]
    version = body["version"]

    resp2 = crud_client.post(
        f"/api/comandas/{comanda['id']}/itens/{item_c_id}/cancelar",
        json={"motivo": "erro_lancamento", "estornado": False, "version": version},
    )
    assert resp2.status_code == 200
    body2 = resp2.json()
    cancelado = next(i for i in body2["itens_ativos"] if i["id"] == item_c_id)
    assert cancelado["cancelado"] is True
    assert Decimal(body2["total_parcial"]) == Decimal("0")


def test_eventos_gravados(crud_client):
    from src.models.eventos_comanda import EventoComanda

    garcom = _criar_garcom(crud_client)
    item = _criar_item_vendavel(crud_client)
    comanda = _abrir_comanda(crud_client, garcom["id"])
    _lancar_item(crud_client, comanda["id"], item["id"], comanda["version"])

    db = _TestingSession()
    eventos = db.query(EventoComanda).filter(EventoComanda.comanda_id == comanda["id"]).all()
    db.close()
    assert len(eventos) == 2
    tipos = {e.tipo for e in eventos}
    assert "comanda_aberta" in tipos
    assert "item_lancado" in tipos


def test_total_parcial_exclui_cancelados_e_cortesias(crud_client):
    garcom = _criar_garcom(crud_client)
    item = _criar_item_vendavel(crud_client, preco="10.00")
    comanda = _abrir_comanda(crud_client, garcom["id"])

    # lançar item normal (10.00)
    resp = _lancar_item(crud_client, comanda["id"], item["id"], comanda["version"])
    body = resp.json()
    version = body["version"]

    # lançar cortesia (0.00)
    resp2 = _lancar_item(crud_client, comanda["id"], item["id"], version, cortesia=True)
    body2 = resp2.json()
    version2 = body2["version"]

    # total deve ser 10.00 (normal) + 0 (cortesia) = 10.00
    assert Decimal(body2["total_parcial"]) == Decimal("10.00")

    # cancelar o item normal
    item_normal_id = body2["itens_ativos"][0]["id"]
    resp3 = crud_client.post(
        f"/api/comandas/{comanda['id']}/itens/{item_normal_id}/cancelar",
        json={"motivo": "erro_lancamento", "estornado": False, "version": version2},
    )
    assert resp3.status_code == 200
    assert Decimal(resp3.json()["total_parcial"]) == Decimal("0")


def test_abrir_comanda_loga_evento_estruturado(crud_client, monkeypatch):
    from src.services import comandas_service

    calls = []
    monkeypatch.setattr(
        comandas_service.logger,
        "info",
        lambda event, **kwargs: calls.append((event, kwargs)),
    )

    garcom = _criar_garcom(crud_client)
    comanda = _abrir_comanda(crud_client, garcom["id"])

    eventos = [event for event, _ in calls]
    assert "comanda_aberta" in eventos
    kwargs = dict(calls[eventos.index("comanda_aberta")][1])
    assert kwargs["comanda_id"] == comanda["id"]
    assert "tenant_id" in kwargs


def test_fechar_comanda_loga_evento_estruturado(crud_client, monkeypatch):
    from src.services import comandas_service

    calls = []
    monkeypatch.setattr(
        comandas_service.logger,
        "info",
        lambda event, **kwargs: calls.append((event, kwargs)),
    )

    garcom = _criar_garcom(crud_client)
    item = _criar_item_vendavel(crud_client, preco="10.00")
    metodo_resp = crud_client.post("/api/metodos-pagamento", json={"nome": "PIX"})
    metodo = metodo_resp.json()
    comanda = _abrir_comanda(crud_client, garcom["id"])
    cid = comanda["id"]
    r = _lancar_item(crud_client, cid, item["id"], comanda["version"]).json()

    resp = crud_client.post(
        f"/api/comandas/{cid}/fechar",
        json={
            "pagamentos": [{"metodo_id": metodo["id"], "valor": "10.00"}],
            "modo_divisao": "sem_divisao",
            "version": r["version"],
        },
    )
    assert resp.status_code == 200, resp.text

    eventos = [event for event, _ in calls]
    assert "comanda_fechada" in eventos
    kwargs = dict(calls[eventos.index("comanda_fechada")][1])
    assert kwargs["comanda_id"] == cid


def test_parse_pessoas_malformado_nao_loga_conteudo_bruto(monkeypatch):
    """`pessoas_json` bruto pode conter nome de cliente — o log de warning de
    parse malformado não deve incluir o valor bruto, só metadados não-sensíveis."""
    from src.services import comandas_service

    calls = []
    monkeypatch.setattr(
        comandas_service.logger,
        "warning",
        lambda event, **kwargs: calls.append((event, kwargs)),
    )

    raw = '{"nome": "Fulano de Tal, telefone (11) 99999-0000"'  # JSON malformado, contém PII
    resultado = comandas_service._parse_pessoas(raw)

    assert resultado == []
    assert len(calls) == 1
    _event, kwargs = calls[0]
    assert "pessoas_json" not in kwargs
    assert raw not in str(kwargs)


def test_taxa_servico_percentual_e_constante_nomeada_de_10_por_cento():
    from src.services import comandas_service

    assert comandas_service.TAXA_SERVICO_PERCENTUAL == Decimal("10.00")


def test_fechar_comanda_com_taxa_servico_cobra_10_por_cento_e_gera_comissao(crud_client):
    garcom = _criar_garcom(crud_client)
    item = _criar_item_vendavel(crud_client, preco="100.00")
    metodo_resp = crud_client.post("/api/metodos-pagamento", json={"nome": "PIX"})
    assert metodo_resp.status_code in (200, 201), metodo_resp.text
    metodo = metodo_resp.json()
    comanda = _abrir_comanda(crud_client, garcom["id"])
    cid = comanda["id"]

    r = _lancar_item(crud_client, cid, item["id"], comanda["version"]).json()

    resp = crud_client.post(
        f"/api/comandas/{cid}/fechar",
        json={
            "pagamentos": [{"metodo_id": metodo["id"], "valor": "110.00"}],
            "modo_divisao": "sem_divisao",
            "taxa_servico": True,
            "version": r["version"],
        },
    )
    assert resp.status_code == 200, resp.text

    db = _TestingSession()
    try:
        from src.models.comissoes_garcom import ComissaoGarcom

        comissao = db.query(ComissaoGarcom).filter(ComissaoGarcom.comanda_id == cid).one()
        assert comissao.valor == Decimal("10.00")
        assert comissao.percentual == Decimal("10.00")
    finally:
        db.close()


def test_list_fechadas_data_malformada_retorna_erro_validacao(crud_client):
    resp = crud_client.get("/api/comandas/fechadas?data_inicio=nao-e-uma-data")
    assert resp.status_code in (400, 422), resp.text


def test_list_fechadas_filtra_por_periodo(crud_client):
    garcom = _criar_garcom(crud_client)
    _abrir_comanda(crud_client, garcom["id"])

    resp = crud_client.get("/api/comandas/fechadas?data_inicio=2020-01-01&data_fim=2020-01-31")
    assert resp.status_code == 200, resp.text
    assert resp.json() == []


def test_top_itens(crud_client):
    garcom = _criar_garcom(crud_client)
    item = _criar_item_vendavel(crud_client, nome="Cerveja")
    comanda = _abrir_comanda(crud_client, garcom["id"])

    version = comanda["version"]
    for _ in range(3):
        resp = _lancar_item(crud_client, comanda["id"], item["id"], version)
        version = resp.json()["version"]

    resp = crud_client.get("/api/produtos/top?dias=7&limit=6")
    assert resp.status_code == 200
    nomes = [i["nome"] for i in resp.json()]
    assert "Cerveja" in nomes


def test_calcular_fechamento_total_pago_sem_desconto_sem_taxa():
    from src.services.comandas_service import _calcular_fechamento

    calculo = _calcular_fechamento(
        subtotal=Decimal("100.00"),
        desconto_percentual=None,
        desconto_valor=None,
        saldo_pendente=None,
        total_pago=Decimal("100.00"),
        modo_divisao="sem_divisao",
        taxa_servico=False,
        garcom_id=None,
    )

    assert calculo.total_com_desconto == Decimal("100.00")
    assert calculo.esperado == Decimal("100.00")
    assert calculo.novo_saldo is None
    assert calculo.valor_comissao is None


def test_calcular_fechamento_com_desconto_percentual_quantiza():
    from src.services.comandas_service import _calcular_fechamento

    calculo = _calcular_fechamento(
        subtotal=Decimal("100.00"),
        desconto_percentual=Decimal("12.50"),
        desconto_valor=None,
        saldo_pendente=None,
        total_pago=Decimal("87.50"),
        modo_divisao="sem_divisao",
        taxa_servico=False,
        garcom_id=None,
    )

    assert calculo.total_com_desconto == Decimal("87.500")
    assert calculo.esperado == Decimal("87.50")


def test_calcular_fechamento_com_taxa_servico_e_garcom_calcula_comissao():
    from src.services.comandas_service import TAXA_SERVICO_PERCENTUAL, _calcular_fechamento

    calculo = _calcular_fechamento(
        subtotal=Decimal("100.00"),
        desconto_percentual=None,
        desconto_valor=None,
        saldo_pendente=None,
        total_pago=Decimal("110.00"),
        modo_divisao="sem_divisao",
        taxa_servico=True,
        garcom_id=7,
    )

    assert calculo.esperado == Decimal("110.00")
    assert calculo.valor_comissao == (Decimal("100.00") * TAXA_SERVICO_PERCENTUAL / Decimal("100")).quantize(
        Decimal("0.01")
    )


def test_calcular_fechamento_pagamento_completo_nao_bate_levanta_erro():
    from src.core.errors import AppError, ErrorCode
    from src.services.comandas_service import _calcular_fechamento

    with pytest.raises(AppError) as exc_info:
        _calcular_fechamento(
            subtotal=Decimal("100.00"),
            desconto_percentual=None,
            desconto_valor=None,
            saldo_pendente=None,
            total_pago=Decimal("50.00"),
            modo_divisao="sem_divisao",
            taxa_servico=False,
            garcom_id=None,
        )

    assert exc_info.value.code == ErrorCode.PAGAMENTO_NAO_BATE


def test_calcular_fechamento_parcial_menor_que_base_calcula_novo_saldo():
    from src.services.comandas_service import _calcular_fechamento

    calculo = _calcular_fechamento(
        subtotal=Decimal("100.00"),
        desconto_percentual=None,
        desconto_valor=None,
        saldo_pendente=None,
        total_pago=Decimal("40.00"),
        modo_divisao="parcial",
        taxa_servico=False,
        garcom_id=None,
    )

    assert calculo.novo_saldo == Decimal("60.00")
    assert calculo.esperado is None
    assert calculo.valor_comissao is None


def test_calcular_fechamento_parcial_maior_ou_igual_base_levanta_erro():
    from src.core.errors import AppError, ErrorCode
    from src.services.comandas_service import _calcular_fechamento

    with pytest.raises(AppError) as exc_info:
        _calcular_fechamento(
            subtotal=Decimal("100.00"),
            desconto_percentual=None,
            desconto_valor=None,
            saldo_pendente=None,
            total_pago=Decimal("100.00"),
            modo_divisao="parcial",
            taxa_servico=False,
            garcom_id=None,
        )

    assert exc_info.value.code == ErrorCode.PAGAMENTO_NAO_BATE


def test_calcular_fechamento_parcial_usa_saldo_pendente_quando_reaberta():
    from src.services.comandas_service import _calcular_fechamento

    calculo = _calcular_fechamento(
        subtotal=Decimal("100.00"),
        desconto_percentual=None,
        desconto_valor=None,
        saldo_pendente=Decimal("30.00"),
        total_pago=Decimal("10.00"),
        modo_divisao="parcial",
        taxa_servico=False,
        garcom_id=None,
    )

    assert calculo.novo_saldo == Decimal("20.00")
