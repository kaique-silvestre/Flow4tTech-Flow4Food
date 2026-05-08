# PRP — Issue #10: Relatórios operacionais

**Parent PRD:** `docs/prd_matchpoint_mvp.md`
**Parent Issue:** `docs/issues_matchpoint_mvp.md` → Issue 10
**Documento mestre:** `docs/matchpoint_documentacao.md` §8.7.1–8.7.3
**Type:** AFK
**Status:** Concluída ✓ (2026-05-08)
**Criado em:** 2026-05-08
**Depende de:** Issue #7 (Fechamento) — concluída

---

## Objetivo

Três relatórios operacionais com timezone `America/Sao_Paulo` e exportação:

- `GET /api/relatorios/vendas-do-dia` — comandas fechadas no dia atual (local).
- `GET /api/relatorios/historico-comandas` — filtros: período, garçom, busca.
- `GET /api/relatorios/fechamento-caixa?data=` — totais + quebra por método de pagamento.
- FE: 3 telas com filtros + tabela. Botão "Exportar PDF" em Fechamento de Caixa via `window.print()` (sem nova dep).
- Testes: 5 cenários cobrindo agregações, filtros, timezone, parcial não conta.

---

## Estrutura de Arquivos a Criar/Modificar

```
backend/
  src/
    schemas/
      relatorio_schemas.py                 # (criar) schemas de resposta
    repositories/
      relatorio_repository.py              # (criar) queries agregadas
    services/
      relatorio_service.py                 # (criar) lógica de negócio
    api/
      routes/
        relatorios.py                      # (criar) 3 endpoints
    main.py                                # (modificar) registrar router

  tests/
    test_relatorios.py                     # (criar) 5 testes

frontend/
  src/
    features/
      relatorios/
        useRelatorios.ts                   # (criar) 3 hooks de query
        VendasDoDiaPage.tsx                # (criar) tela vendas do dia
        HistoricoComandasPage.tsx          # (criar) tela histórico
        FechamentoCaixaPage.tsx            # (criar) tela fechamento + PDF
    App.tsx                                # (modificar) 3 novas rotas
```

---

## Tarefas

### Bloco A — Schemas

- [x] **A1.** Criar `backend/src/schemas/relatorio_schemas.py`:

```python
import datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel


class PagamentoResumo(BaseModel):
    metodo_id: int
    metodo_nome: str
    total: Decimal
    qtd: int


class ComandaRelatorioItem(BaseModel):
    id: int
    identificacao: str
    garcom_nome: str
    total: Decimal
    desconto_percentual: Optional[Decimal]
    desconto_valor: Optional[Decimal]
    cortesias: Decimal
    data_fechamento: datetime.datetime
    pagamentos: list[PagamentoResumo]


class VendasDoDiaResponse(BaseModel):
    data: datetime.date
    qtd_comandas: int
    faturamento_bruto: Decimal
    total_descontos: Decimal
    total_cortesias: Decimal
    faturamento_liquido: Decimal
    por_metodo: list[PagamentoResumo]
    comandas: list[ComandaRelatorioItem]


class HistoricoResponse(BaseModel):
    total: int
    comandas: list[ComandaRelatorioItem]


class FechamentoCaixaResponse(BaseModel):
    data: datetime.date
    qtd_comandas: int
    faturamento_bruto: Decimal
    descontos: Decimal
    cortesias: Decimal
    faturamento_liquido: Decimal
    por_metodo: list[PagamentoResumo]
```

---

### Bloco B — Repository

- [x] **B1.** Criar `backend/src/repositories/relatorio_repository.py`:

