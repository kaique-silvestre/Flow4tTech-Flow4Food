
# Issues — Matchpoint Ajustes e Melhorias v0.2

> Gerado a partir de `docs/prds/prd_matchpoint_v0.2.md`.
> Ordem de criação respeita dependências (blockers primeiro).

---

## Issue 1 — BG1: Toggle ativo/inativo não persiste em MetodoPagamentoModal ✓ Concluída

**Tipo:** AFK  
**Bloqueado por:** Nenhum — pode iniciar imediatamente

### O que construir

Substituir o gerenciamento manual do campo `ativo` via `setValue`/`watch` por `Controller` do React Hook Form em `MetodoPagamentoModal.tsx`. O `Controller` garante que o campo seja registrado corretamente e incluído no payload de submissão.

**Mudança cirúrgica:**
- Importar `Controller` de `react-hook-form`.
- Remover `const ativo = watch("ativo")` e o `setValue` no onClick do toggle.
- Envolver o botão de toggle em `<Controller name="ativo" control={control} render={({ field }) => ...} />`.
- `field.value` substitui `ativo`; `field.onChange(!field.value)` substitui `setValue("ativo", !ativo)`.
- Zero mudança no backend.

### Critérios de aceite

- [x] Abrir modal de método de pagamento ativo → clicar toggle para inativo → salvar → GET confirma `ativo=false`
- [x] Abrir modal de método de pagamento inativo → clicar toggle para ativo → salvar → GET confirma `ativo=true`
- [x] Estado visual do toggle (cor/posição) reflete o valor correto antes e após salvar
- [x] `watch("ativo")` standalone removido — apenas `Controller` gerencia o campo
- [x] Nenhum outro campo do formulário é afetado

### User stories endereçadas

- US1: Como sócio, quero clicar no toggle de ativo/inativo em um método de pagamento e ver a mudança persistida ao salvar, para não precisar repetir a operação.

---

## Issue 2 — BG2: Toggle ativo/inativo não persiste em GarcomModal ✓ Concluída

**Tipo:** AFK  
**Bloqueado por:** Nenhum — pode iniciar imediatamente

### O que construir

Mesmo fix do Issue 1 aplicado a `GarcomModal.tsx`. Causa raiz idêntica — `ativo` gerenciado via `setValue`/`watch` sem `register` em input HTML.

**Mudança cirúrgica:**
- Importar `Controller` de `react-hook-form`.
- Substituir o padrão `watch("ativo")` + `setValue` no onClick do toggle por `Controller`.
- Zero mudança no backend.

### Critérios de aceite

- [x] Abrir modal de garçom ativo → clicar toggle para inativo → salvar → GET confirma `ativo=false`
- [x] Abrir modal de garçom inativo → clicar toggle para ativo → salvar → GET confirma `ativo=true`
- [x] Estado visual do toggle reflete o valor correto antes e após salvar
- [x] `watch("ativo")` standalone removido — apenas `Controller` gerencia o campo
- [x] Nenhum outro campo do formulário é afetado

### User stories endereçadas

- US2: Como sócio, quero clicar no toggle de ativo/inativo em um garçom e ver a mudança persistida ao salvar, para manter o cadastro correto.

---

## Issue 3 — U1: Enum `unidade_base` incompleto no backend ✓ Concluída

**Tipo:** HITL  
**Bloqueado por:** Nenhum — pode iniciar imediatamente

### O que construir

Expandir o enum `UnidadeBase` no backend de 2 para 5 valores (`un`, `g`, `kg`, `ml`, `l`). Criar migration Alembic correspondente para atualizar a constraint do enum no PostgreSQL.

**Backend — `backend/src/models/insumos.py`:**
```python
class UnidadeBase(str, enum.Enum):
    UNIDADE = "un"
    GRAMA = "g"
    QUILOGRAMA = "kg"
    MILILITRO = "ml"
    LITRO = "l"
```

**Migration Alembic:** alterar constraint do enum no PostgreSQL para incluir `kg`, `ml`, `l`.

Zero mudança em services, repositories ou schemas além do enum.

### Critérios de aceite

- [x] `POST /api/insumos` com `unidade_base: "kg"` → 201, dado persistido
- [x] `POST /api/insumos` com `unidade_base: "ml"` → 201, dado persistido
- [x] `POST /api/insumos` com `unidade_base: "l"` → 201, dado persistido
- [x] `POST /api/insumos` com `unidade_base: "g"` e `unidade_base: "un"` → ainda funciona (sem regressão)
- [x] Migration Alembic executa sem erro em DB limpo e em DB com dados existentes
- [x] Migration é reversível (`downgrade` desfaz sem erro quando não há dados com os novos valores)

