# PRP — Issue #12: Dashboard

**Parent PRD:** `docs/prd_matchpoint_mvp.md`
**Parent Issue:** `docs/issues_matchpoint_mvp.md` → Issue 12
**Documento mestre:** `docs/matchpoint_documentacao.md` §8.2
**Type:** AFK
**Status:** Em andamento
**Criado em:** 2026-05-08
**Depende de:** Issue #7 (Fechamento) — concluída

---

## Objetivo

Tela inicial pós-login (`/`) com:

- `GET /api/dashboard` — resposta única com todos os indicadores.
- FE: 4 cards, 4 gráficos (Recharts), lista de comandas abertas.
- Refetch automático a cada 60s via TanStack Query.
- Loading skeleton; sem alertas pós-MVP.

---

## Regras de Negócio Críticas

- **Cards = hoje** (data local SP). Faturamento, ticket médio, comandas abertas/fechadas, lucro estimado.
- **Lucro estimado** = `faturamento_hoje − CMV_hoje` (best-effort: ignora itens sem custo_medio).
- **faturamento_hoje** = `sum(comanda.total)` das FECHADAS hoje (SP).
- **ticket_medio_hoje** = `faturamento_hoje / qtd_fechadas_hoje` (0 se sem fechamentos).
- **faturamento_por_hora**: 24 buckets (hora local SP 0–23). Bucketing feito em Python, não SQL, para evitar dependência de funções de timezone do SQLite/Postgres.
- **top_10_produtos**: últimos 30 dias, ordenado por quantidade desc, excluindo cortesias e cancelados.
- **ultimos_30_dias**: agrupado por data local SP, ordenado asc.
- **heatmap_mes**: mês corrente (SP), cada dia → faturamento (0 se sem fechamentos nesse dia).
- **comandas_abertas_lista**: status ABERTA ou REABERTA, ordenadas por `created_at asc`, `aberta_ha_minutos` calculado em Python.

---

## Estrutura de Arquivos a Criar/Modificar

```
backend/
  src/
    schemas/
      dashboard_schemas.py            # (criar)
    repositories/
      dashboard_repository.py         # (criar)
    services/
      dashboard_service.py            # (criar)
    api/
      routes/
        dashboard.py                  # (criar)
  main.py                             # (modificar) registrar router /api/dashboard

  tests/
    test_dashboard.py                 # (criar) 5 testes

frontend/
  package.json                        # recharts via npm install
  src/
    features/
      dashboard/
        useDashboard.ts               # (criar)
        DashboardPage.tsx             # (criar)
    App.tsx                           # (modificar) rota "/" → DashboardPage
```

---

## Tarefas

### Bloco A — Schemas (backend)

- [ ] **A1.** Criar `backend/src/schemas/dashboard_schemas.py`:

```python
import datetime
from decimal import Decimal

from pydantic import BaseModel


class HoraBucket(BaseModel):
    hora: int
    faturamento: Decimal


class ProdutoTop(BaseModel):
    item_id: int
    nome: str
    quantidade: int
    faturamento: Decimal


class DiaFaturamento(BaseModel):
    data: datetime.date
    faturamento: Decimal


class ComandaAbertaItem(BaseModel):
    id: int
    identificacao: str
    qtd_itens: int
    total: Decimal
    aberta_ha_minutos: int


class DashboardResponse(BaseModel):
    faturamento_hoje: Decimal
    ticket_medio_hoje: Decimal
    comandas_abertas: int
    comandas_fechadas_hoje: int
    lucro_estimado_hoje: Decimal
    faturamento_por_hora: list[HoraBucket]
    top_10_produtos: list[ProdutoTop]
    ultimos_30_dias: list[DiaFaturamento]
    heatmap_mes: list[DiaFaturamento]
    comandas_abertas_lista: list[ComandaAbertaItem]
```

---

### Bloco B — Repository (backend)

- [ ] **B1.** Criar `backend/src/repositories/dashboard_repository.py`:

```python
import datetime
from decimal import Decimal
from zoneinfo import ZoneInfo

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from src.models.comandas import Comanda, StatusComanda
from src.models.itens import Item
from src.models.itens_comanda import ItemComanda
from src.repositories.relatorio_repository import _day_utc_range

TZ = ZoneInfo("America/Sao_Paulo")


def _today_sp() -> datetime.date:
    return datetime.datetime.now(TZ).date()


def _now_utc() -> datetime.datetime:
    return datetime.datetime.utcnow()


def _local_date(dt_utc: datetime.datetime) -> datetime.date:
    """UTC naive datetime → local SP date."""
    return dt_utc.replace(tzinfo=datetime.timezone.utc).astimezone(TZ).date()


def _local_hour(dt_utc: datetime.datetime) -> int:
    """UTC naive datetime → local SP hour (0-23)."""
    return dt_utc.replace(tzinfo=datetime.timezone.utc).astimezone(TZ).hour


def comandas_fechadas_hoje(db: Session) -> list[Comanda]:
    today = _today_sp()
    start, end = _day_utc_range(today)
    return list(
        db.execute(
            select(Comanda).where(
                Comanda.status == StatusComanda.FECHADA.value,
                Comanda.data_fechamento >= start,
                Comanda.data_fechamento <= end,
            )
        ).scalars().all()
    )


def cmv_hoje(db: Session, comanda_ids: list[int]) -> Decimal:
    if not comanda_ids:
        return Decimal("0")
    row = db.execute(
        select(func.sum(Item.custo_medio * ItemComanda.quantidade))
        .select_from(ItemComanda)
        .join(Item, ItemComanda.item_id == Item.id)
        .where(
            ItemComanda.comanda_id.in_(comanda_ids),
            ItemComanda.cancelado.is_(False),
            Item.custo_medio.isnot(None),
        )
    ).scalar()
    return row or Decimal("0")


def faturamento_por_hora_hoje(db: Session, comanda_ids: list[int]) -> list[dict]:
    """Bucketing em Python para evitar dependência de funções de timezone do banco."""
    if not comanda_ids:
        return [{"hora": h, "faturamento": Decimal("0")} for h in range(24)]
    rows = db.execute(
        select(Comanda.data_fechamento, Comanda.total).where(
            Comanda.id.in_(comanda_ids)
        )
    ).all()
    buckets = [Decimal("0")] * 24
    for r in rows:
        if r.data_fechamento:
            hora = _local_hour(r.data_fechamento)
            buckets[hora] += r.total or Decimal("0")
    return [{"hora": h, "faturamento": buckets[h]} for h in range(24)]


def top_10_produtos_30d(db: Session) -> list[dict]:
    today = _today_sp()
    end_date = today
    start_date = today - datetime.timedelta(days=29)
    start, _ = _day_utc_range(start_date)
    _, end = _day_utc_range(end_date)
    rows = db.execute(
        select(
            Item.id,
            Item.nome,
            func.sum(ItemComanda.quantidade).label("quantidade"),
            func.sum(ItemComanda.preco_unitario * ItemComanda.quantidade).label("faturamento"),
        )
        .select_from(ItemComanda)
        .join(Comanda, ItemComanda.comanda_id == Comanda.id)
        .join(Item, ItemComanda.item_id == Item.id)
        .where(
            Comanda.status == StatusComanda.FECHADA.value,
            Comanda.data_fechamento >= start,
            Comanda.data_fechamento <= end,
            ItemComanda.cancelado.is_(False),
            ItemComanda.cortesia.is_(False),
        )
        .group_by(Item.id, Item.nome)
        .order_by(func.sum(ItemComanda.quantidade).desc())
        .limit(10)
    ).all()
    return [
        {
            "item_id": r.id,
            "nome": r.nome,
            "quantidade": int(r.quantidade or 0),
            "faturamento": r.faturamento or Decimal("0"),
        }
        for r in rows
    ]


def faturamento_ultimos_30d(db: Session) -> list[dict]:
    today = _today_sp()
    start_date = today - datetime.timedelta(days=29)
    start, _ = _day_utc_range(start_date)
    _, end = _day_utc_range(today)
    rows = db.execute(
        select(Comanda.data_fechamento, Comanda.total).where(
            Comanda.status == StatusComanda.FECHADA.value,
            Comanda.data_fechamento >= start,
            Comanda.data_fechamento <= end,
        )
    ).all()
    dia_map: dict[datetime.date, Decimal] = {}
    for r in rows:
        if r.data_fechamento:
            d = _local_date(r.data_fechamento)
            dia_map[d] = dia_map.get(d, Decimal("0")) + (r.total or Decimal("0"))
    result = []
    for i in range(30):
        d = start_date + datetime.timedelta(days=i)
        result.append({"data": d, "faturamento": dia_map.get(d, Decimal("0"))})
    return result


def heatmap_mes_atual(db: Session) -> list[dict]:
    today = _today_sp()
    if today.month == 12:
        primeiro_dia_prox = datetime.date(today.year + 1, 1, 1)
    else:
        primeiro_dia_prox = datetime.date(today.year, today.month + 1, 1)
    primeiro = datetime.date(today.year, today.month, 1)
    ultimo = primeiro_dia_prox - datetime.timedelta(days=1)
    start, _ = _day_utc_range(primeiro)
    _, end = _day_utc_range(ultimo)
    rows = db.execute(
        select(Comanda.data_fechamento, Comanda.total).where(
            Comanda.status == StatusComanda.FECHADA.value,
            Comanda.data_fechamento >= start,
            Comanda.data_fechamento <= end,
        )
    ).all()
    dia_map: dict[datetime.date, Decimal] = {}
    for r in rows:
        if r.data_fechamento:
            d = _local_date(r.data_fechamento)
            dia_map[d] = dia_map.get(d, Decimal("0")) + (r.total or Decimal("0"))
    result = []
    d = primeiro
    while d <= ultimo:
        result.append({"data": d, "faturamento": dia_map.get(d, Decimal("0"))})
        d += datetime.timedelta(days=1)
    return result


def comandas_abertas_com_detalhes(db: Session) -> list[dict]:
    now_utc = _now_utc()
    comandas = list(
        db.execute(
            select(Comanda)
            .where(Comanda.status.in_([StatusComanda.ABERTA.value, StatusComanda.REABERTA.value]))
            .order_by(Comanda.created_at.asc())
        ).scalars().all()
    )
    if not comandas:
        return []
    ids = [c.id for c in comandas]
    counts_rows = db.execute(
        select(ItemComanda.comanda_id, func.count(ItemComanda.id).label("qtd"))
        .where(ItemComanda.comanda_id.in_(ids), ItemComanda.cancelado.is_(False))
        .group_by(ItemComanda.comanda_id)
    ).all()
    count_map = {r.comanda_id: r.qtd for r in counts_rows}
    result = []
    for comanda in comandas:
        delta = now_utc - comanda.created_at
        minutos = max(0, int(delta.total_seconds() / 60))
        result.append({
            "id": comanda.id,
            "identificacao": comanda.identificacao,
            "qtd_itens": count_map.get(comanda.id, 0),
            "total": comanda.total or Decimal("0"),
            "aberta_ha_minutos": minutos,
        })
    return result
```