```python
import datetime
from decimal import Decimal
from typing import Optional
from zoneinfo import ZoneInfo

from sqlalchemy import select, func
from sqlalchemy.orm import Session

from src.models.comandas import Comanda, StatusComanda
from src.models.garcons import Garcom
from src.models.pagamentos import Pagamento
from src.models.metodos_pagamento import MetodoPagamento
from src.models.itens_comanda import ItemComanda

TZ = ZoneInfo("America/Sao_Paulo")


def _day_utc_range(data: datetime.date) -> tuple[datetime.datetime, datetime.datetime]:
    """Converte dia local (Sao_Paulo) para intervalo UTC sem tzinfo (naive UTC para comparar com DB)."""
    start = datetime.datetime.combine(data, datetime.time.min, tzinfo=TZ)
    end = datetime.datetime.combine(data, datetime.time.max, tzinfo=TZ)
    utc = datetime.timezone.utc
    return start.astimezone(utc).replace(tzinfo=None), end.astimezone(utc).replace(tzinfo=None)


def _build_por_metodo(db: Session, comanda_ids: list[int]) -> list[dict]:
    if not comanda_ids:
        return []
    rows = db.execute(
        select(
            MetodoPagamento.id,
            MetodoPagamento.nome,
            func.sum(Pagamento.valor).label("total"),
            func.count(Pagamento.id).label("qtd"),
        )
        .join(MetodoPagamento, Pagamento.metodo_id == MetodoPagamento.id)
        .where(Pagamento.comanda_id.in_(comanda_ids))
        .group_by(MetodoPagamento.id, MetodoPagamento.nome)
        .order_by(func.sum(Pagamento.valor).desc())
    ).all()
    return [
        {"metodo_id": r.id, "metodo_nome": r.nome, "total": r.total or Decimal("0"), "qtd": r.qtd}
        for r in rows
    ]


def _cortesias_por_comanda(db: Session, comanda_ids: list[int]) -> dict[int, Decimal]:
    if not comanda_ids:
        return {}
    rows = db.execute(
        select(
            ItemComanda.comanda_id,
            func.sum(ItemComanda.preco_unitario * ItemComanda.quantidade).label("total"),
        )
        .where(
            ItemComanda.comanda_id.in_(comanda_ids),
            ItemComanda.cortesia.is_(True),
            ItemComanda.cancelado.is_(False),
        )
        .group_by(ItemComanda.comanda_id)
    ).all()
    return {r.comanda_id: r.total or Decimal("0") for r in rows}


def _pagamentos_por_comanda(db: Session, comanda_ids: list[int]) -> dict[int, list[dict]]:
    if not comanda_ids:
        return {}
    rows = db.execute(
        select(
            Pagamento.comanda_id,
            MetodoPagamento.id,
            MetodoPagamento.nome,
            func.sum(Pagamento.valor).label("total"),
            func.count(Pagamento.id).label("qtd"),
        )
        .join(MetodoPagamento, Pagamento.metodo_id == MetodoPagamento.id)
        .where(Pagamento.comanda_id.in_(comanda_ids))
        .group_by(Pagamento.comanda_id, MetodoPagamento.id, MetodoPagamento.nome)
    ).all()
    result: dict[int, list[dict]] = {}
    for r in rows:
        result.setdefault(r.comanda_id, []).append(
            {"metodo_id": r.id, "metodo_nome": r.nome, "total": r.total or Decimal("0"), "qtd": r.qtd}
        )
    return result


def _garcom_names(db: Session, garcom_ids: list[int]) -> dict[int, str]:
    if not garcom_ids:
        return {}
    rows = db.execute(select(Garcom.id, Garcom.nome).where(Garcom.id.in_(garcom_ids))).all()
    return {r.id: r.nome for r in rows}


def list_fechadas_no_periodo(
    db: Session,
    start_utc: datetime.datetime,
    end_utc: datetime.datetime,
    garcom_id: Optional[int] = None,
    busca: Optional[str] = None,
) -> list[Comanda]:
    q = (
        db.query(Comanda)
        .filter(
            Comanda.status == StatusComanda.FECHADA.value,
            Comanda.data_fechamento >= start_utc,
            Comanda.data_fechamento <= end_utc,
        )
    )
    if garcom_id is not None:
        q = q.filter(Comanda.garcom_id == garcom_id)
    if busca:
        q = q.filter(Comanda.identificacao.ilike(f"%{busca}%"))
    return q.order_by(Comanda.data_fechamento.desc()).all()
```

---

### Bloco C — Service

- [x] **C1.** Criar `backend/src/services/relatorio_service.py`:

```python
import datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy.orm import Session

from src.repositories import relatorio_repository as rr
from src.schemas.relatorio_schemas import (
    ComandaRelatorioItem,
    FechamentoCaixaResponse,
    HistoricoResponse,
    PagamentoResumo,
    VendasDoDiaResponse,
)


def _build_comanda_items(
    comandas: list,
    garcom_names: dict[int, str],
    cortesias_map: dict[int, Decimal],
    pagamentos_map: dict[int, list[dict]],
) -> list[ComandaRelatorioItem]:
    items = []
    for c in comandas:
        pagamentos = [
            PagamentoResumo(**p) for p in pagamentos_map.get(c.id, [])
        ]
        items.append(
            ComandaRelatorioItem(
                id=c.id,
                identificacao=c.identificacao,
                garcom_nome=garcom_names.get(c.garcom_id, "—"),
                total=c.total or Decimal("0"),
                desconto_percentual=c.desconto_percentual,
                desconto_valor=c.desconto_valor,
                cortesias=cortesias_map.get(c.id, Decimal("0")),
                data_fechamento=c.data_fechamento,
                pagamentos=pagamentos,
            )
        )
    return items


def _aggregate(
    db: Session,
    comandas: list,
) -> tuple[dict, dict, dict, list[dict]]:
    ids = [c.id for c in comandas]
    garcom_names = rr._garcom_names(db, list({c.garcom_id for c in comandas}))
    cortesias_map = rr._cortesias_por_comanda(db, ids)
    pagamentos_map = rr._pagamentos_por_comanda(db, ids)
    por_metodo = rr._build_por_metodo(db, ids)
    return garcom_names, cortesias_map, pagamentos_map, por_metodo


def vendas_do_dia(db: Session) -> VendasDoDiaResponse:
    hoje = datetime.datetime.now(rr.TZ).date()
    start, end = rr._day_utc_range(hoje)
    comandas = rr.list_fechadas_no_periodo(db, start, end)
    garcom_names, cortesias_map, pagamentos_map, por_metodo = _aggregate(db, comandas)

    bruto = sum((c.total or Decimal("0")) for c in comandas)
    descontos = sum(
        (c.desconto_valor or Decimal("0")) for c in comandas
    )
    cortesias_total = sum(cortesias_map.values(), Decimal("0"))

    return VendasDoDiaResponse(
        data=hoje,
        qtd_comandas=len(comandas),
        faturamento_bruto=bruto,
        total_descontos=descontos,
        total_cortesias=cortesias_total,
        faturamento_liquido=bruto - descontos,
        por_metodo=[PagamentoResumo(**p) for p in por_metodo],
        comandas=_build_comanda_items(comandas, garcom_names, cortesias_map, pagamentos_map),
    )


def historico_comandas(
    db: Session,
    data_inicio: datetime.date,
    data_fim: datetime.date,
    garcom_id: Optional[int] = None,
    busca: Optional[str] = None,
) -> HistoricoResponse:
    start, _ = rr._day_utc_range(data_inicio)
    _, end = rr._day_utc_range(data_fim)
    comandas = rr.list_fechadas_no_periodo(db, start, end, garcom_id, busca)
    garcom_names, cortesias_map, pagamentos_map, _ = _aggregate(db, comandas)
    return HistoricoResponse(
        total=len(comandas),
        comandas=_build_comanda_items(comandas, garcom_names, cortesias_map, pagamentos_map),
    )


def fechamento_caixa(db: Session, data: datetime.date) -> FechamentoCaixaResponse:
    start, end = rr._day_utc_range(data)
    comandas = rr.list_fechadas_no_periodo(db, start, end)
    garcom_names, cortesias_map, pagamentos_map, por_metodo = _aggregate(db, comandas)

    bruto = sum((c.total or Decimal("0")) for c in comandas)
    descontos = sum((c.desconto_valor or Decimal("0")) for c in comandas)
    cortesias_total = sum(cortesias_map.values(), Decimal("0"))

    return FechamentoCaixaResponse(
        data=data,
        qtd_comandas=len(comandas),
        faturamento_bruto=bruto,
        descontos=descontos,
        cortesias=cortesias_total,
        faturamento_liquido=bruto - descontos,
        por_metodo=[PagamentoResumo(**p) for p in por_metodo],
    )
```

---

### Bloco D — Routes

- [x] **D1.** Criar `backend/src/api/routes/relatorios.py`:

```python
import datetime
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from src.api.dependencies import get_current_user, get_db
from src.schemas.relatorio_schemas import FechamentoCaixaResponse, HistoricoResponse, VendasDoDiaResponse
from src.services import relatorio_service

router = APIRouter()


@router.get("/vendas-do-dia", response_model=VendasDoDiaResponse)
def vendas_do_dia(
    db: Session = Depends(get_db),
    _user: dict = Depends(get_current_user),
) -> VendasDoDiaResponse:
    return relatorio_service.vendas_do_dia(db)


@router.get("/historico-comandas", response_model=HistoricoResponse)
def historico_comandas(
    data_inicio: datetime.date = Query(...),
    data_fim: datetime.date = Query(...),
    garcom_id: Optional[int] = Query(None),
    busca: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    _user: dict = Depends(get_current_user),
) -> HistoricoResponse:
    return relatorio_service.historico_comandas(db, data_inicio, data_fim, garcom_id, busca)


@router.get("/fechamento-caixa", response_model=FechamentoCaixaResponse)
def fechamento_caixa(
    data: datetime.date = Query(...),
    db: Session = Depends(get_db),
    _user: dict = Depends(get_current_user),
) -> FechamentoCaixaResponse:
    return relatorio_service.fechamento_caixa(db, data)
```