### User stories endereçadas

- US1: Como sócio, quero cadastrar um insumo com unidade "kg" e ter a informação salva corretamente.
- US2: Como sócio, quero cadastrar um insumo com unidade "ml" ou "l" para bebidas a granel.

---

## Issue 4 — U2: Campo `quantidade_caixa` visível apenas para unidade `un` ✓ Concluída

**Tipo:** AFK  
**Bloqueado por:** Issue 3 (U1) — para teste consistente com as novas unidades

### O que construir

Em `InsumoModal.tsx`, renderizar o campo `quantidade_caixa` condicionalmente: apenas quando `unidade_base === "un"`. Para todas as outras unidades, o campo não é renderizado e não é incluído no payload (ou enviado como `null`).

**Frontend — `InsumoModal.tsx`:**
- Adicionar `const unidade = watch("unidade_base")` (ou reaproveitar se já existir).
- Envolver o bloco do campo `quantidade_caixa` com `{unidade === "un" && (...)}`.
- Quando `unidade !== "un"`: não renderizar, não submeter o campo.

### Critérios de aceite

- [x] Selecionar unidade `un` → campo `quantidade_caixa` aparece
- [x] Selecionar unidade `kg` → campo `quantidade_caixa` não aparece
- [x] Selecionar unidade `g`, `ml`, `l` → campo `quantidade_caixa` não aparece
- [x] Trocar de `un` para `kg` durante edição → campo some imediatamente
- [x] Trocar de `kg` para `un` durante edição → campo reaparece
- [x] `POST /api/insumos` com `unidade_base: "kg"` não inclui `quantidade_caixa` no payload

### User stories endereçadas

- US3: Como sócio, quero que o campo "Quantidade por caixa" apareça apenas quando a unidade for "un".

---

## Issue 5 — C3 + C4 + P1: Fixes de validação no modal de nova comanda ✓ Concluída

**Tipo:** AFK  
**Bloqueado por:** Nenhum — pode iniciar imediatamente

### O que construir

Três ajustes independentes em `NovaComandaModal.tsx`:

**C3 — Input numérico para mesa:**
- Quando `tipo_identificacao === "mesa"`: `<Input type="number" min={1} step={1} {...register("identificacao", { valueAsNumber: true })} />`
- Quando `tipo_identificacao === "nome"`: `<Input type="text" />`

**C4 — Mínimo 1 pessoa:**
- Schema Zod: `pessoas: z.array(z.string().min(1)).min(1, "Adicione ao menos uma pessoa")`
- Backend — `ComandaCreateRequest`: `pessoas: list[str] = Field(..., min_length=1)`

**P1 — Remover "(opcional)" do label:**
- Alterar label de `"Pessoas (opcional)"` para `"Pessoas"`.

### Critérios de aceite

- [x] **C3:** Selecionar tipo "mesa" → campo aceita apenas números inteiros positivos (letras ignoradas)
- [x] **C3:** Selecionar tipo "nome" → campo aceita texto livremente
- [x] **C4:** Tentar submeter formulário sem nenhuma pessoa → mensagem de erro no campo `pessoas`
- [x] **C4:** `POST /api/comandas` com `pessoas: []` → erro de validação do backend
- [x] **P1:** Label do campo pessoas exibe "Pessoas" sem "(opcional)"
- [x] Nenhuma regressão no fluxo de abertura de comanda com 1 ou mais pessoas

### User stories endereçadas

- US3: Como operador, quero que o campo de número de mesa aceite apenas números inteiros positivos.
- US4: Como operador, quero ser impedido de abrir uma comanda sem ao menos uma pessoa.
- US5: Como operador, quero que o label do campo pessoas não diga "(opcional)".

---

## Issue 6 — C2: Auto-add nome do cliente na lista de pessoas ✓ Concluída

**Tipo:** AFK  
**Bloqueado por:** Nenhum — pode iniciar imediatamente

### O que construir

Em `NovaComandaModal.tsx`, quando `tipo_identificacao === "nome"` e o campo `identificacao` não está vazio: adicionar automaticamente o valor ao array `pessoas` (se ainda não estiver na lista). Sincronização via `watch` + `useEffect`.

