import datetime
import os
from decimal import Decimal

os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
os.environ.setdefault("JWT_SECRET", "test-secret-only-for-tests")
os.environ.setdefault("ENV", "test")

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import StaticPool, create_engine, event, update
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


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _criar_garcom(c, nome="Garcom"):
    resp = c.post("/api/garcons", json={"nome": nome})
    assert resp.status_code == 201, resp.text
    return resp.json()


def _criar_item(c, nome="Item", preco="50.00"):
    resp = c.post("/api/produtos", json={"nome": nome, "preco_venda": preco})
    assert resp.status_code == 201, resp.text
    return resp.json()


def _criar_metodo(c, nome="PIX"):
    resp = c.post("/api/metodos-pagamento", json={"nome": nome})
    assert resp.status_code in (200, 201), resp.text
    return resp.json()


def _abrir_comanda(c, garcom_id, identificacao="Mesa 1"):
    resp = c.post(
        "/api/comandas",
        json={"identificacao": identificacao, "tipo_identificacao": "mesa", "garcom_id": garcom_id, "pessoas": ["Cliente 1"]},
    )
    assert resp.status_code == 201, resp.text
    return resp.json()


def _lancar_item(c, comanda_id, item_id, version, quantidade=1, cortesia=False):
    resp = c.post(
        f"/api/comandas/{comanda_id}/itens",
        json={"item_id": item_id, "quantidade": quantidade, "version": version, "cortesia": cortesia},
    )
    assert resp.status_code == 200, resp.text
    return resp.json()


def _fechar(c, comanda_id, metodo_id, valor, version):
    resp = c.post(
        f"/api/comandas/{comanda_id}/fechar",
        json={
            "pagamentos": [{"metodo_id": metodo_id, "valor": str(valor)}],
            "modo_divisao": "sem_divisao",
            "version": version,
        },
    )
    assert resp.status_code == 200, resp.text
    return resp.json()


def _criar_insumo(c, nome="Insumo"):
    resp = c.post("/api/insumos", json={"nome": nome, "unidade_base": "un"})
    assert resp.status_code == 201, resp.text
    return resp.json()


def _baixa_sem_venda(c, item_id, quantidade, motivo):
    resp = c.post(
        "/api/estoque/baixa-sem-venda",
        json={"item_id": item_id, "quantidade": str(quantidade), "motivo": motivo},
    )
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


def _forcar_comissao_pendente(comissao_id: int) -> None:
    """Força `pago=False` direto no banco.

    Necessário porque no SQLite dos testes o `server_default="false"` do
    model (`ComissaoGarcom.pago`) é renderizado como a string literal
    `'false'` (não o booleano), que o SQLite grava e a coluna `BOOLEAN` lê de
    volta como truthy — uma comissão recém-criada por `fechar_comanda` já
    nasce com `pago=True` neste ambiente de teste (não reproduz o Postgres de
    produção, onde o mesmo default resolve para `false` corretamente)."""
    from src.models.comissoes_garcom import ComissaoGarcom

    db: Session = _TestingSession()
    try:
        db.execute(update(ComissaoGarcom).where(ComissaoGarcom.id == comissao_id).values(pago=False))
        db.commit()
    finally:
        db.close()


def _set_estoque(insumo_id: int, estoque_atual: Decimal, nivel_critico=None) -> None:
    """Ajusta `estoque_atual`/`nivel_critico` direto no banco — não há endpoint
    de API para definir `estoque_atual` fora do fluxo de movimentos."""
    from src.models.insumos import Insumo

    db: Session = _TestingSession()
    try:
        values = {"estoque_atual": estoque_atual}
        if nivel_critico is not None:
            values["nivel_critico"] = nivel_critico
        db.execute(update(Insumo).where(Insumo.id == insumo_id).values(**values))
        db.commit()
    finally:
        db.close()


def _set_data_fechamento(comanda_id: int, dt_utc: datetime.datetime) -> None:
    from src.models.comandas import Comanda

    db: Session = _TestingSession()
    try:
        db.execute(update(Comanda).where(Comanda.id == comanda_id).values(data_fechamento=dt_utc))
        db.commit()
    finally:
        db.close()


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