---

### Bloco E — Registrar Router

- [x] **E1.** `backend/src/main.py` — importar e registrar router:
  ```python
  from src.api.routes import relatorios as relatorios_routes
  # ...
  app.include_router(relatorios_routes.router, prefix="/api/relatorios", tags=["relatorios"])
  ```
  Adicionar logo após o `include_router` de `estoque`.

---

### Bloco F — Tests

- [x] **F1.** Criar `backend/tests/test_relatorios.py` (5 testes):

  - `test_vendas_do_dia_retorna_apenas_fechadas_hoje` — abre comanda, fecha, chama endpoint → aparece. Comanda aberta não aparece.
  - `test_historico_filtra_por_periodo` — fecha comanda ontem e hoje; filtro só hoje → retorna só a de hoje.
  - `test_historico_filtra_por_garcom` — 2 garçons, cada um com comanda fechada; filtro garcom_id → retorna só as dele.
  - `test_fechamento_caixa_agrega_por_metodo` — fecha comanda com 2 métodos de pagamento (PIX + Dinheiro) → `por_metodo` tem 2 entradas com totais corretos.
  - `test_parcial_nao_conta_como_fechada` — comanda em status `aberta` (pagamento parcial) → não aparece em nenhum relatório.

  **Padrão dos testes:** usar fixtures `db`, `auth_headers` existentes nos outros test files. Criar helper `_fechar_comanda_simples(client, comanda_id, metodo_id, valor)`.

---

### Bloco G — Frontend: useRelatorios.ts

- [x] **G1.** Criar `frontend/src/features/relatorios/useRelatorios.ts`:

```ts
import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";

export interface PagamentoResumo {
  metodo_id: number;
  metodo_nome: string;
  total: number;
  qtd: number;
}

export interface ComandaRelatorioItem {
  id: number;
  identificacao: string;
  garcom_nome: string;
  total: number;
  desconto_percentual: number | null;
  desconto_valor: number | null;
  cortesias: number;
  data_fechamento: string;
  pagamentos: PagamentoResumo[];
}

export interface VendasDoDiaResponse {
  data: string;
  qtd_comandas: number;
  faturamento_bruto: number;
  total_descontos: number;
  total_cortesias: number;
  faturamento_liquido: number;
  por_metodo: PagamentoResumo[];
  comandas: ComandaRelatorioItem[];
}

export interface HistoricoResponse {
  total: number;
  comandas: ComandaRelatorioItem[];
}

export interface FechamentoCaixaResponse {
  data: string;
  qtd_comandas: number;
  faturamento_bruto: number;
  descontos: number;
  cortesias: number;
  faturamento_liquido: number;
  por_metodo: PagamentoResumo[];
}

export function useVendasDoDia() {
  return useQuery<VendasDoDiaResponse>({
    queryKey: ["relatorios", "vendas-do-dia"],
    queryFn: () => api.get<VendasDoDiaResponse>("/api/relatorios/vendas-do-dia").then((r) => r.data),
  });
}

export function useHistoricoComandas(params: {
  data_inicio: string;
  data_fim: string;
  garcom_id?: number | null;
  busca?: string;
}) {
  return useQuery<HistoricoResponse>({
    queryKey: ["relatorios", "historico", params],
    queryFn: () =>
      api
        .get<HistoricoResponse>("/api/relatorios/historico-comandas", {
          params: {
            data_inicio: params.data_inicio,
            data_fim: params.data_fim,
            garcom_id: params.garcom_id ?? undefined,
            busca: params.busca || undefined,
          },
        })
        .then((r) => r.data),
    enabled: !!params.data_inicio && !!params.data_fim,
  });
}

export function useFechamentoCaixa(data: string) {
  return useQuery<FechamentoCaixaResponse>({
    queryKey: ["relatorios", "fechamento-caixa", data],
    queryFn: () =>
      api
        .get<FechamentoCaixaResponse>("/api/relatorios/fechamento-caixa", { params: { data } })
        .then((r) => r.data),
    enabled: !!data,
  });
}
```

---

### Bloco H — Frontend: VendasDoDiaPage.tsx