```ts
useEffect(() => {
  if (tipo === "nome" && identificacao.trim()) {
    const atual = getValues("pessoas") ?? [];
    if (!atual.includes(identificacao.trim())) {
      setValue("pessoas", [identificacao.trim(), ...atual]);
    }
  }
}, [tipo, identificacao]);
```

Se o operador alterar a identificação: remover o valor antigo e adicionar o novo.

### Critérios de aceite

- [x] Selecionar tipo "nome", digitar "Pedro" → "Pedro" aparece automaticamente na lista de pessoas
- [x] "Pedro" não duplicado se já estiver na lista
- [x] Alterar identificação de "Pedro" para "Ana" → "Pedro" removido da lista, "Ana" adicionada
- [x] Comportamento não ativo quando tipo é "mesa"
- [x] Pessoas adicionadas manualmente além do nome identificador permanecem na lista

### User stories endereçadas

- US2: Como operador, quero que ao digitar "Pedro" como nome da comanda, "Pedro" apareça automaticamente na lista de pessoas.

---

## Issue 7 — D1: Card CMV Hoje no Dashboard ✓ Concluída

**Tipo:** HITL  
**Bloqueado por:** Nenhum — pode iniciar imediatamente

### O que construir

Expor `cmv_hoje` no `DashboardResponse` e renderizar card "CMV Hoje" no frontend.

**Backend — `backend/src/schemas/dashboard_schemas.py`:**
```python
cmv_hoje: float
```

**Backend — `backend/src/services/dashboard_service.py`:**
- O valor `cmv` já é calculado internamente. Adicionar `cmv_hoje=float(cmv)` ao objeto de retorno.

**Frontend — `DashboardPage.tsx`:**
- Adicionar card "CMV Hoje" entre "Ticket Médio" e "Lucro Estimado Hoje":
  ```tsx
  <StatCard label="CMV Hoje" value={formatCurrency(data.cmv_hoje)} />
  ```
- Cor neutra (informativo, sem sinalização verde/vermelho).

### Critérios de aceite

- [x] `GET /api/dashboard` retorna campo `cmv_hoje: float`
- [x] Card "CMV Hoje" visível no dashboard entre os demais cards do topo
- [x] Valor do card bate com a soma do CMV de comandas fechadas no dia com insumos de custo conhecido
- [x] Cor do card é neutra (sem verde/vermelho)
- [x] Sem regressão nos demais cards (ticket médio, faturamento, etc.)

### User stories endereçadas

- US1: Como sócio, quero ver o CMV do dia em reais no dashboard para acompanhar o custo de mercadorias diariamente.

---

## Issue 8 — S1: Máscaras de input CNPJ e Telefone em Configurações ✓ Concluída

**Tipo:** AFK  
**Bloqueado por:** Nenhum — pode iniciar imediatamente

### O que construir

Em `ConfiguracoesPage.tsx`, aplicar máscara de input e validação Zod para CNPJ (`XX.XXX.XXX/XXXX-XX`) e Telefone (`(XX) XXXXX-XXXX` ou `(XX) XXXX-XXXX`).

**Máscara:** handler `onChange` puro (sem biblioteca externa) — `replace` de não-dígitos + inserção de separadores por posição.

**Validação Zod:**
```ts
cnpj: z.string().optional().refine(
  (v) => !v || /^\d{2}\.\d{3}\.\d{3}\/\d{4}-\d{2}$/.test(v),
  { message: "CNPJ inválido" }
),
telefone: z.string().optional().refine(
  (v) => !v || /^\(\d{2}\) \d{4,5}-\d{4}$/.test(v),
  { message: "Telefone inválido" }
),
```

Usar `Controller` do RHF nos dois campos para manipular `onChange` e `value` antes de passar ao RHF. Backend armazena string como recebida — zero mudança no backend.

### Critérios de aceite

- [x] Digitar "12345678000195" no campo CNPJ → formata automaticamente para "12.345.678/0001-95"
- [x] Digitar "11999998888" no campo Telefone → formata para "(11) 99999-8888"
- [x] Digitar "1133334444" no campo Telefone → formata para "(11) 3333-4444"
- [x] Submeter CNPJ com formato incorreto → mensagem "CNPJ inválido"
- [x] Submeter Telefone com formato incorreto → mensagem "Telefone inválido"
- [x] CNPJ e Telefone vazios são aceitos (campos opcionais)
- [x] Dados salvos no backend com a formatação aplicada