---

### Bloco C — Service (backend)

- [ ] **C1.** Criar `backend/src/services/dashboard_service.py`:

```python
from decimal import Decimal

from sqlalchemy.orm import Session

from src.repositories import dashboard_repository as dr
from src.schemas.dashboard_schemas import (
    ComandaAbertaItem,
    DashboardResponse,
    DiaFaturamento,
    HoraBucket,
    ProdutoTop,
)


def dashboard(db: Session) -> DashboardResponse:
    fechadas_hoje = dr.comandas_fechadas_hoje(db)
    ids_hoje = [c.id for c in fechadas_hoje]

    faturamento_hoje = sum((c.total or Decimal("0") for c in fechadas_hoje), Decimal("0"))
    qtd_fechadas = len(fechadas_hoje)
    ticket_medio = (faturamento_hoje / qtd_fechadas).quantize(Decimal("0.01")) if qtd_fechadas > 0 else Decimal("0")

    cmv = dr.cmv_hoje(db, ids_hoje)
    lucro_estimado = faturamento_hoje - cmv

    hora_raw = dr.faturamento_por_hora_hoje(db, ids_hoje)
    faturamento_por_hora = [HoraBucket(**h) for h in hora_raw]

    top_raw = dr.top_10_produtos_30d(db)
    top_10 = [ProdutoTop(**p) for p in top_raw]

    dias_raw = dr.faturamento_ultimos_30d(db)
    ultimos_30 = [DiaFaturamento(**d) for d in dias_raw]

    heatmap_raw = dr.heatmap_mes_atual(db)
    heatmap = [DiaFaturamento(**d) for d in heatmap_raw]

    abertas_raw = dr.comandas_abertas_com_detalhes(db)
    abertas = dr.comandas_abertas_com_detalhes.__wrapped__(db) if hasattr(dr.comandas_abertas_com_detalhes, '__wrapped__') else abertas_raw
    abertas_lista = [ComandaAbertaItem(**a) for a in abertas_raw]
    qtd_abertas = len(abertas_lista)

    return DashboardResponse(
        faturamento_hoje=faturamento_hoje,
        ticket_medio_hoje=ticket_medio,
        comandas_abertas=qtd_abertas,
        comandas_fechadas_hoje=qtd_fechadas,
        lucro_estimado_hoje=lucro_estimado,
        faturamento_por_hora=faturamento_por_hora,
        top_10_produtos=top_10,
        ultimos_30_dias=ultimos_30,
        heatmap_mes=heatmap,
        comandas_abertas_lista=abertas_lista,
    )
```

