---
iteration: 1
max_iterations: 31
plan_path: "docs/issues/issues_matchpoint_v0.3.md"
started_at: "2026-05-11T00:00:00Z"
---

# Ralph Progress Log

## Codebase Patterns
- Backend uses `Optional[X]` (Python 3.9), not `X | None`
- Ruff UP035: use native `dict[x]`, `list[x]`, not `Dict`/`List` from typing
- Comanda.data_fechamento is UTC; use `_day_utc_range` + `_local_date` for SP timezone
- Compra.data_compra is plain `datetime.date` (already local, no UTC conversion needed)
- Frontend recharts has pre-existing TS errors (no @types/recharts) — do not fix those
- React Query queryKey pattern: `["resource", "subkey", ...params]`
- SQLite: `op.create_foreign_key` fails — just add column, skip FK constraint
- `CategoriaResponse` with recursive `children` field requires `CategoriaResponse.model_rebuild()` in Pydantic v2
- Edit tool cannot match non-ASCII whitespace (NBSP U+00A0) — use PowerShell byte-level replacement
- pytest must be run via `python -m pytest` (not `.venv\Scripts\pytest.exe`)
- Debounce pattern: `busca === "" ? clearValue : debouncedBusca` for immediate clear behavior
- Dialog component available at `@/components/ui/dialog` — use for all modals
- Controller pattern for RHF radios: `<Controller render={({ field }) => ...} />` instead of `setValue`

## Iteration 1 - 2026-05-11T00:00:00Z

### Completed
- Issue 1 (DB2): Installed `use-debounce` package
- Applied `useDebounce(busca, 350)` in ComandasPage, ComandaAbertaPage, EstoquePage, HistoricoComandasPage
- Clear-input → immediate query (busca === "" path bypasses debounce)
- Committed: bae9b34

### Validation Status
- Type-check: PASS
- Lint: PASS (0 warnings)
- Build: PASS

### Next Steps
- Issue 2 (CM1): Delete dead code — ItensPage.tsx, ItemModal.tsx, itemSchemas.ts, useItens.ts

---

## Iteration 2 - 2026-05-11T01:00:00Z

### Completed
- Issue 2 (CM1): Deleted 4 files from `frontend/src/features/cadastros/itens/`
- Zero imports found — safe to delete
- Committed: ed2e849

### Validation Status
- Type-check: PASS
- Lint: PASS
- Build: PASS

### Next Steps
- Issue 3 (EM1): Remove `reset()` from `handleClose` in `InsumoEditModal.tsx`

---

## Iteration 3 - 2026-05-11T02:00:00Z

### Completed
- Issue 3 (EM1): Removed `reset()` from `handleClose` in `InsumoEditModal.tsx`
- `useEffect([open, editing, reset])` already handles reinit — extra `reset()` caused field flash
- Committed: 3c37c61

### Validation Status
- Type-check: PASS
- Lint: PASS

### Next Steps
- Issue 4 (MOD1+NC1+NC2): `NovaComandaModal.tsx` — migrate to Dialog + valueAsNumber on mesa + radio a11y

---

## Iteration 4 - 2026-05-11T03:00:00Z

### Completed
- Issue 4 (MOD1+NC1+NC2): NovaComandaModal migrado para Dialog
- `valueAsNumber: true` aplicado em `identificacao` quando `tipo === "mesa"`
- Radios com `id="tipo-identificacao-{t}"` e `htmlFor` correspondente
- `ComandasPage.tsx` atualizado: renderização condicional → `open={showModal}` prop
- Committed: 4d6398a

### Validation Status
- Type-check: PASS
- Lint: PASS

### Next Steps
- Issue 5 (MOD1b): `CancelarItemModal.tsx` — migrar para Dialog

---

## Iteration 5 - 2026-05-11T04:00:00Z

### Completed
- Issue 5 (MOD1b): CancelarItemModal migrado para Dialog
- Adicionado `open` prop; caller atualizado com `open={!!cancelando && !!comanda}`
- Committed: 1af081b

### Validation Status
- Type-check: PASS
- Lint: PASS

### Next Steps
- Issue 6 (FE2): `modo_divisao` via Controller em FechamentoPage.tsx

---

## Iteration 6 - 2026-05-11T05:00:00Z

### Completed
- Issue 6 (FE2): modo_divisao via Controller em FechamentoPage — setValue("modo_divisao") removido
- Issues 1–6 marcadas ✅ na documentação docs/issues/issues_matchpoint_v0.3.md
- Committed: 27bed48 (FE2) + 69e200f (docs)

### Validation Status
- Type-check: PASS
- Lint: PASS

### Next Steps
- Issue 7 (FE4): Schema pagamentos coerente com total R$0 — remover .min(1), validação manual no submit

---

## Iteration 7 - 2026-05-11T06:00:00Z