### User stories endereçadas

- US1: Como sócio, quero que ao digitar o CNPJ, os separadores sejam inseridos automaticamente.
- US2: Como sócio, quero que ao digitar o telefone, a formatação seja inserida automaticamente.
- US3: Como sócio, quero ver mensagem de erro se salvar CNPJ ou telefone com formato inválido.

---

## Issue 9 — CP3: Identificador interno `#0001` nas notas de compra ✓ Concluída

**Tipo:** AFK  
**Bloqueado por:** Nenhum — pode iniciar imediatamente

### O que construir

Exibir identificador interno `#${String(compra.id).padStart(4, "0")}` em toda referência à compra no frontend. Zero mudança no backend.

**Frontend:** em `ComprasPage` (listagem, modal de detalhe, toasts) prefixar com o identificador formatado.

### Critérios de aceite

- [x] Compra com `id=1` exibe "#0001" na listagem
- [x] Compra com `id=42` exibe "#0042" na listagem
- [x] Compra com `id=1000` exibe "#1000" na listagem
- [x] Identificador visível na listagem e em modais/detalhes de compra
- [x] Nenhuma chamada adicional ao backend — apenas formatação de `compra.id` existente

### User stories endereçadas

- US4: Como sócio, quero ver um identificador como "#0042" em cada compra para referenciá-la facilmente.

---

## Issue 10 — C1: Edição inline de pessoas em comanda aberta ✓ Concluída

**Tipo:** HITL  
**Bloqueado por:** Issue 5 (C4) — backend deve validar `len(pessoas) >= 1` no PATCH também

### O que construir

Em `ComandaAbertaPage.tsx`, substituir a exibição estática de pessoas por gestão inline: campo de texto + botão "Adicionar" + `×` para remover cada pessoa. Salva via `PATCH /api/comandas/:id` com o array `pessoas` atualizado.

**Frontend:**
- Estado local para edição otimista enquanto a mutação não completa.
- Visível apenas para comandas com `status === "aberta"`.

**Backend — `ComandaPatchRequest`:**
- Verificar se aceita `pessoas: Optional[list[str]]`. Se não: adicionar o campo.
- Validar `len(pessoas) >= 1` no PATCH (não permitir esvaziar lista após abertura).

### Critérios de aceite

- [x] Campo de texto + botão "Adicionar" visíveis na seção de pessoas para comanda aberta
- [x] Adicionar pessoa → aparece na lista imediatamente (otimista) e persiste via PATCH
- [x] Remover pessoa com `×` → some da lista e persiste via PATCH
- [x] Tentar remover a última pessoa → erro (lista mínima de 1)
- [x] `PATCH /api/comandas/:id` com `pessoas: []` → erro de validação
- [x] Seção de edição não aparece para comandas com status diferente de `aberta`
- [x] `GET /api/comandas/:id` após PATCH reflete a lista atualizada

### User stories endereçadas

- US1: Como operador, quero adicionar ou remover pessoas de uma comanda já aberta para corrigir a lista sem precisar cancelar e reabrir.

---

## Issue 11 — Z1: Bypass de pagamento quando total = R$0 ✓ Concluída

**Tipo:** HITL  
**Bloqueado por:** Nenhum — pode iniciar imediatamente

### O que construir

Em `FechamentoPage.tsx`, detectar `comanda.total === 0`. Se verdadeiro: substituir o formulário de pagamento por aviso informativo + botão "Confirmar Fechamento (sem cobrança)".

**Frontend:**
```tsx
<div className="rounded border border-yellow-200 bg-yellow-50 p-4 text-sm text-yellow-800">
  Total R$0,00 — todos os itens são cortesia ou desconto integral.
</div>
<Button onClick={confirmarFechamentoZero}>Confirmar Fechamento (sem cobrança)</Button>
```
- `confirmarFechamentoZero`: chamar endpoint de fechamento com `pagamentos: []`.

**Backend — `ComandaFechamentoRequest` / `comandas_service.fechar_comanda`:**
- Verificar se há guard `len(pagamentos) >= 1` que precise ser removido quando `total == 0`.
- Quando `total_calculado == 0`: aceitar `pagamentos: []` (validação `sum([]) == 0` naturalmente satisfeita).

### Critérios de aceite

