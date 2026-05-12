# PRD — Ajustes e Melhorias v0.3: Sistema Matchpoint

**Versão:** 0.3
**Data:** 2026-05-11
**Status:** Aprovado para desenvolvimento
**Documentos base:** `docs/prds/prd_matchpoint_v0.0.md`, `docs/prds/prd_matchpoint_v0.1.md`, `docs/prds/prd_matchpoint_v0.2.md`, `docs/matchpoint_documentacao.md`

---

## Visão Geral

Este documento cobre correções de bugs identificados após o PRD v0.2, ajustes de usabilidade, padronização de modais, limpeza de código morto e introdução de um sistema de **conversão automática de unidades por família** para insumos. As seções são independentes salvo dependências explicitadas. Nenhuma feature nova de negócio é introduzida além do necessário para suportar o modelo de unidades.

A motivação principal do documento é resolver o problema operacional descrito pelo cliente: insumos comprados em uma unidade (ex: carne em **kg**) mas consumidos em outra (ex: ficha técnica em **g**) hoje exigem que o operador faça a conversão mentalmente ao lançar compras e fichas técnicas. O sistema introduzido nesta versão elimina essa fricção mantendo um único `unidade_base` por insumo.

---

## Índice de Itens

| ID | Área | Tipo | Descrição curta |
|----|------|------|----------------|
| UNI1 | Insumos / Compras / Ficha | Feature | Conversão automática por família (peso, volume, contagem) |
| UNI2 | Banco de dados | Migração | Reset de tabelas operacionais (insumos, compras, comandas, ficha) |
| CP4 | Compras | Bug | `totalPeriodo` calculado só com a página atual |
| CP5 | Compras | UX | Filtro de status (Todas / Ativas / Canceladas) |
| CP6 | Compras | UX | Modal de edição com `Dialog` padronizado |
| CP7 | Compras | Fix | Toast amarelo de aviso de CMV após cancelamento |
| CP8 | Compras | Bug | Reset de linha ao trocar item selecionado |
| CP9 | Compras | Bug | Custo unitário arredondado para 4 casas decimais |
| CP10 | Compras | UX | Warning amarelo ao registrar número de nota duplicado |
| CP11 | Compras | Bug | Transação atômica em `criar_compra` e `cancelar_compra` |
| CP12 | Compras | UX | Sufixo de unidade no input de quantidade |
| FT1 | Cardápio | UX | Sufixo de unidade no input de quantidade da ficha técnica |
| FE1 | Fechamento | Bug | `formatQuantidade` no resumo de itens |
| FE2 | Fechamento | Bug | `modo_divisao` migrado para `Controller` do RHF |
| FE3 | Fechamento | UX | Label "última pessoa" no modo igualitário |
| FE4 | Fechamento | Fix | Schema de pagamentos coerente com Z1 (total R$0) |
| DE1 | Fechamento | Bug | `onOpenChange` correto no modal de desconto |
| DE2 | Fechamento | Bug | Radio "percentual/valor" via `Controller` |
| CV1 | Comprovante | Bug | `formatQuantidade` no comprovante |
| NC1 | Nova Comanda | Bug | `valueAsNumber` no campo de mesa |
| NC2 | Nova Comanda | A11y | `id` + `htmlFor` nos radios `tipo_identificacao` |
| CA1 | Comanda Aberta | UX | Select de pessoa no modo edição de item |
| CA2 | Comanda Aberta | UX | Recalcular "aberta há X min" no frontend |
| MOD1 | Comanda / Compras | UX | Modais com `Dialog` padronizado |
| MV1 | Movimentos | Bug | Badge e label de `ESTORNO_COMPRA` |
| MV2 | Movimentos | UX | Exibir ano na coluna de data |
| AR1 | Navegação | Refactor | Remover `/historico` duplicado |
| AR2 | Relatórios | UX | Linhas clicáveis em `HistoricoComandasPage` |
| CD1 | Cardápio | UX | Filtro ativos / inativos / todos + botão Reativar |
| CD2 | Cardápio | UX | Busca por nome |
| VD1 | Relatórios | UX | Seletor de data em `VendasDoDiaPage` |
| VD2 | Relatórios | UX | Linhas clicáveis em `VendasDoDiaPage` |
| CG1 | Cadastros | UX | Toggle inline ativar/desativar em Garçons e Métodos |
| DB1 | Dashboard | Bug | Hooks de Histórico montados só na aba ativa |
| SB1 | Sidebar | Feature | Badge com contagem de comandas abertas |
| ES1 | Estoque | Feature | Valor total em estoque (saldo × custo médio) |
| BK1 | Configurações | UX | Nome do arquivo de backup com data |
| CM1 | Código | Limpeza | Remover `ItensPage` / `ItemModal` / `useItens` / `itemSchemas` |
| EM1 | Insumos | Bug | `reset()` consistente em `InsumoEditModal` |
| DB2 | Global | UX | Debounce de 350ms nos inputs de busca |

---

# Seção 1 — Sistema de Unidades com Conversão por Família (UNI1, UNI2)

## Problem Statement

A decisão de design U3 do PRD v0.2 estabeleceu que "o insumo é definido na unidade de uso. Compras e ficha técnica operam sempre nessa mesma unidade. Não há conversão automática entre unidades." Na prática operacional do bar, essa decisão se mostrou inviável:

- Carne bovina é comprada em **kg** (1 kg, 2 kg, 5 kg na nota fiscal) e consumida em **g** (200 g por X-Burguer na ficha técnica). Hoje, para registrar uma compra de 1 kg, o operador precisa cadastrar o insumo em `g` e lançar `1000` na quantidade — pouco intuitivo e propenso a erro.
- Refrigerante a granel é comprado em **l** (1 garrafa de 2 l, garrafão de 5 l) e usado em **ml** (300 ml por dose). Mesmo problema.
- Cerveja em caixa é comprada por **caixa** (24 unidades) e vendida por **unidade**. O campo `quantidade_caixa` existe mas é apenas informativo — não há conversão.

A consequência é que o operador precisa fazer a conversão mentalmente em todo lançamento de compra e ficha técnica, e qualquer engano leva a estoque/custo errado.

## Solution

Introduzir o conceito de **família de unidade** sem alterar o modelo de dados do insumo (mantém-se `unidade_base` único). Cada `unidade_base` pertence a uma família com conversão fixa:

| Família | Unidades | Conversão |
|---------|----------|-----------|
| Peso | `kg` ↔ `g` | 1 kg = 1000 g |
| Volume | `l` ↔ `ml` | 1 l = 1000 ml |
| Contagem | `un` ↔ `cx` (caixa) | 1 cx = `quantidade_caixa` un |

Nas telas de compra e ficha técnica, o input de quantidade ganha um **seletor lateral** com as unidades da família do insumo selecionado. O operador digita o número na unidade que preferir e o frontend converte para a `unidade_base` do insumo antes de enviar ao backend. O armazenamento permanece na `unidade_base` configurada no cadastro do insumo — backend não muda.

Para insumos `un`, a opção `cx` só aparece no seletor se `quantidade_caixa` estiver definido.

## User Stories

