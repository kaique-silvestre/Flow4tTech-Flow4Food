# PRP — Issue #11: Relatórios financeiros

**Parent PRD:** `docs/prd_matchpoint_mvp.md`
**Parent Issue:** `docs/issues_matchpoint_mvp.md` → Issue 11
**Documento mestre:** `docs/matchpoint_documentacao.md` §8.7.4–8.7.7
**Type:** AFK
**Status:** Em andamento
**Criado em:** 2026-05-08
**Depende de:** Issue #7 (Fechamento) — concluída

---

## Objetivo

Quatro relatórios gerenciais com regras de negócio específicas:

- `GET /api/relatorios/dre?mes=YYYY-MM` — DRE simplificado (mensal).
- `GET /api/relatorios/cmv-por-produto` — CMV de todos os vendáveis com classificação por margem.
- `GET /api/relatorios/perdas-cortesias?data_inicio=&data_fim=` — baixas sem venda + cortesias de comandas, agrupadas por motivo.
- `GET /api/relatorios/vendas-por-garcom?data_inicio=&data_fim=` — ranking por garçom da abertura.
- FE: 4 telas com filtros + tabela/cards.
- Testes: 5 cenários cobrindo regras de negócio.

---

## Regras de Negócio Críticas

- **Cortesias** (`ItemComanda.cortesia=True`): têm `preco_unitario=0` (não geram receita), mas entram no CMV via `Item.custo_medio * quantidade`.
- **faturamento_bruto** (DRE) = `sum(comanda.total + desconto_valor)` — valor pré-desconto, excluindo cortesias (que têm preco=0).
- **cortesias_valor** (DRE) = `sum(Item.preco_venda * ItemComanda.quantidade WHERE cortesia=True, cancelado=False)` — receita perdida por cortesias (join ItemComanda → Item).
- **faturamento_liquido** = `faturamento_bruto - descontos - cortesias_valor`.
- **CMV** = `sum(Item.custo_medio * ItemComanda.quantidade WHERE cancelado=False)` — inclui itens de cortesia.
- **Perdas** (DRE) = `sum(MovimentoEstoque.quantidade * custo_unitario WHERE tipo=SAIDA_PERDA)` no período.
- **Produtos sem custo** = itens que aparecem em itens_comanda no período mas têm `Item.custo_medio=NULL`.
- **Garçom em vendas-por-garcom** = `Comanda.garcom_id` (garçom da abertura, não do fechamento).
- **Classificação CMV**: verde `> 40%`, amarelo `20–40%`, vermelho `< 20%`, `sem_custo` se `custo_medio=NULL`.
- `margem_percentual = (preco_venda - custo_medio) / preco_venda * 100`.

---

## Estrutura de Arquivos a Criar/Modificar

```
backend/
  src/
    schemas/
      relatorio_schemas.py            # (modificar) adicionar 4 novos schemas
    repositories/
      relatorio_repository.py         # (modificar) adicionar queries para os 4 relatórios
    services/
      relatorio_service.py            # (modificar) adicionar 4 funções de serviço
    api/
      routes/
        relatorios.py                 # (modificar) adicionar 4 endpoints

  tests/
    test_relatorios_financeiros.py    # (criar) 5 testes

frontend/
  src/
    features/
      relatorios/
        useRelatorios.ts              # (modificar) adicionar 4 hooks
        DrePage.tsx                   # (criar)
        CmvPorProdutoPage.tsx         # (criar)
        PerdasCortesiasPage.tsx       # (criar)
        VendasPorGarcomPage.tsx       # (criar)
    App.tsx                           # (modificar) 4 novas rotas
```

---

## Tarefas

### Bloco A — Schemas (backend)

- [ ] **A1.** Adicionar ao `backend/src/schemas/relatorio_schemas.py`:

```python
class ItemSemCusto(BaseModel):
    item_id: int
    nome: str


class DREResponse(BaseModel):
    mes: str  # "2026-05"
    faturamento_bruto: Decimal
    descontos: Decimal
    cortesias_valor: Decimal
    faturamento_liquido: Decimal
    cmv: Decimal
    perdas: Decimal
    total_custos: Decimal
    lucro_bruto: Decimal
    margem_percentual: Decimal
    produtos_sem_custo: list[ItemSemCusto]


class CMVProdutoItem(BaseModel):
    item_id: int
    nome: str
    preco_venda: Optional[Decimal]
    custo_medio: Optional[Decimal]
    margem_valor: Optional[Decimal]
    margem_percentual: Optional[Decimal]
    classificacao: str  # "verde" | "amarelo" | "vermelho" | "sem_custo"


class CMVPorProdutoResponse(BaseModel):
    itens: list[CMVProdutoItem]


class PerdasGrupo(BaseModel):
    motivo: str
    qtd_movimentos: int
    total_valor: Decimal


class PerdasCortesiasResponse(BaseModel):
    data_inicio: datetime.date
    data_fim: datetime.date
    total_geral: Decimal
    grupos: list[PerdasGrupo]


class VendasGarcomItem(BaseModel):
    garcom_id: int
    garcom_nome: str
    qtd_comandas: int
    faturamento: Decimal
    ticket_medio: Decimal


class VendasPorGarcomResponse(BaseModel):
    data_inicio: datetime.date
    data_fim: datetime.date
    garcons: list[VendasGarcomItem]
```

---

### Bloco B — Repository (backend)

- [ ] **B1.** Adicionar ao `backend/src/repositories/relatorio_repository.py`:

```python
from src.models.itens import Item
from src.models.movimentos_estoque import MovimentoEstoque, TipoMovimento


def _month_utc_range(mes: str) -> tuple[datetime.datetime, datetime.datetime]:
    """mes='YYYY-MM' → range UTC naive do primeiro ao último dia do mês."""
    year, month = int(mes[:4]), int(mes[5:7])
    first = datetime.date(year, month, 1)
    if month == 12:
        last = datetime.date(year + 1, 1, 1) - datetime.timedelta(days=1)
    else:
        last = datetime.date(year, month + 1, 1) - datetime.timedelta(days=1)
    return _day_utc_range(first)[0], _day_utc_range(last)[1]


def cmv_total(db: Session, comanda_ids: list[int]) -> Decimal:
    """Soma custo_medio * quantidade para todos itens não cancelados das comandas."""
    if not comanda_ids:
        return Decimal("0")
    row = db.execute(
        select(func.sum(Item.custo_medio * ItemComanda.quantidade))
        .join(Item, ItemComanda.item_id == Item.id)
        .where(
            ItemComanda.comanda_id.in_(comanda_ids),
            ItemComanda.cancelado.is_(False),
            Item.custo_medio.isnot(None),
        )
    ).scalar()
    return row or Decimal("0")


def cortesias_valor_total(db: Session, comanda_ids: list[int]) -> Decimal:
    """Soma Item.preco_venda * quantidade para itens cortesia (receita perdida)."""
    if not comanda_ids:
        return Decimal("0")
    row = db.execute(
        select(func.sum(Item.preco_venda * ItemComanda.quantidade))
        .join(Item, ItemComanda.item_id == Item.id)
        .where(
            ItemComanda.comanda_id.in_(comanda_ids),
            ItemComanda.cortesia.is_(True),
            ItemComanda.cancelado.is_(False),
            Item.preco_venda.isnot(None),
        )
    ).scalar()
    return row or Decimal("0")


def perdas_no_periodo(
    db: Session, start_utc: datetime.datetime, end_utc: datetime.datetime
) -> list[dict]:
    """Retorna SAIDA_PERDA agrupado por motivo no período."""
    rows = db.execute(
        select(
            MovimentoEstoque.motivo,
            func.count(MovimentoEstoque.id).label("qtd"),
            func.sum(MovimentoEstoque.quantidade * MovimentoEstoque.custo_unitario).label("total"),
        )
        .where(
            MovimentoEstoque.tipo == TipoMovimento.SAIDA_PERDA.value,
            MovimentoEstoque.created_at >= start_utc,
            MovimentoEstoque.created_at <= end_utc,
        )
        .group_by(MovimentoEstoque.motivo)
    ).all()
    return [
        {"motivo": r.motivo or "outro", "qtd": r.qtd, "total": r.total or Decimal("0")}
        for r in rows
    ]


def perdas_total(db: Session, start_utc: datetime.datetime, end_utc: datetime.datetime) -> Decimal:
    row = db.execute(
        select(func.sum(MovimentoEstoque.quantidade * MovimentoEstoque.custo_unitario))
        .where(
            MovimentoEstoque.tipo == TipoMovimento.SAIDA_PERDA.value,
            MovimentoEstoque.created_at >= start_utc,
            MovimentoEstoque.created_at <= end_utc,
            MovimentoEstoque.custo_unitario.isnot(None),
        )
    ).scalar()
    return row or Decimal("0")


def produtos_sem_custo(db: Session, comanda_ids: list[int]) -> list[dict]:
    """Itens sem custo_medio que aparecem nas comandas do período."""
    if not comanda_ids:
        return []
    rows = db.execute(
        select(Item.id, Item.nome)
        .join(ItemComanda, ItemComanda.item_id == Item.id)
        .where(
            ItemComanda.comanda_id.in_(comanda_ids),
            ItemComanda.cancelado.is_(False),
            Item.custo_medio.is_(None),
        )
        .distinct()
    ).all()
    return [{"item_id": r.id, "nome": r.nome} for r in rows]


def todos_itens_vendaveis(db: Session) -> list:
    """Todos os itens vendáveis e ativos."""
    return db.execute(
        select(Item).where(Item.vendavel.is_(True), Item.ativo.is_(True)).order_by(Item.nome)
    ).scalars().all()


def vendas_por_garcom_periodo(
    db: Session, start_utc: datetime.datetime, end_utc: datetime.datetime
) -> list[dict]:
    """Agrupa comandas fechadas por garcom_id (garçom da abertura)."""
    rows = db.execute(
        select(
            Comanda.garcom_id,
            func.count(Comanda.id).label("qtd"),
            func.sum(Comanda.total).label("faturamento"),
        )
        .where(
            Comanda.status == StatusComanda.FECHADA.value,
            Comanda.data_fechamento >= start_utc,
            Comanda.data_fechamento <= end_utc,
        )
        .group_by(Comanda.garcom_id)
        .order_by(func.sum(Comanda.total).desc())
    ).all()
    return [
        {
            "garcom_id": r.garcom_id,
            "qtd_comandas": r.qtd,
            "faturamento": r.faturamento or Decimal("0"),
        }
        for r in rows
    ]
```

---

### Bloco C — Service (backend)

- [ ] **C1.** Adicionar ao `backend/src/services/relatorio_service.py`:

```python
from src.schemas.relatorio_schemas import (
    CMVPorProdutoResponse,
    CMVProdutoItem,
    DREResponse,
    ItemSemCusto,
    PerdasCortesiasResponse,
    PerdasGrupo,
    VendasGarcomItem,
    VendasPorGarcomResponse,
)


def dre(db: Session, mes: str) -> DREResponse:
    start, end = rr._month_utc_range(mes)
    comandas = rr.list_fechadas_no_periodo(db, start, end)
    ids = [c.id for c in comandas]

    bruto = sum((c.total or Decimal("0") for c in comandas), Decimal("0"))
    descontos = sum((c.desconto_valor or Decimal("0") for c in comandas), Decimal("0"))
    cortesias_val = rr.cortesias_valor_total(db, ids)
    faturamento_bruto = bruto + descontos  # total pré-desconto (cortesias já são 0)
    faturamento_liquido = faturamento_bruto - descontos - cortesias_val

    cmv = rr.cmv_total(db, ids)
    perdas = rr.perdas_total(db, start, end)
    total_custos = cmv + perdas
    lucro_bruto = faturamento_liquido - total_custos
    margem = (lucro_bruto / faturamento_liquido * Decimal("100")) if faturamento_liquido > 0 else Decimal("0")

    sem_custo = [ItemSemCusto(**p) for p in rr.produtos_sem_custo(db, ids)]

    return DREResponse(
        mes=mes,
        faturamento_bruto=faturamento_bruto,
        descontos=descontos,
        cortesias_valor=cortesias_val,
        faturamento_liquido=faturamento_liquido,
        cmv=cmv,
        perdas=perdas,
        total_custos=total_custos,
        lucro_bruto=lucro_bruto,
        margem_percentual=margem.quantize(Decimal("0.01")),
        produtos_sem_custo=sem_custo,
    )


def cmv_por_produto(db: Session) -> CMVPorProdutoResponse:
    itens = rr.todos_itens_vendaveis(db)
    resultado = []
    for item in itens:
        if item.custo_medio is None or item.preco_venda is None:
            resultado.append(
                CMVProdutoItem(
                    item_id=item.id,
                    nome=item.nome,
                    preco_venda=item.preco_venda,
                    custo_medio=item.custo_medio,
                    margem_valor=None,
                    margem_percentual=None,
                    classificacao="sem_custo",
                )
            )
        else:
            margem_val = item.preco_venda - item.custo_medio
            margem_pct = (margem_val / item.preco_venda * Decimal("100")).quantize(Decimal("0.01"))
            if margem_pct > Decimal("40"):
                classif = "verde"
            elif margem_pct >= Decimal("20"):
                classif = "amarelo"
            else:
                classif = "vermelho"
            resultado.append(
                CMVProdutoItem(
                    item_id=item.id,
                    nome=item.nome,
                    preco_venda=item.preco_venda,
                    custo_medio=item.custo_medio,
                    margem_valor=margem_val,
                    margem_percentual=margem_pct,
                    classificacao=classif,
                )
            )
    return CMVPorProdutoResponse(itens=resultado)


def perdas_cortesias(
    db: Session, data_inicio: datetime.date, data_fim: datetime.date
) -> PerdasCortesiasResponse:
    start, _ = rr._day_utc_range(data_inicio)
    _, end = rr._day_utc_range(data_fim)
    grupos_raw = rr.perdas_no_periodo(db, start, end)
    grupos = [PerdasGrupo(motivo=g["motivo"], qtd_movimentos=g["qtd"], total_valor=g["total"]) for g in grupos_raw]
    total = sum((g.total_valor for g in grupos), Decimal("0"))
    return PerdasCortesiasResponse(
        data_inicio=data_inicio,
        data_fim=data_fim,
        total_geral=total,
        grupos=grupos,
    )


def vendas_por_garcom(
    db: Session, data_inicio: datetime.date, data_fim: datetime.date
) -> VendasPorGarcomResponse:
    start, _ = rr._day_utc_range(data_inicio)
    _, end = rr._day_utc_range(data_fim)
    rows = rr.vendas_por_garcom_periodo(db, start, end)
    garcom_ids = [r["garcom_id"] for r in rows]
    nomes = rr._garcom_names(db, garcom_ids)
    garcons = []
    for r in rows:
        fat = r["faturamento"]
        qtd = r["qtd_comandas"]
        ticket = (fat / qtd).quantize(Decimal("0.01")) if qtd > 0 else Decimal("0")
        garcons.append(
            VendasGarcomItem(
                garcom_id=r["garcom_id"],
                garcom_nome=nomes.get(r["garcom_id"], "—"),
                qtd_comandas=qtd,
                faturamento=fat,
                ticket_medio=ticket,
            )
        )
    return VendasPorGarcomResponse(
        data_inicio=data_inicio,
        data_fim=data_fim,
        garcons=garcons,
    )
```

---

### Bloco D — Routes (backend)