def test_dashboard_cards_hoje(c):
    """Fecha comanda R$100 hoje → faturamento_hoje=100, ticket_medio=100, comandas_fechadas_hoje=1."""
    garcom = _criar_garcom(c)
    item = _criar_item(c, preco="100.00")
    metodo = _criar_metodo(c)

    comanda = _abrir_comanda(c, garcom["id"])
    r = _lancar_item(c, comanda["id"], item["id"], comanda["version"])
    _fechar(c, comanda["id"], metodo["id"], "100.00", r["version"])

    resp = c.get("/api/dashboard")
    assert resp.status_code == 200, resp.text
    data = resp.json()

    assert float(data["faturamento_hoje"]) == pytest.approx(100.0)
    assert float(data["ticket_medio_hoje"]) == pytest.approx(100.0)
    assert data["comandas_fechadas_hoje"] == 1


def test_compras_agendadas_carrega_fornecedores_em_uma_query():
    from src.models.compras import Compra
    from src.models.fornecedores import Fornecedor
    from src.repositories import dashboard_repository as dr

    db: Session = _TestingSession()
    try:
        hoje = datetime.date.today()
        fornecedores = [Fornecedor(tenant_id=1, nome=f"Fornecedor {indice}") for indice in range(3)]
        db.add_all(fornecedores)
        db.flush()
        db.add_all(
            [
                Compra(
                    tenant_id=1,
                    fornecedor_id=fornecedor.id,
                    data_compra=hoje,
                    data_prevista_recebimento=hoje,
                    total=Decimal("10.00"),
                    status="confirmado",
                )
                for fornecedor in fornecedores
            ]
        )
        db.commit()

        queries = 0

        def contar_queries(*_args, **_kwargs):
            nonlocal queries
            queries += 1

        event.listen(_engine, "before_cursor_execute", contar_queries)
        try:
            entregas = dr.compras_agendadas_com_fornecedor(db, hoje)
        finally:
            event.remove(_engine, "before_cursor_execute", contar_queries)

        assert queries == 1
        assert [entrega["fornecedor_nome"] for entrega in entregas] == [
            "Fornecedor 0",
            "Fornecedor 1",
            "Fornecedor 2",
        ]
    finally:
        db.close()


def test_dashboard_lucro_estimado(c):
    """Produto com insumo custo_medio=30, preco=100 → lucro_estimado = 70."""
    garcom = _criar_garcom(c)
    metodo = _criar_metodo(c)

    insumo_resp = c.post("/api/insumos", json={"nome": "Insumo CMV", "unidade_base": "un"})
    assert insumo_resp.status_code == 201
    insumo_id = insumo_resp.json()["id"]
    _set_custo_medio(insumo_id, Decimal("30.00"))

    produto_resp = c.post("/api/produtos", json={
        "nome": "Produto CMV", "preco_venda": "100.00",
        "ficha_tecnica": [{"insumo_id": insumo_id, "quantidade": "1"}],
    })
    assert produto_resp.status_code == 201
    produto = produto_resp.json()

    comanda = _abrir_comanda(c, garcom["id"])
    r = _lancar_item(c, comanda["id"], produto["id"], comanda["version"])
    _fechar(c, comanda["id"], metodo["id"], "100.00", r["version"])

    resp = c.get("/api/dashboard")
    assert resp.status_code == 200, resp.text
    data = resp.json()

    assert float(data["lucro_estimado_hoje"]) == pytest.approx(70.0)


def test_dashboard_faturamento_por_hora_timezone(c):
    """
    Comanda fechada às 23:00 UTC = 20:00 SP (UTC-3).
    bucket[20].faturamento > 0, bucket[23].faturamento == 0.
    """
    garcom = _criar_garcom(c)
    item = _criar_item(c, preco="50.00")
    metodo = _criar_metodo(c)

    comanda = _abrir_comanda(c, garcom["id"])
    r = _lancar_item(c, comanda["id"], item["id"], comanda["version"])
    _fechar(c, comanda["id"], metodo["id"], "50.00", r["version"])

    # Forçar data_fechamento = hoje às 23:00 UTC (= 20:00 SP)
    import datetime
    from zoneinfo import ZoneInfo
    TZ = ZoneInfo("America/Sao_Paulo")
    today_sp = datetime.datetime.now(TZ).date()
    dt_utc = datetime.datetime(today_sp.year, today_sp.month, today_sp.day, 23, 0, 0)
    _set_data_fechamento(comanda["id"], dt_utc)

    resp = c.get("/api/dashboard")
    assert resp.status_code == 200, resp.text
    data = resp.json()

    buckets = {b["hora"]: float(b["faturamento"]) for b in data["faturamento_por_hora"]}
    assert len(data["faturamento_por_hora"]) == 24
    assert buckets[20] == pytest.approx(50.0)
    assert buckets[23] == pytest.approx(0.0)