1. Como sócio, quero cadastrar carne com `unidade_base = kg` e usá-la na ficha técnica do X-Burguer digitando "200 g", para não precisar converter mentalmente para 0,2 kg.
2. Como sócio, quero registrar a compra de 5 caixas de Heineken digitando "5 cx" em vez de calcular 60 unidades, para reduzir erro de operação.
3. Como sistema, quero armazenar internamente sempre na `unidade_base` do insumo, para que relatórios e cálculos de CMV continuem funcionando sem alteração.

## Implementation Decisions

**Frontend — `lib/units.ts` (novo):**

```ts
export type UnidadeBase = "un" | "g" | "kg" | "ml" | "l";

export interface UnidadeOption {
  value: string;
  label: string;
  factorToBase: number;
}

export function getFamilyOptions(
  unidadeBase: UnidadeBase,
  quantidadeCaixa: number | null,
): UnidadeOption[] {
  switch (unidadeBase) {
    case "kg":
      return [
        { value: "kg", label: "kg", factorToBase: 1 },
        { value: "g", label: "g", factorToBase: 1 / 1000 },
      ];
    case "g":
      return [
        { value: "g", label: "g", factorToBase: 1 },
        { value: "kg", label: "kg", factorToBase: 1000 },
      ];
    case "l":
      return [
        { value: "l", label: "l", factorToBase: 1 },
        { value: "ml", label: "ml", factorToBase: 1 / 1000 },
      ];
    case "ml":
      return [
        { value: "ml", label: "ml", factorToBase: 1 },
        { value: "l", label: "l", factorToBase: 1000 },
      ];
    case "un":
      return quantidadeCaixa && quantidadeCaixa > 0
        ? [
            { value: "un", label: "un", factorToBase: 1 },
            { value: "cx", label: "cx", factorToBase: quantidadeCaixa },
          ]
        : [{ value: "un", label: "un", factorToBase: 1 }];
  }
}

export function toBase(value: number, option: UnidadeOption): number {
  return value * option.factorToBase;
}
```

**Frontend — `NovaCompraPage.tsx`:**

- Substituir a coluna fixa "Unidade" por um `<select>` adjacente ao input de quantidade, populado por `getFamilyOptions(item.unidade_base, item.quantidade_caixa)`.
- Estado local `unidadeSelecionada: string[]` (uma por linha), default = `unidade_base` do item escolhido.
- Ao trocar a unidade no select, manter o número digitado e atualizar o submit handler:
  ```ts
  const opt = options.find((o) => o.value === unidadeSelecionada[index]);
  const quantidadeBase = toBase(qtyDigitada, opt);
  // submit usa quantidadeBase
  ```
- O `custo_unitario` exibido segue na unidade base (R$ / unidade_base) — não muda comportamento atual.

**Frontend — `ProdutoModal.tsx` (ficha técnica):**

- Mesmo padrão: cada linha de `ficha_tecnica` ganha um seletor de unidade adjacente ao input de quantidade.
- Cálculo de CMV (`calcCmv`) já usa `custo_medio` na unidade base; ajustar para converter a quantidade digitada para a unidade base antes de multiplicar:
  ```ts
  const opt = getFamilyOptions(insumo.unidade_base, insumo.quantidade_caixa)
    .find((o) => o.value === unidadeSelecionada);
  custo += insumo.custo_medio * toBase(qty, opt);
  ```
- No payload submetido para `ficha_tecnica`, enviar sempre a quantidade convertida para `unidade_base`.

**Backend:** **nenhuma mudança**. Toda conversão acontece no frontend antes do submit. O backend continua recebendo e armazenando quantidades na `unidade_base` do insumo.

### UNI2 — Reset de Tabelas Operacionais

Como o sistema não tem usuários ativos em produção e a introdução do modelo de unidades altera a forma como dados de compra e ficha técnica são interpretados, será feito um reset das tabelas operacionais para evitar inconsistência com cadastros pré-existentes.

**Backend — nova migração Alembic:**

- `DELETE FROM` (na ordem para respeitar FKs):
  - `pagamentos`
  - `itens_comanda`
  - `comandas`
  - `movimentos_estoque`
  - `itens_compra`
  - `compras`
  - `ficha_tecnica`
  - `insumos`
- **Manter:** `usuarios`, `estabelecimento`, `categorias`, `fornecedores`, `garcons`, `metodos_pagamento`, `produtos` (cardápio — mas com ficha técnica zerada).
- Sequências de ID resetadas via `ALTER SEQUENCE ... RESTART WITH 1`.

## Testing Decisions

- **UNI1 compra em kg:** Cadastrar insumo "Carne" com `unidade_base = kg`. Registrar compra digitando "1" com seletor `kg`, total R$50. Verificar via GET que `quantidade = 1` no banco. Repetir digitando "1000" com seletor `g` — verificar `quantidade = 1`.
- **UNI1 ficha em g:** Cadastrar produto "X-Burguer" com ficha técnica de "Carne" digitando "200" com seletor `g`. Verificar via GET que `quantidade = 0.2` (em kg) no banco.
- **UNI1 caixa:** Cadastrar insumo "Heineken 600ml" com `unidade_base = un`, `quantidade_caixa = 12`. Registrar compra digitando "5" com seletor `cx`. Verificar `quantidade = 60` no banco.
- **UNI2:** Executar `alembic upgrade head` — verificar que tabelas operacionais estão vazias e que cadastros administrativos (garçons, categorias, fornecedores) permanecem.

## Out of Scope

- Conversões entre famílias diferentes (peso ↔ volume).
- Unidades adicionais (`cl`, `oz`, `dúzia`).
- Histórico de alteração de `quantidade_caixa` afetando compras passadas.
- Tela de migração assistida para usuários existentes (não há usuários ativos).

---

# Seção 2 — Correções Críticas no Fluxo de Compras (CP4, CP5, CP6, CP7, CP8, CP9, CP10, CP11)

## Problem Statement

Oito problemas independentes no fluxo de compras:

1. **CP4** — `ComprasPage` exibe "Total no período" mas o cálculo soma apenas os 10 itens da página atual, retornando valor errado para qualquer filtro com mais de 10 compras.
2. **CP5** — Listagem mistura compras ativas e canceladas sem filtro, dificultando análise.
3. **CP6** — Modal de edição de compra usa `<div className="fixed inset-0...">` em vez do componente `Dialog`, inconsistente com o restante do sistema.
4. **CP7** — Ao cancelar uma nota, o `ConfirmDialog` menciona estorno de estoque mas não há toast amarelo após o sucesso alertando sobre o impacto no custo médio (previsto no PRD v0.2 CP1).
5. **CP8** — Em `NovaCompraPage`, se o operador digita quantidade e custo para um item e depois troca o item do selector, os valores ficam preservados, podendo salvar dados incoerentes.
6. **CP9** — Backend faz `custo_unitario = custo_total / quantidade`, gerando dízimas com precisão arbitrária no banco (ex: R$10 / 3 = 3.3333333...).
7. **CP10** — Sistema não detecta nem alerta quando o `numero_nota` informado já existe em outra compra.
8. **CP11** — `criar_compra` e `cancelar_compra` no service iteram sobre itens atualizando estoque antes do commit; falha no meio do loop deixa estoque parcialmente atualizado sem registro de compra correspondente.

## Solution