### Completed
- Issue 7 (FE4): removido `.min(1)` de `fecharComandaSchema.pagamentos`
- `setError` adicionado ao useForm; `onSubmit` valida manualmente quando `baseTotal > 0 && pagamentos.length === 0`
- Doc marcada ✅
- Committed: c40fdbd + e7251af

### Validation Status
- Type-check: PASS
- Lint: PASS

### Next Steps
- Issue 8 (DE1+DE2): AplicarDescontoModal — onOpenChange correto + Controller para radio tipo

---

## Iteration 8 - 2026-05-11T07:00:00Z

### Completed
- Issue 8 (DE1+DE2): AplicarDescontoModal — onOpenChange correto + Controller para radio tipo
- `onOpenChange={(v) => !v && onClose()}` evita fechamento ao abrir
- `<Controller>` substitui radios com `setValue` manual
- `useEffect` removido — modal sempre remonta (conditional render `{descontoOpen && ...}`)
- Doc marcada ✅
- Committed: 810b1a0

### Validation Status
- Type-check: PASS
- Lint: PASS

### Next Steps
- Issue 9 (FE1+CV1): `formatQuantidade` no Fechamento e no Comprovante

---

## Iteration 9 - 2026-05-11T08:00:00Z

### Completed
- Issue 9 (FE1+CV1): `formatQuantidade` pt-BR em FechamentoPage e ComprovantePage
- `formatQuantidade` atualizado: `toLocaleString("pt-BR", { maximumFractionDigits: 3 })` → vírgula como separador decimal
- Testes atualizados: `"0.25"` → `"0,25"` etc.
- `FechamentoPage.tsx`: adicionado import + `{formatQuantidade(item.quantidade)}×`
- `ComprovantePage.tsx`: adicionado import + `{formatQuantidade(item.quantidade)}x`
- Doc marcada ✅
- Committed: ce51cb6

### Validation Status
- Type-check: PASS
- Lint: PASS

### Next Steps
- Issue 10 (FE3): Label "Última pessoa paga" no modo igualitário em FechamentoPage

---

## Iteration 10 - 2026-05-11T09:00:00Z

### Completed
- Issue 10 (FE3): label "1ª pessoa paga:" → "Última pessoa paga:" em FechamentoPage.tsx:210
- Doc marcada ✅
- Committed: ae56d59

### Validation Status
- Type-check: PASS
- Lint: PASS

### Next Steps
- Issue 11 (CA1): Select de pessoa no modo edição de item em ComandaAbertaPage

---

## Iteration 11 - 2026-05-11T10:00:00Z

### Completed
- Issue 11 (CA1): select de pessoa no edit mode de item — `<select>` quando `comanda.pessoas.length > 0`, `<Input>` senão
- Issue 12 (CA2): `useEffect`+`setInterval(60s)` em ComandaAbertaPage (só quando aberta) e ComandasPage; `minutesAgo(created_at)` substitui `tempo_aberta_minutos`
- Issue 13 (MV1+MV2): `estorno_compra` em `TIPO_OPTIONS/BADGE/LABEL`; `year: "2-digit"` no `toLocaleString` de MovimentosPage
- Issue 14 (CP4): `total_periodo` real via `SUM(total)` no repository; adicionado ao schema + service + frontend `ComprasPageResponse`; `compras.reduce` removido
- Issue 15 (CP5): filtro status Ativas/Todas/Canceladas; default "ativa"; backend aceita `status: Optional[str]`; `atualizarFiltro` reseta pagina
- Doc marcada ✅ para issues 11-15
- Committed: d3afdb7

### Validation Status
- Type-check: PASS
- Lint: PASS

### Next Steps
- Issue 16 (CP6): Modal de edição de compra com Dialog padronizado em ComprasPage

---

## Iteration 12 - 2026-05-11T11:00:00Z

### Completed
- Issue 16 (CP6): modal edição compra migrado para Dialog; `onOpenChange={(v) => !v && setEditando(null)}`
- Issue 17 (CP7): já estava implementado (toast.warning duration 6000 em useCancelarCompra) — marcado ✅
- Issue 18 (CP8): `handleItemChange(index)` no `onChange` do item selector — zera qtd, custo_total, unitarios[index], lastEditedRef
- Issue 19 (CP9): `custo_unitario = (total/qty).quantize(Decimal("0.0001"))` em compras_service
- Issue 20 (CP10): `find_by_numero_nota` no repo; check em `criar_compra`; `warning` no CompraResponse; toast.warning no frontend onSuccess
- Doc marcada ✅ issues 16-20
- Committed: 7565fe9

### Validation Status
- Type-check: PASS
- Lint: PASS

### Next Steps
- Issue 21 (CP11): Transação atômica em criar_compra e cancelar_compra

---