def test_dashboard_top_10_produtos(c):
    """3 itens com quantidades distintas → lista ordenada por quantidade desc."""
    garcom = _criar_garcom(c)
    item_a = _criar_item(c, nome="ItemA", preco="10.00")
    item_b = _criar_item(c, nome="ItemB", preco="10.00")
    item_c = _criar_item(c, nome="ItemC", preco="10.00")
    metodo = _criar_metodo(c)

    # comanda 1: 3x ItemA, 2x ItemB, 1x ItemC
    comanda = _abrir_comanda(c, garcom["id"])
    v = comanda["version"]
    r = _lancar_item(c, comanda["id"], item_a["id"], v, quantidade=3)
    v = r["version"]
    r = _lancar_item(c, comanda["id"], item_b["id"], v, quantidade=2)
    v = r["version"]
    r = _lancar_item(c, comanda["id"], item_c["id"], v, quantidade=1)
    _fechar(c, comanda["id"], metodo["id"], "60.00", r["version"])

    resp = c.get("/api/dashboard")
    assert resp.status_code == 200, resp.text
    data = resp.json()

    top = data["top_10_produtos"]
    assert len(top) >= 3
    nomes = [p["nome"] for p in top]
    # ItemA (3) deve ser primeiro
    assert nomes[0] == "ItemA"
    assert top[0]["quantidade"] == 3
    assert top[1]["quantidade"] == 2
    assert top[2]["quantidade"] == 1


def test_por_metodo_pagamento_hoje_inclui_pagamento_parcial_de_comanda_ainda_aberta(c):
    """Comanda com pagamento parcial hoje que NÃO fecha (modo_divisao="parcial"
    mantém a comanda aberta, com saldo_pendente) → o pagamento já recebido deve
    contar em por_metodo_pagamento_hoje mesmo assim (prova que a query não reusa
    o filtro de comandas fechadas de fechamento_caixa/_build_por_metodo).

    Nota: um cenário de fechar-e-depois-reabrir não serve de prova aqui —
    `reabrir_comanda` apaga as linhas de `Pagamento` da comanda (comportamento
    de `comandas_service.py`, fora do escopo deste ticket), então não haveria
    pagamento algum para a query encontrar depois da reabertura. O caso crítico
    real descrito na spec ("pagamento parcial hoje que não fechou, status
    aberto/reaberto") é o pagamento parcial abaixo, que deixa a comanda aberta
    sem jamais apagar o pagamento já registrado."""
    garcom = _criar_garcom(c)
    item = _criar_item(c, preco="100.00")
    metodo = _criar_metodo(c, nome="Dinheiro")

    comanda = _abrir_comanda(c, garcom["id"])
    r = _lancar_item(c, comanda["id"], item["id"], comanda["version"])
    resp_fechar = c.post(
        f"/api/comandas/{comanda['id']}/fechar",
        json={
            "pagamentos": [{"metodo_id": metodo["id"], "valor": "40.00"}],
            "modo_divisao": "parcial",
            "version": r["version"],
        },
    )
    assert resp_fechar.status_code == 200, resp_fechar.text
    assert resp_fechar.json()["status"] != "fechada"

    resp = c.get("/api/dashboard")
    assert resp.status_code == 200, resp.text
    data = resp.json()

    por_metodo = {p["metodo_nome"]: p for p in data["por_metodo_pagamento_hoje"]}
    assert "Dinheiro" in por_metodo
    assert float(por_metodo["Dinheiro"]["total"]) == pytest.approx(40.0)