1. **CP4** — Backend adiciona `total_periodo: Decimal` ao `ComprasPageResponse`, calculado sobre todos os filtros (não paginado). Frontend exibe esse campo.
2. **CP5** — Adicionar filtro com 3 opções (Todas / Ativas / Canceladas) com default "Ativas". Backend aceita parâmetro `status?: "ativa" | "cancelada"`.
3. **CP6** — Migrar o JSX inline para componente `Dialog` padrão usado nos demais modais.
4. **CP7** — Após sucesso de `useCancelarCompra`, disparar `toast.warning("Verifique o custo médio dos insumos afetados.")` com persistência de 5 segundos.
5. **CP8** — No `onChange` do select de item, resetar quantidade, custo unitário e custo total da linha.
6. **CP9** — Arredondar `custo_unitario` para 4 casas decimais antes de persistir.
7. **CP10** — Backend retorna 200 com `warning: "Número de nota já registrado na compra #0042"` quando duplicado; compra é salva mesmo assim. Frontend exibe `toast.warning(...)`.
8. **CP11** — Envolver `criar_compra` e `cancelar_compra` em bloco `try/except` com `db.rollback()` em caso de erro; commits no final.

## User Stories

1. Como sócio, quero ver o total real do período filtrado de compras, para conferir gastos com fornecedores sem somar manualmente página por página.
2. Como sócio, quero filtrar a listagem de compras por status, para focar apenas em notas ativas ou auditar canceladas.
3. Como sistema, quero modais com aparência consistente em todo o sistema, para evitar variação visual confusa.
4. Como sócio, quero um aviso após cancelar uma nota lembrando que o custo médio dos insumos pode ter ficado impreciso, para registrar nova compra corretiva quando necessário.
5. Como operador, quero que a linha da compra seja zerada ao trocar o item selecionado, para não salvar valores do item anterior por engano.
6. Como sistema, quero arredondar o custo unitário a uma precisão suficiente sem introduzir dízimas longas no banco, para que relatórios sejam estáveis.
7. Como sócio, quero ser avisado quando estou cadastrando uma nota com número que já existe, para verificar se não é duplicata sem bloquear o cadastro legítimo.
8. Como sistema, quero que falhas no meio do registro de compra não deixem o estoque parcialmente alterado, para garantir consistência dos dados.

## Implementation Decisions

### CP4 — Total do período no backend

**Backend — `schemas/compras.py`:**
```python
class ComprasPageResponse(BaseModel):
    itens: list[CompraResponse]
    total: int
    pagina: int
    por_pagina: int
    total_paginas: int
    total_periodo: Decimal  # novo
```

**Backend — `compras_service.list_compras`:**
- Adicionar query agregada `SELECT COALESCE(SUM(total), 0) FROM compras WHERE <filtros>` (sem paginação) e incluir no response.

**Frontend — `ComprasPage.tsx`:**
- Trocar `compras.reduce(...)` por `paginado?.total_periodo ?? 0`.

### CP5 — Filtro de status

**Backend — `compras_service.list_compras`:**
- Adicionar parâmetro `status: Optional[str] = None`. Quando informado, aplicar `WHERE status = :status`.

**Frontend — `ComprasPage.tsx`:**
- Estado `statusFiltro: "ativa" | "cancelada" | "todas"` (default `"ativa"`).
- Toggle de 3 botões no topo, padrão visual igual ao já usado em `InsumosPage`.
- Passar `status` apenas quando diferente de `"todas"`.

### CP6 — Dialog padronizado

- Substituir o bloco `<div className="fixed inset-0 z-50...">` em `ComprasPage.tsx` linha ~212 por `<Dialog open={!!editando} onOpenChange={(v) => !v && setEditando(null)}>` com `DialogContent`, `DialogHeader`, `DialogTitle`, `DialogFooter`.

### CP7 — Toast amarelo pós-cancelamento

**Frontend — `useCompras.ts → useCancelarCompra`:**
```ts
onSuccess: () => {
  qc.invalidateQueries({ queryKey: ["compras"] });
  toast.warning("Nota cancelada. Verifique o custo médio dos insumos afetados.");
}
```

### CP8 — Reset de linha ao trocar item

**Frontend — `NovaCompraPage.tsx`:**
- No `onChange` do `<select>` de `item_id`:
  ```ts
  setValue(`itens.${index}.quantidade`, 0);
  setValue(`itens.${index}.custo_total`, 0);
  setUnitarios((prev) => {
    const next = [...prev];
    next[index] = "";
    return next;
  });
  delete lastEditedRef.current[index];
  ```

### CP9 — Precisão custo_unitario

**Backend — `compras_service.criar_compra`:**
```python
custo_unitario = (item_req.custo_total / item_req.quantidade).quantize(Decimal("0.0001"))
```

### CP10 — Warning de nota duplicada

**Backend — `compras_service.criar_compra`:**
- Antes de criar a compra, se `numero_nota` informado:
  ```python
  existing = db.execute(
      select(Compra).where(Compra.numero_nota == data.numero_nota).limit(1)
  ).scalar_one_or_none()
  warning = None
  if existing:
      warning = f"Número de nota já registrado na compra #{str(existing.id).zfill(4)}"
  ```
- Incluir campo opcional `warning: Optional[str]` em `CompraResponse`.

**Frontend — `useCompras.ts → useCreateCompra`:**
- `onSuccess`: se `data.warning`, disparar `toast.warning(data.warning)`.

### CP11 — Transações atômicas

**Backend — `compras_service.criar_compra`:**
- Não há `try/except` explícito hoje. Sessão SQLAlchemy faz commit/rollback automático em contexto, mas o loop manipula `estoque` antes do `db.commit()` final, e qualquer exceção entre passos deixa state inconsistente em memória da sessão.
- Mudar para:
  ```python
  try:
      # loop atual
      db.commit()
  except Exception:
      db.rollback()
      raise
  ```
- Mesmo padrão em `cancelar_compra`.

## Testing Decisions

- **CP4:** Criar 25 compras de R$10 cada → filtrar tudo → verificar `total_periodo = 250` no response e UI mostra "Total no período: R$250,00" mesmo na página 1.
- **CP5:** Cancelar 3 de 5 compras → filtrar "Ativas" → verificar 2 resultados. Filtrar "Canceladas" → 3 resultados. Filtrar "Todas" → 5.
- **CP6:** Abrir modal de edição → verificar que usa o mesmo componente `Dialog` que outros modais (esc fecha, click fora fecha, foco aprisionado).
- **CP7:** Cancelar nota com 2 insumos → verificar toast amarelo após sucesso.
- **CP8:** Linha 1 com item A, qtd 5, custo 100 → trocar item para B → verificar qtd e custos zerados.
- **CP9:** Registrar compra de 3 unidades a R$10 → verificar `custo_unitario = 3.3333` (4 casas) no banco.
- **CP10:** Registrar compra com `numero_nota = "X1"` → registrar segunda compra com mesmo número → verificar warning no response e toast no front. Verificar que compra foi salva.
- **CP11:** Simular falha no meio do loop de `criar_compra` (mock de `update_estoque_e_custo` lançando exceção na 2ª iteração) → verificar que estoque do 1º insumo não foi alterado e compra não foi criada.

## Out of Scope