---

### Bloco D — Routes (backend)

- [ ] **D1.** Criar `backend/src/api/routes/dashboard.py`:

```python
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from src.api.dependencies import get_current_user, get_db
from src.schemas.dashboard_schemas import DashboardResponse
from src.services import dashboard_service

router = APIRouter()


@router.get("", response_model=DashboardResponse)
def dashboard(
    db: Session = Depends(get_db),
    _user: dict = Depends(get_current_user),
) -> DashboardResponse:
    return dashboard_service.dashboard(db)
```

- [ ] **D2.** Modificar `backend/src/main.py` — adicionar router:

```python
from src.api.routes import dashboard as dashboard_routes
# ...
app.include_router(dashboard_routes.router, prefix="/api/dashboard", tags=["dashboard"])
```

---

### Bloco E — Tests (backend)

- [ ] **E1.** Criar `backend/tests/test_dashboard.py` (5 testes):

  - `test_dashboard_cards_hoje` — fecha comanda R$100 hoje → `faturamento_hoje=100`, `ticket_medio_hoje=100`, `comandas_fechadas_hoje=1`.
  - `test_dashboard_lucro_estimado` — item com custo_medio=30, preco=100 → lucro_estimado = 70.
  - `test_dashboard_faturamento_por_hora_timezone` — setar `data_fechamento` UTC à 23:00 UTC (= 20h SP) → `faturamento_por_hora[20].faturamento > 0`, `faturamento_por_hora[23].faturamento == 0`.
  - `test_dashboard_top_10_produtos` — 3 itens diferentes, quantidades distintas → lista ordenada por quantidade desc.
  - `test_dashboard_comandas_abertas_lista` — 2 comandas abertas com itens → lista retorna ambas com `qtd_itens` correto.

  **Padrão:** mesmo que `test_relatorios_financeiros.py` — fixture `c`, helpers inline, engine SQLite em memória.

  **Nota timezone no teste:** para testar o bucket de hora, usar `sqlalchemy update` para setar `data_fechamento` em UTC diretamente na DB, depois chamar `GET /api/dashboard` e verificar o bucket correto em SP.

---

### Bloco F — Frontend: install Recharts

- [ ] **F1.** `npm install recharts` no diretório `frontend/`.

  Recharts não está em package.json — instalar antes de criar os componentes.

---

### Bloco G — Frontend: useDashboard.ts

- [ ] **G1.** Criar `frontend/src/features/dashboard/useDashboard.ts`:

```ts
import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";

export interface HoraBucket {
  hora: number;
  faturamento: number;
}

export interface ProdutoTop {
  item_id: number;
  nome: string;
  quantidade: number;
  faturamento: number;
}

export interface DiaFaturamento {
  data: string;
  faturamento: number;
}

export interface ComandaAbertaItem {
  id: number;
  identificacao: string;
  qtd_itens: number;
  total: number;
  aberta_ha_minutos: number;
}

export interface DashboardData {
  faturamento_hoje: number;
  ticket_medio_hoje: number;
  comandas_abertas: number;
  comandas_fechadas_hoje: number;
  lucro_estimado_hoje: number;
  faturamento_por_hora: HoraBucket[];
  top_10_produtos: ProdutoTop[];
  ultimos_30_dias: DiaFaturamento[];
  heatmap_mes: DiaFaturamento[];
  comandas_abertas_lista: ComandaAbertaItem[];
}

export function useDashboard() {
  return useQuery<DashboardData>({
    queryKey: ["dashboard"],
    queryFn: () => api.get<DashboardData>("/api/dashboard").then((r) => r.data),
    refetchInterval: 60_000,
  });
}
```