def test_dashboard_comandas_abertas_lista(c):
    """2 comandas abertas com itens → lista retorna ambas com qtd_itens correto."""
    garcom = _criar_garcom(c)
    item = _criar_item(c)

    comanda1 = _abrir_comanda(c, garcom["id"], identificacao="Mesa 1")
    _lancar_item(c, comanda1["id"], item["id"], comanda1["version"], quantidade=2)

    comanda2 = _abrir_comanda(c, garcom["id"], identificacao="Mesa 2")
    r = _lancar_item(c, comanda2["id"], item["id"], comanda2["version"], quantidade=1)
    _lancar_item(c, comanda2["id"], item["id"], r["version"], quantidade=1)

    resp = c.get("/api/dashboard")
    assert resp.status_code == 200, resp.text
    data = resp.json()

    lista = data["comandas_abertas_lista"]
    assert len(lista) == 2
    assert data["comandas_abertas"] == 2

    by_id = {c_item["id"]: c_item for c_item in lista}
    assert by_id[comanda1["id"]]["qtd_itens"] == 2
    assert by_id[comanda2["id"]]["qtd_itens"] == 2


def test_dashboard_top_garcons_hoje_top_3_por_faturamento(c):
    """4 garçons fecham comandas hoje com faturamentos distintos → top_garcons_hoje
    traz só os 3 melhores, ordenados por faturamento desc."""
    item = _criar_item(c, preco="10.00")
    metodo = _criar_metodo(c)

    faturamentos = {"Ana": 40, "Bruno": 30, "Carla": 20, "Duda": 10}
    for nome, valor in faturamentos.items():
        garcom = _criar_garcom(c, nome=nome)
        comanda = _abrir_comanda(c, garcom["id"], identificacao=f"Mesa {nome}")
        r = _lancar_item(c, comanda["id"], item["id"], comanda["version"], quantidade=valor // 10)
        _fechar(c, comanda["id"], metodo["id"], f"{valor}.00", r["version"])

    resp = c.get("/api/dashboard")
    assert resp.status_code == 200, resp.text
    top = resp.json()["top_garcons_hoje"]

    assert len(top) == 3
    assert [g["garcom_nome"] for g in top] == ["Ana", "Bruno", "Carla"]
    assert float(top[0]["faturamento"]) == pytest.approx(40.0)


def test_dashboard_perdas_cortesias_mes(c):
    """2 baixas-sem-venda com motivos distintos no mês corrente → total e breakdown
    por motivo aparecem em perdas_cortesias_mes_total/_por_motivo."""
    insumo = _criar_insumo(c, nome="Insumo Perda")
    _set_custo_medio(insumo["id"], Decimal("3.00"))

    _baixa_sem_venda(c, insumo["id"], "2", "perda")
    _baixa_sem_venda(c, insumo["id"], "1", "quebra")

    resp = c.get("/api/dashboard")
    assert resp.status_code == 200, resp.text
    data = resp.json()

    assert float(data["perdas_cortesias_mes_total"]) == pytest.approx(9.0)  # 2*3 + 1*3
    motivos = {g["motivo"]: float(g["valor"]) for g in data["perdas_cortesias_mes_por_motivo"]}
    assert motivos["perda"] == pytest.approx(6.0)
    assert motivos["quebra"] == pytest.approx(3.0)


def test_dashboard_comissoes_a_pagar(c):
    """Comanda fechada com taxa_servico=True gera comissão pago=False → aparece
    em comissoes_a_pagar_total/_por_garcom."""
    garcom = _criar_garcom(c, nome="Garcom Comissionado")
    item = _criar_item(c, preco="100.00")
    metodo = _criar_metodo(c)

    comanda = _abrir_comanda(c, garcom["id"])
    r = _lancar_item(c, comanda["id"], item["id"], comanda["version"])
    resp_fechar = c.post(
        f"/api/comandas/{comanda['id']}/fechar",
        json={
            "pagamentos": [{"metodo_id": metodo["id"], "valor": "110.00"}],
            "modo_divisao": "sem_divisao",
            "taxa_servico": True,
            "version": r["version"],
        },
    )
    assert resp_fechar.status_code == 200, resp_fechar.text

    stats = c.get(f"/api/garcons/{garcom['id']}/stats").json()
    comissao_id = stats["comissoes"][0]["id"]
    _forcar_comissao_pendente(comissao_id)

    resp = c.get("/api/dashboard")
    assert resp.status_code == 200, resp.text
    data = resp.json()

    # 10% de taxa de serviço sobre 100.00 = 10.00, ainda não paga.
    assert float(data["comissoes_a_pagar_total"]) == pytest.approx(10.0)
    por_garcom = {c_item["nome"]: c_item for c_item in data["comissoes_a_pagar_por_garcom"]}
    assert "Garcom Comissionado" in por_garcom
    assert float(por_garcom["Garcom Comissionado"]["valor_pendente"]) == pytest.approx(10.0)


def test_dashboard_insumos_menor_estoque_ordenado_exclui_criticos(c):
    """6 insumos não-críticos + 1 crítico com o menor estoque de todos →
    insumos_menor_estoque traz exatamente 5, ordenados por estoque_disponivel
    asc, sem incluir o insumo crítico (que aparece só em insumos_criticos)."""
    critico = _criar_insumo(c, nome="Insumo Critico")
    _set_estoque(critico["id"], Decimal("1"), nivel_critico=Decimal("5"))

    nomes_nao_criticos = []
    for i, estoque in enumerate([50, 40, 30, 20, 10, 60]):
        insumo = _criar_insumo(c, nome=f"Insumo NC{i}")
        _set_estoque(insumo["id"], Decimal(str(estoque)))
        nomes_nao_criticos.append((insumo["nome"], estoque))

    resp = c.get("/api/dashboard")
    assert resp.status_code == 200, resp.text
    data = resp.json()

    criticos_nomes = {i["nome"] for i in data["insumos_criticos"]}
    assert "Insumo Critico" in criticos_nomes

    menor_estoque = data["insumos_menor_estoque"]
    assert len(menor_estoque) == 5
    nomes_menor_estoque = [i["nome"] for i in menor_estoque]
    assert "Insumo Critico" not in nomes_menor_estoque

    esperado_ordem = [n for n, _ in sorted(nomes_nao_criticos, key=lambda t: t[1])][:5]
    assert nomes_menor_estoque == esperado_ordem


def test_dashboard_top_10_produtos_por_faturamento_com_cmv(c):
    """Produto de menor quantidade mas maior faturamento aparece antes na lista
    (prova que a ordenação mudou de quantidade para faturamento); produto sem
    ficha técnica recebe classificacao_cmv="sem_custo" e cmv_percentual=None."""
    insumo = _criar_insumo(c, nome="Insumo Top10")
    _set_custo_medio(insumo["id"], Decimal("2.00"))
    metodo = _criar_metodo(c)
    garcom = _criar_garcom(c)

    produto_a = c.post(
        "/api/produtos",
        json={
            "nome": "AltaQtdBaixoFaturamento",
            "preco_venda": "10.00",
            "ficha_tecnica": [{"insumo_id": insumo["id"], "quantidade": "1"}],
        },
    ).json()
    produto_b = c.post(
        "/api/produtos",
        json={
            "nome": "BaixaQtdAltoFaturamento",
            "preco_venda": "100.00",
            "ficha_tecnica": [{"insumo_id": insumo["id"], "quantidade": "1"}],
        },
    ).json()
    produto_c = _criar_item(c, nome="SemFichaTecnica", preco="30.00")

    comanda = _abrir_comanda(c, garcom["id"])
    v = comanda["version"]
    r = _lancar_item(c, comanda["id"], produto_a["id"], v, quantidade=5)
    v = r["version"]
    r = _lancar_item(c, comanda["id"], produto_b["id"], v, quantidade=1)
    v = r["version"]
    r = _lancar_item(c, comanda["id"], produto_c["id"], v, quantidade=1)
    _fechar(c, comanda["id"], metodo["id"], "180.00", r["version"])

    resp = c.get("/api/dashboard")
    assert resp.status_code == 200, resp.text
    top = resp.json()["top_10_produtos"]

    nomes = [p["nome"] for p in top[:3]]
    assert nomes == ["BaixaQtdAltoFaturamento", "AltaQtdBaixoFaturamento", "SemFichaTecnica"]

    by_nome = {p["nome"]: p for p in top}
    assert by_nome["BaixaQtdAltoFaturamento"]["cmv_percentual"] == pytest.approx(2.0)
    assert by_nome["BaixaQtdAltoFaturamento"]["classificacao_cmv"] == "verde"
    assert by_nome["AltaQtdBaixoFaturamento"]["cmv_percentual"] == pytest.approx(20.0)
    assert by_nome["SemFichaTecnica"]["cmv_percentual"] is None
    assert by_nome["SemFichaTecnica"]["classificacao_cmv"] == "sem_custo"


# ---------------------------------------------------------------------------
# Regressão: agregações de dashboard_repository via GROUP BY em SQL
# (caracterizam o comportamento atual antes/depois de trocar loop Python por
# GROUP BY/func.sum no SQLAlchemy — devem continuar batendo byte-a-byte).
# ---------------------------------------------------------------------------


def _comanda_fechada(db: Session, dt_utc: datetime.datetime, total: str, identificacao="Mesa X"):
    from src.models.comandas import Comanda, StatusComanda

    comanda = Comanda(
        tenant_id=1,
        identificacao=identificacao,
        tipo_identificacao="mesa",
        garcom_id=1,
        status=StatusComanda.FECHADA.value,
        total=Decimal(total),
        data_fechamento=dt_utc,
    )
    db.add(comanda)
    db.flush()
    return comanda


def _compra(db: Session, data_compra: datetime.date, total: str):
    from src.models.compras import Compra

    compra = Compra(tenant_id=1, data_compra=data_compra, total=Decimal(total), status="confirmado")
    db.add(compra)
    db.flush()
    return compra


def test_faturamento_ultimos_30d_agrega_por_dia_local():
    from zoneinfo import ZoneInfo

    from src.repositories import dashboard_repository as dr

    TZ = ZoneInfo("America/Sao_Paulo")
    today_sp = datetime.datetime.now(TZ).date()

    db: Session = _TestingSession()
    try:
        # Duas comandas no mesmo dia local de hoje (23:00 UTC = 20:00 SP e 02:00 UTC = 23:00 SP do dia anterior em UTC)
        _comanda_fechada(db, datetime.datetime(today_sp.year, today_sp.month, today_sp.day, 23, 0, 0), "40.00")
        # Comanda 29 dias atrás (limite inferior da janela) às 03:00 UTC local (~00:00 SP)
        d_29 = today_sp - datetime.timedelta(days=29)
        _comanda_fechada(db, datetime.datetime(d_29.year, d_29.month, d_29.day, 3, 0, 1), "10.00")
        # Comanda fora da janela (31 dias atrás) — não deve aparecer em nenhum bucket
        d_fora = today_sp - datetime.timedelta(days=31)
        _comanda_fechada(db, datetime.datetime(d_fora.year, d_fora.month, d_fora.day, 12, 0, 0), "999.00")
        db.commit()

        result = dr.faturamento_ultimos_30d(db)

        assert len(result) == 30
        assert result[0]["data"] == d_29
        assert result[-1]["data"] == today_sp
        by_date = {r["data"]: r["faturamento"] for r in result}
        assert by_date[today_sp] == Decimal("40.00")
        assert by_date[d_29] == Decimal("10.00")
        total_geral = sum(by_date.values(), Decimal("0"))
        assert total_geral == Decimal("50.00")
    finally:
        db.close()


def test_heatmap_mes_atual_agrega_por_dia_do_mes():
    from zoneinfo import ZoneInfo

    from src.repositories import dashboard_repository as dr

    TZ = ZoneInfo("America/Sao_Paulo")
    today_sp = datetime.datetime.now(TZ).date()
    primeiro = datetime.date(today_sp.year, today_sp.month, 1)

    db: Session = _TestingSession()
    try:
        _comanda_fechada(db, datetime.datetime(primeiro.year, primeiro.month, primeiro.day, 15, 0, 0), "25.00")
        _comanda_fechada(db, datetime.datetime(today_sp.year, today_sp.month, today_sp.day, 15, 0, 0), "35.00")
        db.commit()

        result = dr.heatmap_mes_atual(db)

        by_date = {r["data"]: r["faturamento"] for r in result}
        assert by_date[primeiro] == Decimal("25.00")
        assert by_date[today_sp] == Decimal("35.00")
        assert result[0]["data"] == primeiro
    finally:
        db.close()


def test_historico_periodo_agrega_faturamento_e_compras():
    from src.repositories import dashboard_repository as dr

    db: Session = _TestingSession()
    try:
        inicio = datetime.date(2025, 3, 1)
        fim = datetime.date(2025, 3, 5)
        # dentro do período (03/03 às 14:00 UTC = 11:00 SP)
        _comanda_fechada(db, datetime.datetime(2025, 3, 3, 14, 0, 0), "70.00")
        # exatamente na fronteira final (05/03 às 23:59 SP = 06/03 02:59 UTC)
        _comanda_fechada(db, datetime.datetime(2025, 3, 6, 2, 59, 0), "30.00")
        # fora do período (06/03 04:00 UTC = 01:00 SP do dia 06 -> fora)
        _comanda_fechada(db, datetime.datetime(2025, 3, 6, 4, 0, 0), "999.00")
        _compra(db, datetime.date(2025, 3, 3), "15.00")
        _compra(db, datetime.date(2025, 3, 3), "5.00")
        db.commit()

        result = dr.historico_periodo(db, inicio, fim)

        assert [r["data"] for r in result] == [
            datetime.date(2025, 3, d) for d in range(1, 6)
        ]
        by_date = {r["data"]: r for r in result}
        assert by_date[datetime.date(2025, 3, 3)]["faturamento"] == Decimal("70.00")
        assert by_date[datetime.date(2025, 3, 3)]["total_compras"] == Decimal("20.00")
        assert by_date[datetime.date(2025, 3, 5)]["faturamento"] == Decimal("30.00")
        assert by_date[datetime.date(2025, 3, 1)]["faturamento"] == Decimal("0")
        assert by_date[datetime.date(2025, 3, 1)]["total_compras"] == Decimal("0")
    finally:
        db.close()


def test_resumo_anual_agrega_por_mes():
    from src.repositories import dashboard_repository as dr

    db: Session = _TestingSession()
    try:
        _comanda_fechada(db, datetime.datetime(2025, 1, 15, 14, 0, 0), "100.00")
        _comanda_fechada(db, datetime.datetime(2025, 6, 15, 14, 0, 0), "200.00")
        # fronteira: 31/12 23:59 SP = 01/01/2026 02:59 UTC — não deve entrar em 2025
        _comanda_fechada(db, datetime.datetime(2026, 1, 1, 2, 59, 0), "50.00")
        _compra(db, datetime.date(2025, 1, 10), "40.00")
        _compra(db, datetime.date(2025, 6, 20), "60.00")
        db.commit()

        result = dr.resumo_anual(db, 2025)

        assert len(result) == 12
        by_mes = {r["mes"]: r for r in result}
        assert by_mes[1]["faturamento"] == Decimal("100.00")
        assert by_mes[1]["total_compras"] == Decimal("40.00")
        assert by_mes[6]["faturamento"] == Decimal("200.00")
        assert by_mes[6]["total_compras"] == Decimal("60.00")
        assert by_mes[2]["faturamento"] == Decimal("0")
        assert by_mes[2]["total_compras"] == Decimal("0")
    finally:
        db.close()


def test_faturamento_mes_soma_periodo():
    from src.repositories import dashboard_repository as dr

    db: Session = _TestingSession()
    try:
        _comanda_fechada(db, datetime.datetime(2025, 4, 10, 14, 0, 0), "100.00")
        _comanda_fechada(db, datetime.datetime(2025, 4, 20, 14, 0, 0), "50.00")
        _comanda_fechada(db, datetime.datetime(2025, 5, 1, 14, 0, 0), "999.00")
        db.commit()

        assert dr.faturamento_mes(db, 2025, 4) == Decimal("150.00")
        assert dr.faturamento_mes(db, 2025, 3) == Decimal("0")
    finally:
        db.close()


def test_faturamento_por_hora_hoje_agrega_por_hora_local():
    from zoneinfo import ZoneInfo

    from src.repositories import dashboard_repository as dr

    TZ = ZoneInfo("America/Sao_Paulo")
    today_sp = datetime.datetime.now(TZ).date()

    db: Session = _TestingSession()
    try:
        c1 = _comanda_fechada(db, datetime.datetime(today_sp.year, today_sp.month, today_sp.day, 23, 0, 0), "50.00")
        c2 = _comanda_fechada(db, datetime.datetime(today_sp.year, today_sp.month, today_sp.day, 23, 30, 0), "25.00")
        db.commit()

        result = dr.faturamento_por_hora_hoje(db, [c1.id, c2.id])

        assert len(result) == 24
        by_hora = {r["hora"]: r["faturamento"] for r in result}
        assert by_hora[20] == Decimal("75.00")
        assert by_hora[23] == Decimal("0")
    finally:
        db.close()