- Bloqueio total de nota duplicada (decisão: apenas warning).
- Auditoria de quem cancelou a nota e quando (não há sistema multi-usuário com identificação).

---

# Seção 3 — Padronização de Modais (MOD1)

## Problem Statement

Três modais ainda usam `<div className="fixed inset-0...">` em vez do componente `Dialog`:
- `NovaComandaModal`
- `CancelarItemModal`
- Modal de edição de compra dentro de `ComprasPage` (coberto em CP6).

A divergência prejudica a UX (sem foco aprisionado, sem fechar com Esc, sem fechar com clique fora) e dificulta manutenção.

## Solution

Migrar `NovaComandaModal` e `CancelarItemModal` para usar `<Dialog>`, `<DialogContent>`, `<DialogHeader>`, `<DialogTitle>` e `<DialogFooter>`.

## User Stories

1. Como operador, quero fechar qualquer modal pressionando Esc ou clicando fora, para fluxo rápido durante o atendimento.
2. Como operador, quero foco automático no primeiro campo ao abrir um modal, para começar a digitar sem precisar clicar.

## Implementation Decisions

**`NovaComandaModal.tsx`:**
- Trocar o wrapper externo por `<Dialog open={true} onOpenChange={(v) => !v && onClose()}>`.
- Mover o botão "Cancelar" para `<DialogFooter>`.
- Garantir que o componente seja sempre montado controlado por prop (já está).

**`CancelarItemModal.tsx`:**
- Mesma migração.

## Testing Decisions

- Abrir modal → pressionar Esc → modal fecha.
- Abrir modal → clicar fora → modal fecha.
- Abrir modal → foco automático no primeiro input.

## Out of Scope

- Redesign visual dos modais.
- Animação de transição.

---

# Seção 4 — Correções no Fluxo de Comanda (NC1, NC2, CA1, CA2)

## Problem Statement

Quatro pontos no fluxo de comandas:

1. **NC1** — `NovaComandaModal` renderiza `<Input type="number" />` para o campo `identificacao` quando `tipo = "mesa"`, mas não passa `valueAsNumber` ao `register`. O backend recebe string `"5"` em vez de número 5. O PRD v0.2 C3 previa esse ajuste, mas só metade foi implementada.
2. **NC2** — Radio inputs de `tipo_identificacao` em `NovaComandaModal` não têm `id` correspondente ao `htmlFor` dos labels — apenas o `value` do radio dentro do `<label>` envolvendo. Acessibilidade prejudicada.
3. **CA1** — Em `ComandaAbertaPage`, o modo de edição inline de um item lançado usa `<Input>` (texto livre) para o campo `pessoa`, mesmo quando a comanda já possui `pessoas` cadastradas. O painel "Adicionar Item" usa `<select>` no mesmo caso. Inconsistência.
4. **CA2** — O campo "Aberta há X min" é calculado no backend no momento da query e enviado como inteiro. Se o operador deixa a tela aberta por 30 minutos sem refresh, o valor exibido permanece desatualizado.

## Solution

1. **NC1** — Adicionar `valueAsNumber: tipo === "mesa"` no `register("identificacao")`.
2. **NC2** — Adicionar `id` em cada `<input type="radio">` e `htmlFor` no `<label>`.
3. **CA1** — Trocar `<Input>` por `<select>` populado com `comanda.pessoas` no modo de edição inline.
4. **CA2** — Calcular `tempo_aberta_minutos` no frontend a partir de `created_at`, atualizando a cada 60 segundos via `setInterval`.

## User Stories

1. Como sistema, quero receber o número da mesa como inteiro do frontend, para validações numéricas funcionarem corretamente no backend.
2. Como operador com leitor de tela, quero que o foco do radio de tipo de identificação esteja conectado ao label, para navegar via teclado.
3. Como operador, quero selecionar a pessoa de um item já lançado via lista de pessoas da comanda, para não digitar o nome incorretamente.
4. Como operador, quero ver o tempo atualizado de uma comanda aberta, mesmo sem recarregar a tela, para saber quanto tempo o cliente está no estabelecimento.

## Implementation Decisions

### NC1 + NC2

**`NovaComandaModal.tsx`:**

```tsx
<input
  type="radio"
  id={`tipo-${tipo}`}
  value={tipo}
  {...register("tipo_identificacao")}
/>
<label htmlFor={`tipo-${tipo}`}>{...}</label>
```

```tsx
<Input
  id="identificacao"
  type={tipoSelecionado === "mesa" ? "number" : "text"}
  {...register("identificacao", { valueAsNumber: tipoSelecionado === "mesa" })}
/>
```

### CA1 — Select de pessoa no edit item

**`ComandaAbertaPage.tsx`:**

```tsx
{editingId === ic.id ? (
  comanda.pessoas.length > 0 ? (
    <select
      className="..."
      value={editPessoa}
      onChange={(e) => setEditPessoa(e.target.value)}
    >
      <option value="">— nenhuma —</option>
      {comanda.pessoas.map((p, i) => (
        <option key={i} value={p}>{p}</option>
      ))}
    </select>
  ) : (
    <Input value={editPessoa} onChange={(e) => setEditPessoa(e.target.value)} />
  )
) : ( ... )}
```

### CA2 — Recálculo no frontend

**`ComandaAbertaPage.tsx`:**

```tsx
const [agora, setAgora] = useState(() => Date.now());

useEffect(() => {
  if (comanda?.status !== "aberta" && comanda?.status !== "reaberta") return;
  const id = setInterval(() => setAgora(Date.now()), 60_000);
  return () => clearInterval(id);
}, [comanda?.status]);

const tempoAberta = comanda
  ? Math.floor((agora - new Date(comanda.created_at).getTime()) / 60_000)
  : 0;
```

- Substituir `comanda.tempo_aberta_minutos` por `tempoAberta` na renderização.
- Aplicar a mesma lógica em `ComandasPage.tsx` (lista de cards/lista).

## Testing Decisions

- **NC1:** Abrir modal, selecionar "mesa", digitar "5", abrir comanda → verificar via GET que `identificacao` é número (não string).
- **NC2:** Navegar pelo teclado (Tab) → radios recebem foco e labels estão associados (DevTools "Inspect Accessibility").
- **CA1:** Comanda com pessoas ["Ana", "Bruno"] → editar item → verificar que o campo pessoa é select com Ana, Bruno e "— nenhuma —".
- **CA2:** Abrir comanda → aguardar 1 minuto → verificar que o contador "Aberta há X min" incrementou sem refresh.

## Out of Scope

- Refresh automático dos itens da comanda (continua manual via invalidate de cache).
- Adicionar campo `pessoa_associada` ao registro de cancelamento.

---

# Seção 5 — Correções no Fluxo de Fechamento (FE1, FE2, FE3, FE4, DE1, DE2, CV1)

## Problem Statement

Sete problemas no fluxo de fechamento de comanda e desconto:

1. **FE1** — O resumo de itens em `FechamentoPage` exibe `{item.quantidade}×` diretamente, em vez de aplicar `formatQuantidade`. Quantidades decimais aparecem com casas indesejadas (ex: "1.5×" em vez de "1,5×"). Inconsistente com `ComandaAbertaPage`.
2. **FE2** — O `modo_divisao` em `FechamentoPage` usa radio inputs com `setValue` manual e `watch`, mesmo padrão dos bugs BG1/BG2 do PRD v0.2.
3. **FE3** — No modo "igualmente", o componente rotula "1ª pessoa paga: Y" para o valor que absorve a sobra do arredondamento. O termo "1ª pessoa" sugere a primeira da lista, quando na verdade é a pessoa que paga o valor diferente. Confunde o operador.
4. **FE4** — O schema `fecharComandaSchema.pagamentos: z.array(...).min(1)` é incompatível com Z1 do PRD v0.2 (total R$0 envia `pagamentos: []`). Hoje o front desvia pelo caminho `baseTotal === 0` sem passar pelo schema, mas a incoerência é uma armadilha futura.
5. **DE1** — `AplicarDescontoModal` usa `<Dialog open={open} onOpenChange={onClose}>` — `onClose` é chamado a cada mudança de estado do Dialog (inclusive abertura). Deveria ser `(v) => !v && onClose()`.
6. **DE2** — Radio inputs de tipo de desconto ("percentual" / "valor") em `AplicarDescontoModal` usam `setValue` manual. Mesmo padrão BG1/BG2.
7. **CV1** — `ComprovantePage` linha 117 exibe `{item.quantidade}x` sem `formatQuantidade`. Mesma classe do FE1.

## Solution

1. **FE1** — Aplicar `formatQuantidade(item.quantidade)` no resumo de itens.
2. **FE2** — Migrar o radio de `modo_divisao` para `<Controller>` do RHF.
3. **FE3** — Trocar o label "1ª pessoa paga" por "Última pessoa paga".
4. **FE4** — Tornar `pagamentos.min(1)` condicional: `pagamentos: z.array(...)` sem `.min(1)`; validar manualmente no submit: se `baseTotal > 0` então `pagamentos.length >= 1`.
5. **DE1** — Trocar `onOpenChange={onClose}` por `onOpenChange={(v) => !v && onClose()}`.
6. **DE2** — Migrar o radio de tipo de desconto para `<Controller>`.
7. **CV1** — Aplicar `formatQuantidade(item.quantidade)` no comprovante.

## User Stories

1. Como caixa, quero ver "1,5×" em vez de "1.5×" para quantidades fracionárias no resumo do fechamento, para coerência com a tela de comanda.
2. Como caixa, quero que o modo de divisão selecionado seja sempre persistido corretamente no submit, para o cálculo refletir minha escolha.
3. Como caixa, quero que o label do valor diferente seja "Última pessoa", para entender corretamente quem paga a sobra do arredondamento.
4. Como sistema, quero schemas coerentes com os fluxos suportados, para evitar bugs futuros.
5. Como sócio, quero abrir o modal de desconto sem que ele tente fechar sozinho, para aplicar desconto sem perder o input.
6. Como sócio, quero que a escolha entre desconto percentual ou em valor seja sempre persistida, para o desconto correto ser aplicado.
7. Como cliente, quero ver "1,5×" em vez de "1.5×" no comprovante impresso, para legibilidade no padrão brasileiro.

## Implementation Decisions

### FE1 + CV1 — formatQuantidade

**`FechamentoPage.tsx` (linha ~97):**
```tsx
<span>
  {formatQuantidade(item.quantidade)}× {item.item_nome}
  {item.cortesia && " 🎁"}
  {item.pessoa_associada && ` (${item.pessoa_associada})`}
</span>
```

**`ComprovantePage.tsx` (linha 117):**
```tsx
<span className="flex-1 truncate">
  {formatQuantidade(item.quantidade)}x {item.nome}
  {item.cortesia && <span className="text-gray-500"> (cortesia)</span>}
</span>
```

### FE2 — modo_divisao via Controller

**`FechamentoPage.tsx`:**
```tsx
<Controller
  control={control}
  name="modo_divisao"
  render={({ field }) => (
    <div className="space-y-2">
      {modoOpcoes.map((opt) => (
        <div key={opt.value} className="flex items-center gap-2">
          <input
            type="radio"
            id={`modo-${opt.value}`}
            value={opt.value}
            checked={field.value === opt.value}
            onChange={() => {
              field.onChange(opt.value);
              if (opt.value === "sem_divisao") {
                setValue("pagamentos.0.valor", Number(baseTotal.toFixed(2)));
              } else {
                setValue("pagamentos.0.valor", 0);
              }
            }}
          />
          <Label htmlFor={`modo-${opt.value}`}>{opt.label}</Label>
        </div>
      ))}
    </div>
  )}
/>
```

### FE3 — Label "última pessoa"

**`FechamentoPage.tsx`:**
- Substituir o texto "1ª pessoa paga:" por "Última pessoa paga:".
- Manter a ordem dos cálculos como hoje (N-1 pessoas pagam o valor base, a última paga o saldo).

### FE4 — Schema coerente com Z1

**`fechamentoSchemas.ts`:**
```ts
export const fecharComandaSchema = z.object({
  pagamentos: z.array(pagamentoSchema),
  modo_divisao: z.enum(["sem_divisao", "igualmente", "por_pessoa", "parcial"]),
});
```

- Remover `.min(1)` do array.
- Validar manualmente no submit handler do `FechamentoPage`: se `baseTotal > 0 && pagamentos.length === 0` → setar erro no formulário e impedir submit.

### DE1 + DE2 — AplicarDescontoModal

**`AplicarDescontoModal.tsx`:**
```tsx
<Dialog open={open} onOpenChange={(v) => !v && onClose()}>
```

```tsx
<Controller
  control={control}
  name="tipo"
  render={({ field }) => (
    <div className="flex gap-4">
      {(["percentual", "valor"] as const).map((t) => (
        <div key={t} className="flex items-center gap-2">
          <input
            type="radio"
            id={`desc-${t}`}
            checked={field.value === t}
            onChange={() => field.onChange(t)}
          />
          <Label htmlFor={`desc-${t}`}>
            {t === "percentual" ? "Percentual (%)" : "Valor fixo (R$)"}
          </Label>
        </div>
      ))}
    </div>
  )}
/>
```

## Testing Decisions

- **FE1:** Lançar item com qtd 1.5, ir ao fechamento → resumo exibe "1,5×" (vírgula).
- **FE2:** Selecionar "igualmente", submeter → verificar payload com `modo_divisao: "igualmente"`. Repetir para os 4 modos.
- **FE3:** Modo igualmente com N=3 → verificar label "Última pessoa paga".
- **FE4:** Comanda com total R$0 → confirmar fechamento sem método → backend recebe `pagamentos: []`. Comanda com total > 0 sem pagamento → submit bloqueado.
- **DE1:** Abrir modal de desconto → verificar que não fecha automaticamente.
- **DE2:** Trocar entre "Percentual" e "Valor fixo" → submeter → verificar payload com `tipo` correto.
- **CV1:** Imprimir comprovante de comanda com item de qtd 1.5 → exibe "1,5x" (vírgula).

## Out of Scope

- Redesign visual da tela de fechamento.
- Modos de divisão adicionais (porcentagem por pessoa, etc.).

---

# Seção 6 — Histórico de Movimentações (MV1, MV2)

## Problem Statement