- [x] Comanda com todos os itens cortesia → tela de fechamento exibe aviso amarelo e botão "Confirmar sem cobrança" (sem formulário de pagamento)
- [x] Clicar em "Confirmar Fechamento (sem cobrança)" → comanda fechada com `status=fechada`, `total=0`, `pagamentos=[]`
- [x] `GET /api/comandas/:id` após fechamento confirma `status=fechada` e `pagamentos=[]`
- [x] Comanda com `total > 0` → formulário de pagamento normal aparece (sem regressão)
- [x] Comanda com mix de itens normais e cortesia resultando em `total > 0` → fluxo normal

### User stories endereçadas

- US1: Como caixa, quero fechar comanda com total R$0 sem precisar informar método de pagamento.
- US2: Como sistema, quero que o fechamento com total R$0 seja registrado normalmente no histórico.

---

## Issue 12 — F1 + F2: Filtro Ativos/Inativos/Todos em Garçons e Métodos de Pagamento ✓ Concluída

**Tipo:** AFK  
**Bloqueado por:** Nenhum — pode iniciar imediatamente

### O que construir

Adicionar filtro de status (toggle "Todos / Ativos / Inativos") no topo de `GarconsPage` e `MetodosPagamentoPage`. Filtragem client-side sobre os dados já carregados — zero chamada adicional à API.

**Ambas as páginas:**
- Estado local: `filtro: "todos" | "ativos" | "inativos"` inicializado como `"ativos"`.
- Toggle de 3 botões no topo da listagem.
- Filtragem via `.filter(...)` nos dados já em memória.
- Padrão visual: botão selecionado com `bg-gray-900 text-white`.

### Critérios de aceite

- [x] **F1:** Toggle "Todos / Ativos / Inativos" visível no topo de `GarconsPage`
- [x] **F1:** Padrão ao carregar a página: "Ativos" selecionado
- [x] **F1:** Selecionar "Inativos" → apenas garçons inativos aparecem
- [x] **F1:** Selecionar "Todos" → todos os garçons aparecem
- [x] **F2:** Mesmo comportamento em `MetodosPagamentoPage`
- [x] Filtragem sem chamada adicional à API (apenas `.filter` no array em memória)
- [x] Botão selecionado destacado visualmente

### User stories endereçadas

- US1: Como sócio, quero filtrar a lista de garçons por "Ativos", "Inativos" ou "Todos".
- US2: Como sócio, quero filtrar a lista de métodos de pagamento por status.

---

## Issue 13 — MP1: Botão Remover método de pagamento ✓ Concluída

**Tipo:** HITL  
**Bloqueado por:** Nenhum — pode iniciar imediatamente

### O que construir

Botão "Remover" por linha em `MetodosPagamentoPage` com modal de confirmação. Hard delete com guard 409 se o método possui pagamentos históricos.

**Backend — novo endpoint `DELETE /api/metodos-pagamento/{metodo_id}`:**
```python
def delete_metodo(db: Session, metodo_id: int) -> None:
    obj = get_metodo(db, metodo_id)  # 404 se não encontrado
    count = db.execute(
        select(func.count()).where(Pagamento.metodo_pagamento_id == metodo_id)
    ).scalar()
    if count > 0:
        raise AppError(ErrorCode.CONFLICT, "Método possui histórico de pagamentos", http_status=409)
    metodos_pagamento_repository.delete(db, metodo_id)
```

**Frontend:**
- Botão "Remover" ao lado de "Editar" em cada linha.
- Modal de confirmação: "Tem certeza que deseja remover o método '{nome}'? Esta ação não pode ser desfeita."
- Se API retornar 409: toast de erro "Método de pagamento possui histórico e não pode ser removido."

### Critérios de aceite

- [x] Botão "Remover" visível por linha em `MetodosPagamentoPage`
- [x] Clicar em "Remover" abre modal de confirmação com nome do método
- [x] Confirmar remoção de método sem histórico → 204, método some da lista
- [x] `GET /api/metodos-pagamento/{id}` após remoção → 404
- [x] Tentar remover método com pagamentos históricos → 409, toast de erro exibido
- [x] Cancelar o modal de confirmação → método não é removido

### User stories endereçadas

- US3: Como sócio, quero remover um método de pagamento cadastrado por engano.
- US4: Como sistema, quero bloquear remoção de método com histórico financeiro.

---

## Issue 14 — CP1: Cancelamento de nota de compra (estorno de estoque) ✓ Concluída