- [ ] **D1.** Adicionar ao `backend/src/api/routes/relatorios.py`:

```python
from src.schemas.relatorio_schemas import (
    CMVPorProdutoResponse,
    DREResponse,
    PerdasCortesiasResponse,
    VendasPorGarcomResponse,
)


@router.get("/dre", response_model=DREResponse)
def dre(
    mes: str = Query(..., description="Formato YYYY-MM"),
    db: Session = Depends(get_db),
    _user: dict = Depends(get_current_user),
) -> DREResponse:
    return relatorio_service.dre(db, mes)


@router.get("/cmv-por-produto", response_model=CMVPorProdutoResponse)
def cmv_por_produto(
    db: Session = Depends(get_db),
    _user: dict = Depends(get_current_user),
) -> CMVPorProdutoResponse:
    return relatorio_service.cmv_por_produto(db)


@router.get("/perdas-cortesias", response_model=PerdasCortesiasResponse)
def perdas_cortesias(
    data_inicio: datetime.date = Query(...),
    data_fim: datetime.date = Query(...),
    db: Session = Depends(get_db),
    _user: dict = Depends(get_current_user),
) -> PerdasCortesiasResponse:
    return relatorio_service.perdas_cortesias(db, data_inicio, data_fim)


@router.get("/vendas-por-garcom", response_model=VendasPorGarcomResponse)
def vendas_por_garcom(
    data_inicio: datetime.date = Query(...),
    data_fim: datetime.date = Query(...),
    db: Session = Depends(get_db),
    _user: dict = Depends(get_current_user),
) -> VendasPorGarcomResponse:
    return relatorio_service.vendas_por_garcom(db, data_inicio, data_fim)
```

---

### Bloco E — Tests (backend)

- [ ] **E1.** Criar `backend/tests/test_relatorios_financeiros.py` (5 testes):

  - `test_dre_produto_sem_custo_gera_alerta` — vende item com `custo_medio=None` em comanda fechada → `DREResponse.produtos_sem_custo` contém o nome do item; `cmv` = 0 para esse item.
  - `test_dre_cortesia_entra_cmv_nao_receita` — fecha comanda com 1 item normal + 1 item cortesia (tem custo_medio). Verifica: `cmv` inclui custo da cortesia; `cortesias_valor` = `preco_venda` da cortesia; `faturamento_liquido` não inclui a cortesia.
  - `test_cmv_classificacao_faixas` — GET `/api/relatorios/cmv-por-produto` com 3 itens com margens 50%, 30%, 10% → classificações verde, amarelo, vermelho respectivamente.
  - `test_perdas_agrupadas_por_motivo` — 2 movimentos SAIDA_PERDA com motivos distintos (perda, quebra) → response tem 2 grupos com totais corretos.
  - `test_vendas_por_garcom_respeita_garcom_abertura` — 2 garçons, cada um abre 1 comanda. Fechamento realizado (sem trocar garçom — comanda.garcom_id não muda). Verifica que cada garçom aparece com suas próprias comandas.

  **Padrão dos testes:** usar fixtures `client`, `db`, `auth_headers` e helper `_fechar_comanda_simples` do mesmo arquivo de testes (ou de conftest). Usar `db.execute(update(Item)...)` para setar custo_medio.

---

### Bloco F — Frontend: hooks

- [ ] **F1.** Adicionar ao `frontend/src/features/relatorios/useRelatorios.ts`:

```ts
export interface ItemSemCusto {
  item_id: number;
  nome: string;
}

export interface DREResponse {
  mes: string;
  faturamento_bruto: number;
  descontos: number;
  cortesias_valor: number;
  faturamento_liquido: number;
  cmv: number;
  perdas: number;
  total_custos: number;
  lucro_bruto: number;
  margem_percentual: number;
  produtos_sem_custo: ItemSemCusto[];
}

export interface CMVProdutoItem {
  item_id: number;
  nome: string;
  preco_venda: number | null;
  custo_medio: number | null;
  margem_valor: number | null;
  margem_percentual: number | null;
  classificacao: "verde" | "amarelo" | "vermelho" | "sem_custo";
}

export interface CMVPorProdutoResponse {
  itens: CMVProdutoItem[];
}

export interface PerdasGrupo {
  motivo: string;
  qtd_movimentos: number;
  total_valor: number;
}

export interface PerdasCortesiasResponse {
  data_inicio: string;
  data_fim: string;
  total_geral: number;
  grupos: PerdasGrupo[];
}

export interface VendasGarcomItem {
  garcom_id: number;
  garcom_nome: string;
  qtd_comandas: number;
  faturamento: number;
  ticket_medio: number;
}

export interface VendasPorGarcomResponse {
  data_inicio: string;
  data_fim: string;
  garcons: VendasGarcomItem[];
}

export function useDRE(mes: string) {
  return useQuery<DREResponse>({
    queryKey: ["relatorios", "dre", mes],
    queryFn: () =>
      api.get<DREResponse>("/api/relatorios/dre", { params: { mes } }).then((r) => r.data),
    enabled: !!mes,
  });
}

export function useCMVPorProduto() {
  return useQuery<CMVPorProdutoResponse>({
    queryKey: ["relatorios", "cmv-por-produto"],
    queryFn: () =>
      api.get<CMVPorProdutoResponse>("/api/relatorios/cmv-por-produto").then((r) => r.data),
  });
}

export function usePerdasCortesias(params: { data_inicio: string; data_fim: string }) {
  return useQuery<PerdasCortesiasResponse>({
    queryKey: ["relatorios", "perdas-cortesias", params],
    queryFn: () =>
      api
        .get<PerdasCortesiasResponse>("/api/relatorios/perdas-cortesias", { params })
        .then((r) => r.data),
    enabled: !!params.data_inicio && !!params.data_fim,
  });
}

export function useVendasPorGarcom(params: { data_inicio: string; data_fim: string }) {
  return useQuery<VendasPorGarcomResponse>({
    queryKey: ["relatorios", "vendas-por-garcom", params],
    queryFn: () =>
      api
        .get<VendasPorGarcomResponse>("/api/relatorios/vendas-por-garcom", { params })
        .then((r) => r.data),
    enabled: !!params.data_inicio && !!params.data_fim,
  });
}
```

---

### Bloco G — Frontend: DrePage.tsx

- [ ] **G1.** Criar `frontend/src/features/relatorios/DrePage.tsx`:
  - Filtro: `mes` (input type="month", default = mês atual `YYYY-MM`).
  - Chama `useDRE(mes)`.
  - Seção RECEITA: Faturamento Bruto, (-) Descontos, (-) Cortesias, Faturamento Líquido.
  - Seção CUSTOS: CMV, Perdas/Quebras, Total Custos.
  - Resultado: Lucro Bruto + Margem% (destaque em verde se positivo, vermelho se negativo).
  - Alerta amarelo no topo se `produtos_sem_custo.length > 0`: "X produto(s) sem custo cadastrado — CMV pode estar subestimado." + lista dos nomes.
  - Loading skeleton; empty state se não há dados.

---

### Bloco H — Frontend: CmvPorProdutoPage.tsx

- [ ] **H1.** Criar `frontend/src/features/relatorios/CmvPorProdutoPage.tsx`:
  - Sem filtros (dados atuais do catálogo).
  - Chama `useCMVPorProduto()`.
  - Tabela: Produto | Preço Venda | Custo Médio | Margem R$ | Margem % | Classificação.
  - Coluna Classificação: badge colorido (verde/amarelo/vermelho/cinza para sem_custo).
  - Legenda de cores abaixo da tabela.
  - Loading skeleton.

---

### Bloco I — Frontend: PerdasCortesiasPage.tsx