1. **MV1** — O PRD v0.2 CP1 introduziu o tipo `ESTORNO_COMPRA` no backend para estornos de cancelamento de notas. `MovimentosPage` no frontend tem mapas `TIPO_BADGE`, `TIPO_LABEL` e `TIPO_OPTIONS` que não incluem esse tipo — movimentos de estorno aparecem sem badge nem label legível.
2. **MV2** — A coluna de data exibe `dd/mm HH:MM`, omitindo o ano. Para histórico longo (vários meses), fica ambíguo se o movimento foi neste ano ou no anterior.

## Solution

1. **MV1** — Adicionar `estorno_compra` em `TIPO_BADGE`, `TIPO_LABEL` e `TIPO_OPTIONS`.
2. **MV2** — Alterar `toLocaleString` para incluir ano: `dd/mm/yyyy HH:MM`.

## User Stories

1. Como sócio, quero ver claramente quais movimentos são estornos de compra cancelada, para auditar reversões.
2. Como sócio, quero filtrar apenas movimentos de estorno, para revisar cancelamentos recentes.
3. Como sócio, quero ver o ano da movimentação, para distinguir registros antigos de recentes.

## Implementation Decisions

**`MovimentosPage.tsx`:**

```ts
const TIPO_OPTIONS = [
  { value: "", label: "Todos os tipos" },
  { value: "entrada", label: "Entrada" },
  { value: "saida_venda", label: "Saída venda" },
  { value: "saida_perda", label: "Baixa" },
  { value: "estorno_compra", label: "Estorno compra" },
];

const TIPO_BADGE: Record<string, string> = {
  entrada: "bg-green-100 text-green-700",
  saida_venda: "bg-blue-100 text-blue-700",
  saida_perda: "bg-orange-100 text-orange-700",
  estorno_compra: "bg-gray-100 text-gray-600",
};

const TIPO_LABEL: Record<string, string> = {
  entrada: "Entrada",
  saida_venda: "Saída venda",
  saida_perda: "Baixa",
  estorno_compra: "Estorno compra",
};
```

```tsx
{new Date(mov.created_at).toLocaleString("pt-BR", {
  day: "2-digit",
  month: "2-digit",
  year: "2-digit",
  hour: "2-digit",
  minute: "2-digit",
})}
```

## Testing Decisions

- Criar uma compra e cancelá-la → ir em Movimentos → filtrar por "Estorno compra" → ver o registro com badge cinza.
- Verificar que a data exibida inclui o ano (ex: "11/05/26 14:30").

## Out of Scope

- Filtro combinado de tipo + insumo (já existe parcialmente).
- Exportação CSV dos movimentos.

---

# Seção 7 — Arquitetura: Histórico Unificado (AR1, AR2)

## Problem Statement

1. **AR1** — Existem duas páginas com função quase idêntica: `/historico` (`HistoricoPage`) e `/relatorios/historico` (`HistoricoComandasPage`). Ambas listam comandas fechadas com filtro de período e busca. A primeira tem rows clicáveis mas não tem filtro por garçom; a segunda tem filtro por garçom mas rows não clicáveis. Duplicação confunde o usuário.
2. **AR2** — `HistoricoComandasPage` não permite clicar nas linhas para abrir o detalhe da comanda. Operador precisa decorar o número da comanda para acessá-la.

## Solution

1. **AR1** — Remover `/historico` do Sidebar e do roteamento. A rota fica fora do navegação principal. Mover a única vantagem (rows clicáveis) para `HistoricoComandasPage`.
2. **AR2** — Tornar as linhas da tabela em `HistoricoComandasPage` clicáveis, navegando para `/comandas/:id`.

## User Stories

1. Como sócio, quero um único lugar para consultar histórico de comandas fechadas, para não me confundir com duas telas parecidas.
2. Como sócio, quero clicar em uma comanda no histórico para abrir seu detalhe, para revisar pedidos e pagamentos sem precisar copiar o número.

## Implementation Decisions

### AR1 — Remoção de /historico

**`Sidebar.tsx`:**
- Remover entrada `{ label: "Histórico", to: "/historico", icon: ScrollText }` de `NAV_ITEMS`.

**`App.tsx`:**
- Manter a rota `/historico` apontando para `HistoricoComandasPage` (redirecionamento temporário) ou removê-la. **Decisão: remover** — não há usuários ativos para preservar bookmarks.
- Excluir o arquivo `HistoricoPage.tsx` e seus imports.

### AR2 — Rows clicáveis em HistoricoComandasPage

**`HistoricoComandasPage.tsx`:**

```tsx
<tr
  key={c.id}
  onClick={() => navigate(`/comandas/${c.id}`)}
  className="border-b hover:bg-gray-50 cursor-pointer"
>
  ...
</tr>
```

- Importar `useNavigate` do `react-router-dom`.

## Testing Decisions

- Navegar pelo Sidebar → não há item "Histórico" no nível principal.
- Acessar `/historico` diretamente → 404 ou rota tratada pelo `PlaceholderPage`.
- Ir em "Relatórios → Histórico de Comandas" → clicar em uma linha → navega para `/comandas/:id`.

## Out of Scope

- Adicionar paginação em `HistoricoComandasPage` (deixar para próxima versão).
- Exportação CSV.

---

# Seção 8 — Cardápio (CD1, CD2)

## Problem Statement

1. **CD1** — `CardapioPage` exibe todos os produtos misturando ativos e inativos sem filtro. Botão "Desativar" aparece mesmo para produtos já inativos, quando deveria ser "Reativar".
2. **CD2** — Sem campo de busca por nome — operador precisa rolar a lista inteira em cardápios grandes.

## Solution

1. **CD1** — Adicionar filtro (Todos / Ativos / Inativos) com default "Ativos". Botão da linha alterna entre "Desativar" e "Reativar" conforme o status.
2. **CD2** — Adicionar input de busca por nome. Filtragem client-side sobre os produtos carregados.

## User Stories

1. Como sócio, quero ver apenas produtos ativos por padrão no cardápio, para focar no que está em uso.
2. Como sócio, quero alternar para inativos quando quiser reativar algum produto antigo.
3. Como sócio, quero reativar um produto desativado clicando "Reativar" diretamente na lista.
4. Como sócio, quero buscar produtos por nome rapidamente, para edição sem rolar.

## Implementation Decisions

### CD1 — Filtro + Reativar

**Backend — `produtos_service` (se necessário):**
- Garantir que `GET /api/produtos` retorne campo `ativo: bool` (verificar — provavelmente já retorna).
- Endpoint `POST /api/produtos/{id}/reativar` (ou reutilizar o de update com `ativo: true`).

**Frontend — `CardapioPage.tsx`:**
- Estado `filtro: "todos" | "ativos" | "inativos"` (default `"ativos"`).
- Botão da coluna ações: condicional baseado em `produto.ativo`:
  ```tsx
  {produto.ativo ? (
    <Button onClick={() => setConfirmDesativar(p.id)}>Desativar</Button>
  ) : (
    <Button onClick={() => reativar.mutate(p.id)}>Reativar</Button>
  )}
  ```

### CD2 — Busca por nome