---

### Bloco H — Frontend: DashboardPage.tsx

- [ ] **H1.** Criar `frontend/src/features/dashboard/DashboardPage.tsx`:

  - **4 cards no topo** (2×2 em mobile, 4×1 em 1280+):
    - Faturamento Hoje (`formatCurrency`)
    - Ticket Médio (`formatCurrency`)
    - Comandas: "X abertas / Y fechadas"
    - Lucro Estimado (`formatCurrency`, verde se >0, vermelho se <0)
  - **Gráfico 1 — Faturamento por Hora** (`BarChart`, eixo X = hora, eixo Y = R$, 24 barras)
  - **Gráfico 2 — Top 10 Produtos** (`BarChart` com `layout="vertical"`, eixo Y = nome, eixo X = quantidade)
  - **Gráfico 3 — Últimos 30 Dias** (`LineChart`, eixo X = data abreviada, eixo Y = R$)
  - **Gráfico 4 — Heatmap do Mês** (grid CSS 7 colunas, cada célula colorida por intensidade; sem biblioteca adicional)
  - **Lista de Comandas Abertas** — tabela simples: Identificação | Itens | Total | Há X min | botão "Abrir" → `/comandas/:id`
  - Loading: skeleton (`animate-pulse`) em todos os blocos
  - Empty state: mensagem quando sem dados

---

### Bloco I — App.tsx

- [ ] **I1.** Modificar `frontend/src/App.tsx`:

```tsx
import { DashboardPage } from "@/features/dashboard/DashboardPage";
// Substituir:
// <Route path="/" element={<PlaceholderPage />} />
// Por:
<Route path="/" element={<DashboardPage />} />
```

---

## Validações

### Backend
```bash
cd backend
ruff check .
mypy src/
pytest tests/test_dashboard.py -v
```

### Frontend
```bash
cd frontend
npm run type-check
npm run lint
npm run build
```

---

## Critérios de Aceite

- [ ] `GET /api/dashboard` retorna todos os campos em uma única chamada.
- [ ] Cards refletem dados do dia corrente (hora local SP).
- [ ] `faturamento_por_hora` tem exatamente 24 buckets (0–23), sem erro de timezone.
- [ ] `top_10_produtos` ordenado por quantidade desc, máx 10 itens, últimos 30 dias.
- [ ] `heatmap_mes` tem um entry por dia do mês corrente.
- [ ] `comandas_abertas_lista` inclui apenas ABERTA/REABERTA, com `qtd_itens` correto.
- [ ] FE: 4 cards + 4 gráficos + lista renderizam em 1280×720 sem clipping.
- [ ] FE: refetch automático a cada 60s (via `refetchInterval: 60_000`).
- [ ] FE: click em comanda abre `/comandas/:id`.
- [ ] Testes: 5 cenários passando.

---

## Notas Importantes

- **Bucketing de hora em Python**: banco usa UTC naive; converter para SP antes de agrupar. Não usar `func.extract(hour, ...)` pois depende do timezone do banco.
- **lucro_estimado**: pode ser negativo se CMV > faturamento (raro mas possível). Exibir em vermelho no FE.
- **Recharts**: instalar antes de criar componentes (`npm install recharts`). `@types/recharts` não necessário — Recharts ≥2 inclui tipos próprios.
- **Python 3.9**: `list[X]` e `dict[X, Y]` OK em type hints de corpo de função; para campos Pydantic usar `list[X]` (Python 3.9+ suporta).
- **Comanda.total**: pode ser `None` se ainda aberta. Usar `c.total or Decimal("0")`.
- **heatmap_mes** FE: calcular `max_faturamento` do array para normalizar intensidade (0–1). Usar `opacity` ou `bg-green-X` baseado em faixas.
- **Dashboard service**: remover a linha desnecessária `abertas = dr.comandas_abertas_com_detalhes.__wrapped__(db) if ...` — foi erro de rascunho. Usar só `abertas_raw`.