- [ ] **I1.** Criar `frontend/src/features/relatorios/PerdasCortesiasPage.tsx`:
  - Filtros: `data_inicio` (default = hoje − 30 dias), `data_fim` (default = hoje).
  - Chama `usePerdasCortesias(filters)`.
  - Card total geral no topo.
  - Tabela: Motivo | Qtd Movimentos | Total Valor.
  - Tradução dos motivos: consumo_interno → "Consumo Interno", perda → "Perda", quebra → "Quebra", cortesia → "Cortesia (Baixa)", outro → "Outro".
  - Empty state se sem grupos.

---

### Bloco J — Frontend: VendasPorGarcomPage.tsx

- [ ] **J1.** Criar `frontend/src/features/relatorios/VendasPorGarcomPage.tsx`:
  - Filtros: `data_inicio` (default = hoje − 30 dias), `data_fim` (default = hoje).
  - Chama `useVendasPorGarcom(filters)`.
  - Tabela ranking: # | Garçom | Qtd Comandas | Faturamento | Ticket Médio.
  - Faturamento total no rodapé da tabela.
  - Empty state se sem dados.

---

### Bloco K — App.tsx

- [ ] **K1.** `frontend/src/App.tsx` — adicionar imports e 4 rotas:

```tsx
import { DrePage } from "@/features/relatorios/DrePage";
import { CmvPorProdutoPage } from "@/features/relatorios/CmvPorProdutoPage";
import { PerdasCortesiasPage } from "@/features/relatorios/PerdasCortesiasPage";
import { VendasPorGarcomPage } from "@/features/relatorios/VendasPorGarcomPage";

// Dentro de <Route element={<AppLayout />}>:
<Route path="/relatorios/dre" element={<DrePage />} />
<Route path="/relatorios/cmv" element={<CmvPorProdutoPage />} />
<Route path="/relatorios/perdas-cortesias" element={<PerdasCortesiasPage />} />
<Route path="/relatorios/vendas-por-garcom" element={<VendasPorGarcomPage />} />
```

---

## Validações

### Backend
```bash
cd backend
ruff check .
mypy src/
pytest tests/test_relatorios_financeiros.py -v
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

- [ ] `GET /api/relatorios/dre?mes=YYYY-MM` calcula DRE com todos os campos corretos.
- [ ] DRE retorna `produtos_sem_custo` quando houver itens sem custo_medio no período.
- [ ] `GET /api/relatorios/cmv-por-produto` classifica itens em verde/amarelo/vermelho/sem_custo.
- [ ] `GET /api/relatorios/perdas-cortesias` agrupa SAIDA_PERDA por motivo com totais.
- [ ] `GET /api/relatorios/vendas-por-garcom` usa garçom da abertura (Comanda.garcom_id).
- [ ] Cortesia entra no CMV mas não em receita (faturamento_liquido).
- [ ] Testes: 5 cenários passando.
- [ ] FE: 4 telas acessíveis e funcionais.
- [ ] FE: DrePage exibe alerta amarelo quando `produtos_sem_custo` não vazio.

---

## Notas Importantes

- **cortesia preco_unitario=0**: quando item é lançado como cortesia, `preco_unitario = 0`. Para calcular `cortesias_valor` (receita perdida no DRE), fazer JOIN com `Item.preco_venda`.
- **faturamento_bruto vs comanda.total**: `comanda.total = subtotal_sem_cortesias - desconto`. Logo `faturamento_bruto = sum(comanda.total + comanda.desconto_valor)`.
- **custo_unitario nullable em MovimentoEstoque**: usar `custo_unitario.isnot(None)` no WHERE para somar perdas.
- **month range**: implementar `_month_utc_range` usando `datetime.date` e `_day_utc_range` existente.
- **Decimal precision**: usar `.quantize(Decimal("0.01"))` em `margem_percentual` e `ticket_medio`.
- **Python 3.9**: `Optional[X]` não `X | None`.
- **Imports novos no relatorio_repository.py**: adicionar `Item`, `MovimentoEstoque`, `TipoMovimento` ao bloco de imports existente.