**Frontend — `CardapioPage.tsx`:**
- Estado `busca: string`.
- Input no topo da página: `<Input placeholder="Buscar produto..." />`.
- Filtro combinado: `produtos.filter(p => (filtro aplicado) && p.nome.toLowerCase().includes(busca.toLowerCase()))`.

## Testing Decisions

- Cadastrar 2 produtos ativos e 1 inativo → filtrar "Ativos" → ver 2. Filtrar "Inativos" → ver 1.
- Clicar "Reativar" no inativo → produto fica ativo e aparece no filtro "Ativos".
- Digitar parte do nome de um produto → lista filtra.

## Out of Scope

- Filtro por categoria além do que já existe.
- Ordenação por CMV ou margem.

---

# Seção 9 — Relatório Vendas do Dia (VD1, VD2)

## Problem Statement

1. **VD1** — `VendasDoDiaPage` sempre mostra o dia atual. Para consultar vendas de ontem, o usuário precisa ir em "Histórico de Comandas" e somar manualmente.
2. **VD2** — Linhas da tabela de comandas não são clicáveis — não navegam para o detalhe.

## Solution

1. **VD1** — Adicionar seletor de data com default = hoje. Backend já aceita parâmetro `data`.
2. **VD2** — Tornar linhas clicáveis para `/comandas/:id`.

## User Stories

1. Como sócio, quero ver vendas de ontem ou de qualquer dia anterior, para comparar desempenho.
2. Como sócio, quero clicar na linha de uma comanda para abrir o detalhe, para revisar pedidos.

## Implementation Decisions

**`VendasDoDiaPage.tsx`:**

```tsx
const [data, setData] = useState(() => new Date().toISOString().slice(0, 10));
const { data: vendas, isLoading } = useVendasDoDia(data);
```

```tsx
<input
  type="date"
  value={data}
  onChange={(e) => setData(e.target.value)}
  className="rounded border px-2 py-1 text-sm"
/>
```

**`useRelatorios.ts → useVendasDoDia`:**
- Aceitar parâmetro `data?: string` e passar como query param.

**Backend:** verificar se endpoint já aceita parâmetro `data` (se não, adicionar).

**Linhas clicáveis:**
```tsx
<tr
  key={c.id}
  onClick={() => navigate(`/comandas/${c.id}`)}
  className="border-b hover:bg-gray-50 cursor-pointer"
>
```

## Testing Decisions

- Trocar data para 1 dia atrás → verificar que os totais mudam (se houve vendas).
- Clicar em uma linha de comanda → navega para `/comandas/:id`.

## Out of Scope

- Comparativo entre dois dias na mesma tela.
- Exportação do relatório.

---

# Seção 10 — Cadastros: Toggle Inline (CG1)

## Problem Statement

`GarconsPage` e `MetodosPagamentoPage` permitem ativar/desativar registros apenas via modal de edição: o usuário clica "Editar", encontra o toggle, salva. São 3 ações para uma operação atômica.

## Solution

Adicionar botão "Ativar" / "Desativar" diretamente na linha da tabela, ao lado de "Editar" / "Remover".

## User Stories

1. Como sócio, quero desativar um garçom diretamente da lista, sem precisar abrir o modal de edição.
2. Como sócio, quero o mesmo comportamento para métodos de pagamento.

## Implementation Decisions

**Backend:**
- Verificar se existe endpoint `PATCH /api/garcons/{id}/toggle-ativo` (PRD v0.2 BG2 fix usou Controller para o toggle no modal — o endpoint genérico de update já cobre).
- Se não existe, adicionar `PATCH /api/garcons/{id}` aceitando `{ ativo: boolean }`.

**Frontend — `GarconsPage.tsx`:**

```tsx
<Button
  size="sm"
  variant="outline"
  onClick={() => toggleAtivo.mutate(g.id)}
>
  {g.ativo ? "Desativar" : "Ativar"}
</Button>
```

- `useToggleGarcomAtivo` em `useGarcons.ts`: chama `PATCH /api/garcons/{id}` com `{ ativo: !current }`.

**`MetodosPagamentoPage.tsx`:** mesmo padrão com `useToggleMetodoAtivo` em `useMetodosPagamento.ts`.

## Testing Decisions

- Clicar "Desativar" em um garçom ativo → verifica que linha fica com badge "Inativo".
- Clicar "Ativar" → volta para ativo.
- Repetir para métodos de pagamento.

## Out of Scope

- Toggle inline em Insumos (já existe).

---

# Seção 11 — Dashboard e Sidebar (DB1, SB1)

## Problem Statement

1. **DB1** — `DashboardPage` mantém os hooks `useDashboardHistorico` e `useDashboardResumoAnual` montados mesmo quando a aba ativa é "Resumo". Fetches desnecessários no carregamento inicial.
2. **SB1** — Sidebar não exibe contagem de comandas abertas. Operador precisa ir até "Comandas" para saber se há comandas em aberto.

## Solution

1. **DB1** — Mover os hooks para dentro do componente `TabHistorico`, que só monta quando a aba está ativa.
2. **SB1** — Adicionar badge com contagem (`comandas_abertas` do dashboard) ao item "Comandas" do Sidebar.

## User Stories

1. Como sistema, quero evitar chamadas de API desnecessárias, para reduzir carga no backend.
2. Como operador, quero ver a contagem de comandas abertas direto no menu lateral, para saber rapidamente se há trabalho pendente.

## Implementation Decisions

### DB1

**`DashboardPage.tsx`:**
- Os hooks `useDashboardHistorico` e `useDashboardResumoAnual` já estão dentro de `TabHistorico` (verificar — pelo código atual estão lá). **Confirmar via leitura final** que não há instâncias paralelas em `DashboardPage` principal.
- Se houver, remover do escopo do `DashboardPage` raiz.

### SB1 — Badge no Sidebar

**Frontend — `Sidebar.tsx`:**
- Adicionar hook `useComandasAbertasCount()` (novo, em `useComandas.ts`) que retorna apenas a contagem:
  ```ts
  export function useComandasAbertasCount() {
    return useQuery<number>({
      queryKey: ["comandas", "count-abertas"],
      queryFn: () => api.get<number>("/api/comandas/count-abertas").then(r => r.data),
      staleTime: 30_000,
    });
  }
  ```
- Backend: endpoint leve `GET /api/comandas/count-abertas` retornando inteiro.
- No item "Comandas" do `NAV_ITEMS`, renderizar badge:
  ```tsx
  {count > 0 && (
    <span className="ml-auto rounded-full bg-amber-500 px-2 py-0.5 text-xs text-white">
      {count}
    </span>
  )}
  ```

## Testing Decisions

- **DB1:** Abrir Dashboard na aba "Resumo" → verificar via DevTools que `/api/dashboard/historico` e `/api/dashboard/resumo-anual` não foram chamados.
- **SB1:** Abrir 3 comandas → ver badge "3" ao lado de "Comandas" no menu. Fechar todas → badge desaparece.

## Out of Scope

- Badge em outras entradas do menu.
- Atualização em tempo real via WebSocket.

---

# Seção 12 — Estoque e Backup (ES1, BK1)

## Problem Statement

1. **ES1** — `EstoquePage` mostra saldo e custo médio por item mas não mostra o valor total em estoque (capital parado). Sócio não tem visão imediata desse número.
2. **BK1** — Backup baixado pelo navegador sempre tem nome `backup.json` ou `backup.xlsx` — múltiplos backups são sobrescritos no diretório de downloads.