**Tipo:** HITL  
**Bloqueado por:** Nenhum — pode iniciar imediatamente

### O que construir

Marcar compra como `cancelada` + gerar movimentos `ESTORNO_COMPRA` para cada item, revertendo quantidades no estoque. Custo médio não é revertido (limitação aceita).

**Backend — migration:** adicionar coluna `status` na tabela `compras`:
```python
status: Mapped[str] = mapped_column(sa.String(20), nullable=False, default="ativa")
```

**Backend — `POST /api/compras/{compra_id}/cancelar`:**
1. Buscar compra — 404 se não encontrada.
2. Guard: `compra.status == "cancelada"` → 409 `COMPRA_JA_CANCELADA`.
3. Para cada `ItemCompra`: baixar estoque + registrar `MovimentoEstoque` com `tipo=ESTORNO_COMPRA`.
4. Marcar `compra.status = "cancelada"` → commit.

Adicionar `TipoMovimento.ESTORNO_COMPRA` ao enum se não existir.

**Frontend — `ComprasPage`:**
- Botão "Cancelar Nota" por linha, apenas para `status === "ativa"`.
- Modal de confirmação com aviso de custo médio.
- Após sucesso: toast amarelo "Nota cancelada. Verifique o custo médio dos insumos afetados."
- Compras canceladas: linha em `text-gray-400` + badge "Cancelada" na coluna Status.

### Critérios de aceite

- [x] Registrar compra com 2 insumos → estoque aumenta → cancelar → estoque revertido
- [x] Movimentos `ESTORNO_COMPRA` criados para cada item da compra cancelada
- [x] `custo_medio` dos insumos não muda após cancelamento
- [x] Tentar cancelar compra já cancelada → 409
- [x] Compras canceladas exibidas com badge "Cancelada" e linha acinzentada
- [x] Botão "Cancelar Nota" não aparece para compras já canceladas
- [x] Migration executa sem erro em DB com dados existentes

### User stories endereçadas

- US1: Como sócio, quero cancelar uma nota com itens incorretos para estornar as quantidades do estoque.
- US2: Como sócio, quero ser avisado que o custo médio pode ficar impreciso após o cancelamento.
- US5: Como sistema, quero que compras canceladas apareçam com status visual diferenciado.

---

## Issue 15 — CP2: Edição de campos não-estoque de compra ✓ Concluída

**Tipo:** HITL  
**Bloqueado por:** Issue 14 (CP1) — compartilha model `Compra` com campo `status`

### O que construir

Permitir editar fornecedor, data e número da nota de uma compra ativa. Quantidades e itens não são editáveis.

**Backend — `PATCH /api/compras/{compra_id}`:**
- Aceitar `fornecedor_id`, `data_compra`, `numero_nota` no payload.
- Guard: `compra.status == "cancelada"` → 422 (não editar compra cancelada).
- Não aceitar `itens` no payload.

**Frontend — `ComprasPage`:**
- Botão "Editar" por linha (apenas para `status === "ativa"`).
- Modal de edição pré-preenchido com os 3 campos editáveis.
- Salvar via PATCH. Invalidar query de compras após sucesso.

### Critérios de aceite

- [x] Botão "Editar" visível por linha apenas para compras com `status === "ativa"`
- [x] Modal de edição abre com fornecedor, data e número da nota pré-preenchidos
- [x] Salvar edição → `PATCH` enviado → dados atualizados na listagem
- [x] Tentar editar compra cancelada (via API direta) → 422
- [x] Botão "Editar" não aparece para compras canceladas
- [x] Campos de itens/quantidades não presentes no modal de edição

### User stories endereçadas

- US3: Como sócio, quero editar fornecedor, data e número da nota sem alterar os itens para corrigir erros de preenchimento.

---

## Sequência de implementação

```
Bloco A — Bugs imediatos:     Issue 1 (BG1), Issue 2 (BG2)
Bloco B — Backend enum:       Issue 3 (U1)
Bloco C — UI independentes:   Issue 4 (U2), Issue 5 (C3+C4+P1), Issue 6 (C2), Issue 7 (D1), Issue 8 (S1), Issue 9 (CP3)
Bloco D — Features comanda:   Issue 10 (C1), Issue 11 (Z1)
Bloco E — Cadastros:          Issue 12 (F1+F2), Issue 13 (MP1)
Bloco F — Compras:            Issue 14 (CP1), Issue 15 (CP2)
```