- [x] **H1.** Criar `frontend/src/features/relatorios/VendasDoDiaPage.tsx`:
  - Chama `useVendasDoDia()`.
  - Header: título "Vendas do Dia" + data atual formatada.
  - Cards de resumo: Faturamento Bruto, Descontos, Cortesias, Faturamento Líquido, Qtd Comandas.
  - Tabela por método de pagamento: Método | Total | Qtd.
  - Tabela de comandas: ID | Identificação | Garçom | Total | Desconto | Data/Hora.
  - Loading com skeleton; empty state se 0 comandas.

---

### Bloco I — Frontend: HistoricoComandasPage.tsx

- [x] **I1.** Criar `frontend/src/features/relatorios/HistoricoComandasPage.tsx`:
  - Filtros no topo: `data_inicio` (date input), `data_fim` (date input), garçom (select com `useGarcons`), busca (text).
  - Default: `data_inicio` = hoje − 7 dias, `data_fim` = hoje.
  - Chama `useHistoricoComandas(filters)`.
  - Tabela: Identificação | Garçom | Total | Desconto | Cortesias | Data/Hora.
  - Rodapé: "X comandas encontradas".

---

### Bloco J — Frontend: FechamentoCaixaPage.tsx

- [x] **J1.** Criar `frontend/src/features/relatorios/FechamentoCaixaPage.tsx`:
  - Filtro: date input `data` (default = hoje).
  - Chama `useFechamentoCaixa(data)`.
  - Layout igual ao wireframe §8.7.3:
    - Total comandas fechadas
    - Faturamento bruto
    - Descontos aplicados
    - Cortesias
    - Faturamento líquido
    - Tabela: Método | Total | Qtd
  - Botão `[EXPORTAR PDF]` → `window.print()`.
  - Adicionar `<style>` inline ou className `print:hidden` nos filtros/botão para que não apareçam no PDF impresso.
  - **Print CSS:** usar Tailwind `print:hidden` nos controles; título e dados sempre visíveis.

---

### Bloco K — App.tsx

- [x] **K1.** `frontend/src/App.tsx` — adicionar imports e 3 rotas:

```tsx
import { VendasDoDiaPage } from "@/features/relatorios/VendasDoDiaPage";
import { HistoricoComandasPage } from "@/features/relatorios/HistoricoComandasPage";
import { FechamentoCaixaPage } from "@/features/relatorios/FechamentoCaixaPage";

// Dentro de <Route element={<AppLayout />}>:
<Route path="/relatorios/vendas-do-dia" element={<VendasDoDiaPage />} />
<Route path="/relatorios/historico" element={<HistoricoComandasPage />} />
<Route path="/relatorios/fechamento-caixa" element={<FechamentoCaixaPage />} />
```

---

## Validações

### Backend
```bash
cd backend
ruff check .
mypy src/
pytest tests/test_relatorios.py -v
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

- [x] `GET /api/relatorios/vendas-do-dia` retorna comandas fechadas no dia atual (timezone `America/Sao_Paulo`).
- [x] `GET /api/relatorios/historico-comandas` filtra por período, garçom e busca.
- [x] `GET /api/relatorios/fechamento-caixa?data=` retorna totais + quebra por método.
- [x] Timezone: dia local SP → range UTC correto nas queries.
- [x] Cortesias calculadas por soma de itens com `cortesia=True` e `cancelado=False`.
- [x] Comanda com status `aberta` não aparece em nenhum relatório.
- [x] Testes: 5 cenários passando.
- [x] FE: 3 telas acessíveis e funcionais.
- [x] FE: `window.print()` no Fechamento de Caixa oculta controles na impressão (`print:hidden`).

---

## Notas Importantes

- **`zoneinfo`** (stdlib Python 3.9) para timezone — sem `pytz` (não está nas deps).
- **`window.print()`** para PDF — sem jsPDF (não está nas deps). Tailwind `print:hidden` esconde filtros.
- **Naive UTC no DB** — `data_fechamento` é stored sem tzinfo. `_day_utc_range` retorna naive UTC (`.replace(tzinfo=None)`) para comparar corretamente.
- **`por_metodo` em FechamentoCaixa** — soma pagamentos de todas as comandas fechadas do dia, não por comanda.
- **`faturamento_liquido = bruto - descontos`** — cortesias são informativas (não subtraem do líquido; são custos de CMV).
- **`useGarcons`** já existe em `features/cadastros/garcons/useGarcons.ts` — importar direto.
- **`date-fns`** já disponível — usar `format(parseISO(str), "dd/MM/yyyy HH:mm")` para datas.
- **Python 3.9**: `Optional[X]` não `X | None`.