## Solution

1. **ES1** — Adicionar coluna "Valor em estoque" (saldo × custo_medio) e rodapé totalizando o valor de todos os itens visíveis.
2. **BK1** — Incluir data no nome do arquivo: `backup_YYYY-MM-DD.json` / `.xlsx`.

## User Stories

1. Como sócio, quero ver o valor financeiro do estoque atual, para saber quanto capital está parado.
2. Como sócio, quero baixar vários backups sem que se sobrescrevam, para manter histórico de versões.

## Implementation Decisions

### ES1 — Valor em estoque

**Frontend — `EstoquePage.tsx`:**
- Nova coluna na tabela:
  ```tsx
  <td className="py-2 text-gray-600">
    {item.custo_medio != null
      ? formatCurrency(Number(item.estoque_atual) * item.custo_medio)
      : "—"}
  </td>
  ```
- Rodapé `<tfoot>` somando todos os itens visíveis (respeitando filtros).

### BK1 — Backup com data

**`ConfiguracoesPage.tsx → TabBackup → download`:**
```ts
const today = new Date().toISOString().slice(0, 10);
a.download = `backup_${today}.${ext}`;
```

## Testing Decisions

- Cadastrar insumos com saldo e custo conhecidos → verificar valor por linha + total no rodapé.
- Baixar backup → arquivo nomeado `backup_2026-05-11.json`.

## Out of Scope

- Histórico de backups guardado no servidor.
- Importação de backup.

---

# Seção 13 — Limpeza de Código Morto e Consistência (CM1, EM1)

## Problem Statement

1. **CM1** — `ItensPage.tsx`, `ItemModal.tsx`, `useItens.ts` e `itemSchemas.ts` existem no codebase mas não estão registrados em nenhuma rota do `App.tsx` nem mencionados no `Sidebar`. Código legado da época anterior à separação entre Insumos e Produtos (PRD v0.1 M000).
2. **EM1** — `InsumoEditModal.handleClose` chama `reset()` sem argumentos, retornando valores a `undefined`. Quando o modal é reaberto para outro insumo, há um flash visual antes do `useEffect` repreencher os campos.

## Solution

1. **CM1** — Deletar os 4 arquivos. Remover quaisquer imports residuais.
2. **EM1** — `reset()` deve receber os valores corretos no fechamento, ou simplesmente não ser chamado (deixar o `useEffect` em `[open, editing]` cuidar disso).

## User Stories

1. Como desenvolvedor, quero remover código morto, para reduzir confusão e tempo de manutenção.
2. Como operador, quero abrir o modal de edição de insumo sem ver campos vazios brevemente, para fluxo visual limpo.

## Implementation Decisions

### CM1

Excluir os seguintes arquivos:

- `frontend/src/features/cadastros/itens/ItensPage.tsx`
- `frontend/src/features/cadastros/itens/ItemModal.tsx`
- `frontend/src/features/cadastros/itens/itemSchemas.ts`
- Eventual `useItens.ts` (se existir no diretório — verificar; pode ser que use um shared hook).

Confirmar que nenhum outro arquivo importa desses módulos via `grep "from.*cadastros/itens"`.

### EM1

**`InsumoEditModal.tsx`:**
```ts
function handleClose() {
  onClose();
}
```

- Remover a chamada `reset()` em `handleClose`. O `useEffect([open, editing, reset])` já cuida de reinicializar os campos quando o modal reabre com novo `editing`.

## Testing Decisions

- **CM1:** Após exclusão, rodar `npm run build` e `npm run type-check` no frontend — sem erros.
- **EM1:** Editar insumo A → fechar → editar insumo B → verificar que campos preenchem direto com dados de B sem flash de valores vazios.

## Out of Scope

- Auditoria completa de outros possíveis arquivos órfãos.

---

# Seção 14 — Debounce de Buscas (DB2)

## Problem Statement

Inputs de busca em diversas páginas (`ComandasPage`, `ComandaAbertaPage`, `EstoquePage`, `MovimentosPage`, `HistoricoComandasPage`, `CardapioPage` após CD2) disparam queries à API a cada tecla digitada. Em volume real isso gera 5-10 requisições por palavra digitada — desperdício de rede e potencial throttling.

## Solution

Adicionar dependência `use-debounce` (~2kb) e aplicar `useDebounce(busca, 350)` em todos os inputs de busca que disparam queries de API.

## User Stories

1. Como operador, quero que minha busca dispare uma única vez ao terminar de digitar, para resposta rápida e sem flicker.
2. Como sistema, quero reduzir chamadas redundantes à API, para escalabilidade.

## Implementation Decisions

**Instalação:**
```bash
cd frontend
npm install use-debounce
```

**Padrão de uso:**
```ts
import { useDebounce } from "use-debounce";

const [busca, setBusca] = useState("");
const [debouncedBusca] = useDebounce(busca, 350);
const { data } = useComandas(debouncedBusca || undefined);
```

**Aplicar em:**
- `ComandasPage.tsx` — busca no `useComandas(busca)`.
- `ComandaAbertaPage.tsx` — busca no `useProdutos(busca)`.
- `EstoquePage.tsx` — `filters.busca` aplicado via `useSaldoEstoque(filters)`.
- `HistoricoComandasPage.tsx` — `busca` no `useHistoricoComandas`.
- `CardapioPage.tsx` (após CD2).
- `HistoricoPage.tsx` (será removido em AR1).
- `MovimentosPage.tsx` — não tem busca textual, mas se vier a ter no futuro.

## Testing Decisions

- Digitar uma palavra de 8 letras rapidamente em um campo de busca → verificar via DevTools Network que houve **1** request (não 8).
- Aguardar 350ms após parar de digitar → query é disparada.

## Out of Scope

- Cancelamento de requests in-flight quando a query muda (deixar para próxima versão).
- Configuração global de delay.

---

## Sequência de Implementação Recomendada

```
Bloco A (limpeza, sem dependências):    CM1, EM1, DB2
Bloco B (fixes de schema/Controller):   FE2, FE4, DE1, DE2
Bloco C (fixes UX pontuais):            FE1, FE3, CV1, NC1, NC2, CA1, CA2, MV1, MV2
Bloco D (compras pré-unidades):         CP4, CP5, CP6, CP7, CP8, CP9, CP10, CP11
Bloco E (modais padronizados):          MOD1
Bloco F (reset banco):                  UNI2
Bloco G (unidades):                     UNI1, CP12, FT1
Bloco H (navegação e listagens):        AR1, AR2, CD1, CD2, VD1, VD2, CG1
Bloco I (features pequenas):            DB1, SB1, ES1, BK1
```

**Dependências críticas:**
- UNI2 (reset banco) **deve ocorrer antes** de UNI1 — após reset, todos os testes de compra e ficha técnica usam dados novos.
- CP4 a CP11 devem vir antes de UNI1 — UNI1 altera o submit de compra/ficha técnica e ficaria mais difícil debugar se os outros bugs ainda estiverem ativos.
- DB2 (debounce) pode ser feito em qualquer ordem, mas antes das mudanças em listagens (Bloco H) facilita validação.
