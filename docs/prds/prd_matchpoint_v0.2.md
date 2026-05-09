# PRD — Ajustes e Melhorias v0.2: Sistema Matchpoint

**Versão:** 0.2
**Data:** 2026-05-09
**Status:** Aprovado para desenvolvimento
**Documentos base:** `docs/prds/prd_matchpoint_v0.0.md`, `docs/prds/prd_matchpoint_v0.1.md`

---

## Visão Geral

Este documento cobre exclusivamente ajustes em funcionalidades existentes e melhorias de usabilidade identificadas após o MVP. Nenhuma feature nova de negócio é adicionada. As seções são independentes e podem ser implementadas em qualquer ordem, salvo dependências explicitadas.

---

## Índice de Itens

| ID | Área | Tipo | Descrição curta |
|----|------|------|----------------|
| BG1 | Métodos de Pagamento | Bug | Toggle ativo/inativo não persiste |
| BG2 | Garçons | Bug | Toggle ativo/inativo não persiste |
| U1 | Insumos | Fix | Enum `unidade_base` backend incompleto |
| U2 | Insumos | UX | `quantidade_caixa` visível só para `un` |
| C1 | Comanda | Feature | Edição inline de pessoas em comanda aberta |
| C2 | Comanda | Feature | Auto-add nome do cliente em pessoas na abertura |
| C3 | Comanda | Fix | Input de mesa restrito a números |
| C4 | Comanda | Rule | Mínimo 1 pessoa obrigatório para abrir comanda |
| P1 | Comanda | UX | Remover label "(opcional)" do campo pessoas |
| Z1 | Fechamento | Feature | Bypass de pagamento quando total = R$0 |
| D1 | Dashboard | Feature | Card CMV Hoje |
| S1 | Configurações | Feature | Máscaras de input CNPJ e Telefone |
| F1 | Garçons | Feature | Filtro Ativos / Inativos / Todos |
| F2 | Métodos de Pagamento | Feature | Filtro Ativos / Inativos / Todos |
| MP1 | Métodos de Pagamento | Feature | Botão Remover método de pagamento |
| CP1 | Compras | Feature | Cancelamento de nota (estorno de estoque) |
| CP2 | Compras | Feature | Edição de campos não-estoque de compra |
| CP3 | Compras | UX | Identificador interno `#0001` nas notas |

---

# Seção 1 — Correção de Bug: Toggle Ativo/Inativo (BG1, BG2)

## Problem Statement

O botão de toggle ativo/inativo em `MetodoPagamentoModal` e `GarcomModal` não persiste a mudança ao salvar. O campo `ativo` é gerenciado via `setValue` + `watch` do React Hook Form sem nunca ser `register`ado em um input HTML. Em certas condições, o valor submetido no formulário não reflete o estado visual do toggle, fazendo o campo retornar ao valor anterior após salvar.

O padrão de código é idêntico nos dois modais — mesma causa raiz, mesmo fix.

## Solution

Substituir o gerenciamento manual via `setValue`/`watch` por `Controller` do React Hook Form, que garante que o campo seja devidamente registrado e seu valor corretamente incluído no payload de submissão.

## User Stories

1. Como sócio, quero clicar no toggle de ativo/inativo em um método de pagamento e ver a mudança persistida ao salvar, para não precisar repetir a operação.
2. Como sócio, quero clicar no toggle de ativo/inativo em um garçom e ver a mudança persistida ao salvar, para manter o cadastro correto.

## Implementation Decisions

**`MetodoPagamentoModal.tsx` e `GarcomModal.tsx`:**

- Importar `Controller` do `react-hook-form`.
- Substituir o padrão atual:
  ```tsx
  const ativo = watch("ativo");
  // ...
  <button onClick={() => setValue("ativo", !ativo)} ...>
  ```
  Por `Controller` wrappando o botão de toggle:
  ```tsx
  <Controller
    name="ativo"
    control={control}
    render={({ field }) => (
      <button
        type="button"
        onClick={() => field.onChange(!field.value)}
        className={`... ${field.value ? "bg-gray-900" : "bg-gray-300"}`}
      >
        <span className={`... ${field.value ? "translate-x-5" : "translate-x-0.5"}`} />
      </button>
    )}
  />
  ```
- Remover `watch("ativo")` e `setValue` do toggle — `Controller` gerencia o estado.
- Zero mudança no backend.

## Testing Decisions

- Abrir modal de edição de método de pagamento ativo → clicar toggle → salvar → verificar que `ativo=false` foi persistido no GET subsequente.
- Repetir para garçom.

## Out of Scope

- Redesign visual do toggle.
- Qualquer mudança no backend.

---

# Seção 2 — Sistema de Unidades de Insumos (U1, U2)

## Problem Statement

**U1 — Mismatch de enum:** O backend define `UnidadeBase` com apenas dois valores (`un`, `g`), enquanto o frontend já apresenta cinco opções ao usuário (`un`, `g`, `kg`, `ml`, `l`). Ao tentar salvar um insumo com unidade `kg`, `ml` ou `l`, o backend rejeita o valor com erro de validação.

**U2 — Campo `quantidade_caixa` exibido para todas as unidades:** O campo "Quantidade por caixa" faz sentido apenas para itens contados em unidades (ex: 24 garrafas por caixa). Para insumos em `g`, `kg`, `ml` ou `l`, o campo não tem significado semântico e gera confusão.

**Decisão de design (U3 — sem conversão):** O insumo é definido na unidade de uso. Compras e ficha técnica operam sempre nessa mesma unidade. Não há conversão automática entre unidades. Exemplo: carne definida como `kg` → compra-se `1` (kg) → ficha técnica usa `0.2` (kg) por X-Burguer.

## Solution

- **U1:** Adicionar `kg`, `ml`, `l` ao enum `UnidadeBase` no backend. Criar migration Alembic correspondente.
- **U2:** Em `InsumoModal.tsx`, mostrar o campo `quantidade_caixa` apenas quando `unidade_base === "un"`. Para as demais unidades, esconder o campo completamente e não enviar o campo no payload.

## User Stories

1. Como sócio, quero cadastrar um insumo com unidade "kg" e ter a informação salva corretamente, para não receber erro ao tentar cadastrar carnes e cereais.
2. Como sócio, quero cadastrar um insumo com unidade "ml" ou "l" para bebidas a granel, para cobrir todos os insumos do bar.
3. Como sócio, quero que o campo "Quantidade por caixa" apareça apenas quando a unidade for "un", para não ver campos sem sentido ao cadastrar insumos por peso ou volume.

## Implementation Decisions

**Backend:**
- `backend/src/models/insumos.py` — expandir `UnidadeBase`:
  ```python
  class UnidadeBase(str, enum.Enum):
      UNIDADE = "un"
      GRAMA = "g"
      QUILOGRAMA = "kg"
      MILILITRO = "ml"
      LITRO = "l"
  ```
- Migration Alembic: alterar constraint do enum no PostgreSQL para incluir os novos valores.
- Zero mudança em services, repositories ou schemas — enum é o único ponto de alteração.

**Frontend — `InsumoModal.tsx`:**
- Observar o campo `unidade_base` via `watch("unidade_base")`.
- Renderizar `quantidade_caixa` condicionalmente:
  ```tsx
  {unidade === "un" && (
    <div className="space-y-1">
      <Label>Quantidade por caixa</Label>
      <Input type="number" {...register("quantidade_caixa")} />
    </div>
  )}
  ```
- Quando unidade ≠ `"un"`: não renderizar o campo e não incluir `quantidade_caixa` no payload (ou enviar `null`).

## Testing Decisions

- `POST /api/insumos` com `unidade_base: "kg"` → verificar 201 e dado persistido.
- `POST /api/insumos` com `unidade_base: "ml"` → verificar 201.
- **Frontend:** selecionar unidade `kg` → verificar que campo `quantidade_caixa` não aparece. Selecionar `un` → verificar que aparece.

## Out of Scope

- Conversão entre unidades (ex: comprar em `kg` e estoque em `g`).
- Unidades de volume adicionais (ex: `cl`, `oz`).

---

# Seção 3 — Ajustes de Comanda (C1, C2, C3, C4, P1)

## Problem Statement

Cinco problemas de usabilidade no fluxo de comanda:

1. **C1** — Após abrir uma comanda, não há forma de adicionar ou remover pessoas. O campo `pessoas` fica travado no estado da abertura.
2. **C2** — Quando `tipo_identificacao = "nome"`, o nome digitado no campo `identificacao` representa o cliente responsável, mas não é automaticamente adicionado à lista `pessoas`, obrigando o operador a digitá-lo duas vezes.
3. **C3** — O input de `identificacao` não muda de tipo quando `tipo_identificacao = "mesa"`. O operador consegue digitar texto onde deveria haver apenas números.
4. **C4** — É possível abrir uma comanda sem nenhuma pessoa associada, impossibilitando a divisão de conta e a associação de itens por pessoa.
5. **P1** — O label do campo `pessoas` exibe "(opcional)", o que contradiz a regra C4 agora obrigatória.

## Solution

1. **C1** — Adicionar gestão inline de pessoas em `ComandaAbertaPage`: input de texto + botão "Adicionar" + `×` para remover cada pessoa. Salva via `PATCH /api/comandas/:id` com o array `pessoas` atualizado.
2. **C2** — Em `NovaComandaModal`, quando `tipo = "nome"`, ao preencher `identificacao`, adicionar o valor automaticamente ao array `pessoas` (se ainda não estiver na lista). Sincronização via `watch` + `useEffect`.
3. **C3** — Em `NovaComandaModal`, quando `tipo = "mesa"`, renderizar `<Input type="number" min={1} step={1}>`. Quando `tipo = "nome"`, renderizar `<Input type="text">`.
4. **C4** — Adicionar validação Zod: `pessoas: z.array(z.string()).min(1, "Adicione ao menos uma pessoa")`. Backend: validar `len(pessoas) >= 1` no `ComandaCreateRequest`.
5. **P1** — Remover o texto "(opcional)" do label do campo `pessoas` em `NovaComandaModal`.

## User Stories

1. Como operador, quero adicionar ou remover pessoas de uma comanda já aberta, para corrigir a lista sem precisar cancelar e reabrir.
2. Como operador, quero que ao digitar "Pedro" como nome da comanda, "Pedro" apareça automaticamente na lista de pessoas, para não precisar digitá-lo duas vezes.
3. Como operador, quero que o campo de número de mesa aceite apenas números inteiros positivos, para não digitar texto onde não cabe.
4. Como operador, quero ser impedido de abrir uma comanda sem ao menos uma pessoa, para garantir que a divisão de conta funcione.
5. Como operador, quero que o label do campo pessoas não diga "(opcional)" já que o campo é obrigatório, para não ser induzido ao erro.

## Implementation Decisions

### C1 — Edição inline de pessoas em ComandaAbertaPage

**Frontend:**
- Na seção de pessoas de `ComandaAbertaPage.tsx`, substituir a exibição estática (só leitura) por:
  - Campo de texto + botão "Adicionar" (Enter ou clique).
  - Cada pessoa exibida como pill com botão `×`.
  - Ao adicionar ou remover: chamar `patchComanda({ pessoas: novaLista })`.
- Usar estado local para edição otimista enquanto a mutação não completa.
- Visível apenas para comandas com `status === "aberta"`.

**Backend:**
- `PATCH /api/comandas/:id` — já existe. Verificar se aceita `pessoas` no payload `ComandaPatchRequest`. Se não: adicionar campo `pessoas: Optional[list[str]]`.
- Validar que `len(pessoas) >= 1` mesmo no PATCH (não permitir esvaziar a lista após abertura).

### C2 — Auto-add nome do cliente

**Frontend — `NovaComandaModal.tsx`:**
- `watch(["tipo_identificacao", "identificacao"])` via `useEffect`.
- Quando `tipo === "nome"` e `identificacao` não está vazio: garantir que o valor esteja no array `pessoas`.
- Lógica:
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
- Se o operador alterar a identificação após o auto-add: remover o valor antigo e adicionar o novo.

### C3 — Input numérico para mesa

**Frontend — `NovaComandaModal.tsx`:**
- Input de `identificacao` condicionalmente tipado:
  ```tsx
  <Input
    type={tipo === "mesa" ? "number" : "text"}
    min={tipo === "mesa" ? 1 : undefined}
    step={tipo === "mesa" ? 1 : undefined}
    {...register("identificacao", { valueAsNumber: tipo === "mesa" })}
  />
  ```
- Validação Zod: quando `tipo === "mesa"`, `identificacao` deve ser string numérica positiva.

### C4 — Mínimo 1 pessoa

**Frontend — schema Zod de abertura:**
```ts
pessoas: z.array(z.string().min(1)).min(1, "Adicione ao menos uma pessoa")
```

**Backend — `ComandaCreateRequest`:**
```python
pessoas: list[str] = Field(..., min_length=1)
```

### P1 — Remover label "(opcional)"

- `NovaComandaModal.tsx`: alterar label de `"Pessoas (opcional)"` para `"Pessoas"`.

## Testing Decisions

- **C1:** PATCH de comanda aberta com `pessoas: ["Ana", "Bruno"]` → GET → verificar persistência. PATCH com `pessoas: []` → verificar erro de validação.
- **C2:** Abrir modal com `tipo=nome`, digitar "Pedro" → verificar que "Pedro" aparece automaticamente em `pessoas` sem ação extra.
- **C3:** Selecionar tipo "mesa" → tentar digitar letras no input → verificar que não são aceitas.
- **C4:** Tentar submeter formulário sem pessoas → verificar mensagem de erro no campo.

## Out of Scope

- Reordenação de pessoas.
- Edição de nome de pessoa já cadastrada na comanda (remover e adicionar novamente).

---

# Seção 4 — Fechamento com Total R$0 (Z1)

## Problem Statement

Quando todos os itens de uma comanda são cortesia ou o desconto zera o total, o fechamento fica bloqueado: o formulário exige seleção de método de pagamento e a validação `soma_pagamentos == total` nunca é satisfeita com `total = 0`.

## Solution

Ao carregar `FechamentoPage`, detectar `comanda.total == 0`. Se verdadeiro: substituir o formulário de pagamento por botão direto "Confirmar Fechamento (sem cobrança)". Backend aceita `pagamentos: []` quando `total == 0`.

## User Stories

1. Como caixa, quero fechar uma comanda cujo total é R$0,00 (todos os itens cortesia ou desconto total) sem precisar informar método de pagamento, para não ficar bloqueado em um formulário que não faz sentido.
2. Como sistema, quero que o fechamento com total R$0 seja registrado normalmente no histórico, para que a comanda apareça nos relatórios com valor zerado.

## Implementation Decisions

**Frontend — `FechamentoPage.tsx`:**
- Ao montar o componente, verificar `comanda.total === 0`.
- Se verdadeiro: renderizar em vez do formulário de pagamento:
  ```tsx
  <div className="rounded border border-yellow-200 bg-yellow-50 p-4 text-sm text-yellow-800">
    Total R$0,00 — todos os itens são cortesia ou desconto integral.
  </div>
  <Button onClick={confirmarFechamentoZero}>Confirmar Fechamento (sem cobrança)</Button>
  ```
- `confirmarFechamentoZero`: chamar endpoint de fechamento com `pagamentos: []`.

**Backend — `ComandaFechamentoRequest` / `comandas_service.fechar_comanda`:**
- Aceitar `pagamentos: []` quando `total_calculado == 0`.
- Validação atual: `sum(pagamentos) == total` → quando `total == 0`, `sum([]) == 0` satisfaz a condição naturalmente.
- Verificar se a lógica atual já comporta isso ou se há guard `len(pagamentos) >= 1` que precise ser removido.

## Testing Decisions

- Abrir comanda → lançar 1 item com cortesia → fechar → verificar que tela de fechamento exibe botão "Confirmar sem cobrança" e não o formulário de pagamento.
- Confirmar fechamento → verificar status `fechada`, `total = 0`, `pagamentos = []` no GET.
- Comanda com total > 0 → verificar que formulário de pagamento normal aparece (sem regressão).

## Out of Scope

- Comanda com mix de itens normais e cortesia que resulte em total > 0: fluxo normal de pagamento.

---

# Seção 5 — Dashboard: Card CMV Hoje (D1)

## Problem Statement

O backend já calcula `cmv_hoje` internamente para derivar `lucro_estimado_hoje`, mas não expõe o valor bruto do CMV na resposta da API. O cliente quer visualizar o CMV diariamente no dashboard para acompanhar o custo operacional em tempo real.

## Solution

Expor `cmv_hoje` como campo adicional no `DashboardResponse`. Renderizar card "CMV Hoje" no frontend ao lado dos cards existentes.

## User Stories

1. Como sócio, quero ver o CMV do dia em reais no dashboard, para acompanhar o custo de mercadorias diariamente sem precisar acessar relatórios.

## Implementation Decisions

**Backend — `backend/src/schemas/dashboard_schemas.py`:**
- Adicionar campo ao `DashboardResponse`:
  ```python
  cmv_hoje: float
  ```

**Backend — `backend/src/services/dashboard_service.py`:**
- Já calcula `cmv`. Adicionar ao objeto de retorno:
  ```python
  cmv_hoje=float(cmv),
  ```

**Frontend — `DashboardPage.tsx`:**
- Adicionar card "CMV Hoje" na área de cards do topo, entre "Ticket Médio" e "Lucro Estimado Hoje":
  ```tsx
  <StatCard label="CMV Hoje" value={formatCurrency(data.cmv_hoje)} />
  ```
- Cor neutra (sem sinalização verde/vermelho — é informativo, não alerta).

## Testing Decisions

- `GET /api/dashboard` → verificar que response inclui `cmv_hoje: float`.
- Com comandas fechadas no dia com insumos de custo conhecido → verificar que `cmv_hoje` bate com soma esperada.

## Out of Scope

- CMV do mês (cobre-se pelo DRE já existente).
- Meta ou threshold de CMV no dashboard.

---

# Seção 6 — Configurações: Máscaras de Input (S1)

## Problem Statement

Os campos CNPJ e Telefone em Configurações → Estabelecimento têm apenas placeholder indicando o formato esperado (`00.000.000/0000-00` e `(11) 99999-9999`), mas nenhuma máscara de entrada. O operador pode salvar valores em formato incorreto sem receber feedback.

## Solution

Aplicar máscara de input e validação Zod para CNPJ e Telefone.

## User Stories

1. Como sócio, quero que ao digitar o CNPJ, os pontos, barra e traço sejam inseridos automaticamente no formato correto, para não errar a formatação.
2. Como sócio, quero que ao digitar o telefone, parênteses, espaço e traço sejam inseridos automaticamente, para não precisar digitar a formatação manualmente.
3. Como sócio, quero ver mensagem de erro se salvar um CNPJ ou telefone com formato inválido, para saber que preciso corrigir.

## Implementation Decisions

**Frontend — `ConfiguracoesPage.tsx`:**

- CNPJ: máscara `XX.XXX.XXX/XXXX-XX` aplicada via handler `onChange` que formata a string conforme o usuário digita (sem biblioteca externa — manipulação pura de string com `replace` de não-dígitos + inserção de separadores por posição).
- Telefone: máscara `(XX) XXXXX-XXXX` (celular) ou `(XX) XXXX-XXXX` (fixo) — detectar automaticamente pelo comprimento após o DDD.

**Validação Zod — `estSchema`:**
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

- Backend: armazena string como recebida — sem mudança de schema.
- Usar `Controller` do RHF para os campos com máscara (permite manipular `onChange` e `value` antes de passar ao RHF).

## Testing Decisions

- Digitar "12345678000195" no campo CNPJ → verificar que formata para "12.345.678/0001-95" automaticamente.
- Submeter CNPJ com 13 dígitos → verificar mensagem "CNPJ inválido".
- Digitar "11999998888" → verificar que formata para "(11) 99999-8888".

## Out of Scope

- Validação de dígitos verificadores do CNPJ (formato apenas).
- Máscara para campo Endereço (texto livre).

---

# Seção 7 — Garçons e Métodos de Pagamento: Filtro e Remoção (F1, F2, MP1)

## Problem Statement

1. **F1 / F2** — As listagens de Garçons e Métodos de Pagamento mostram todos os registros misturados (ativos e inativos) sem opção de filtro. Com o tempo, a lista de inativos polui a visualização e dificulta encontrar os registros em uso.
2. **MP1** — Não existe botão para remover um método de pagamento. Atualmente só é possível desativá-lo. Métodos cadastrados por engano não podem ser eliminados.

## Solution

1. **F1 / F2** — Adicionar filtro de status (toggle "Todos / Ativos / Inativos") no topo de `GarconsPage` e `MetodosPagamentoPage`. Filtragem client-side sobre os dados já carregados.
2. **MP1** — Adicionar botão "Remover" por linha em `MetodosPagamentoPage`. Hard delete com guard: bloqueado com erro 409 se o método possui pagamentos históricos associados.

## User Stories

1. Como sócio, quero filtrar a lista de garçons por "Ativos", "Inativos" ou "Todos", para não ver registros que não estão em uso.
2. Como sócio, quero filtrar a lista de métodos de pagamento por status, pelo mesmo motivo.
3. Como sócio, quero remover um método de pagamento cadastrado por engano, para manter a lista limpa.
4. Como sistema, quero bloquear a remoção de um método de pagamento que já foi utilizado em comandas históricas, para não quebrar o histórico financeiro.

## Implementation Decisions

### F1 — Filtro em GarconsPage

**Frontend — `GarconsPage.tsx`:**
- Estado local: `filtro: "todos" | "ativos" | "inativos"` inicializado como `"ativos"` (padrão mais útil).
- Toggle de 3 opções renderizado com botões no topo da listagem.
- Filtragem via `garcons.filter(...)` sobre os dados carregados — zero chamada adicional à API.
- Padrão visual: botões com borda, selecionado com `bg-gray-900 text-white`.

### F2 — Filtro em MetodosPagamentoPage

- Mesmo padrão que F1. Estado `filtro: "todos" | "ativos" | "inativos"` inicializado como `"ativos"`.

### MP1 — Botão Remover em MetodosPagamentoPage

**Frontend:**
- Adicionar botão "Remover" por linha, ao lado do botão "Editar".
- Modal de confirmação: "Tem certeza que deseja remover o método '{nome}'? Esta ação não pode ser desfeita."
- Se API retornar 409: toast de erro "Método de pagamento possui histórico e não pode ser removido."

**Backend:**
- Novo endpoint: `DELETE /api/metodos-pagamento/{metodo_id}`.
- Service `metodos_pagamento_service.delete_metodo`:
  ```python
  def delete_metodo(db: Session, metodo_id: int) -> None:
      obj = get_metodo(db, metodo_id)  # 404 se não encontrado
      # guard: verificar referências em tabela pagamentos
      count = db.execute(
          select(func.count()).where(Pagamento.metodo_pagamento_id == metodo_id)
      ).scalar()
      if count > 0:
          raise AppError(ErrorCode.CONFLICT, "Método possui histórico de pagamentos", http_status=409)
      metodos_pagamento_repository.delete(db, metodo_id)
  ```
- Repository: `DELETE FROM metodos_pagamento WHERE id = :id`.

## Testing Decisions

- **Filtro:** montar página com mix de ativos/inativos → selecionar "Ativos" → verificar que apenas ativos aparecem.
- **MP1 sem histórico:** `DELETE /api/metodos-pagamento/{id}` de método sem pagamentos → 204. GET → 404.
- **MP1 com histórico:** `DELETE` de método com pagamentos associados → 409 com código `CONFLICT`.

## Out of Scope

- Filtro por nome/busca textual nas listagens.
- Remoção de garçons (garçons são apenas desativados — possuem histórico em comandas).
- Paginação nas listagens.

---

# Seção 8 — Compras: Gestão de Notas (CP1, CP2, CP3)

## Problem Statement

Após registrar uma compra, não há forma de corrigir ou cancelar a nota. Erros comuns:
- Fornecedor errado
- Data incorreta
- Número de nota digitado errado
- Itens ou quantidades incorretas (requer estorno e nova entrada)

Para itens/quantidades, o custo médio ponderado é recalculado na entrada. Reverter a fórmula com precisão requer os valores originais pré-compra, que não são armazenados — tornando a edição de quantidades inviável sem introduzir imprecisões de custo.

Adicionalmente, as compras não têm identificador interno visível, dificultando referenciá-las na operação.

## Solution

- **CP1 — Cancelamento (estorno):** Marcar compra como `cancelada` + gerar movimentos de saída (`ESTORNO_COMPRA`) para cada item, revertendo as quantidades no estoque. Custo médio não é revertido (limitação aceita, com toast de aviso).
- **CP2 — Edição de campos não-estoque:** Permitir editar fornecedor, data e número da nota. Quantidades e itens não são editáveis.
- **CP3 — Identificador interno:** Exibir `#${id.toString().padStart(4, "0")}` no frontend. Zero mudança no backend.

## User Stories

1. Como sócio, quero cancelar uma nota de compra registrada com itens incorretos, para estornar as quantidades do estoque sem precisar de ajuste manual.
2. Como sócio, quero ser avisado que o custo médio pode ficar impreciso após o cancelamento, para saber que pode ser necessário registrar uma nova compra correta.
3. Como sócio, quero editar o fornecedor, a data e o número da nota de uma compra sem alterar os itens, para corrigir erros de preenchimento sem impacto no estoque.
4. Como sócio, quero ver um identificador como "#0042" em cada compra, para referenciá-la facilmente na operação do dia.
5. Como sistema, quero que compras canceladas apareçam com status visual diferenciado na listagem, para distinguir do histórico válido.

## Implementation Decisions

### CP1 — Cancelamento (estorno)

**Backend:**

- Migration Alembic: adicionar coluna `status` na tabela `compras`:
  ```python
  status: Mapped[str] = mapped_column(
      sa.String(20), nullable=False, default="ativa"
  )
  ```
  Valores possíveis: `"ativa"` | `"cancelada"`.

- Novo endpoint: `POST /api/compras/{compra_id}/cancelar`.
- Service `compras_service.cancelar_compra`:
  1. Buscar compra — 404 se não encontrada.
  2. Guard: se `compra.status == "cancelada"` → 409 com `COMPRA_JA_CANCELADA`.
  3. Para cada `ItemCompra` da compra:
     - Buscar `Insumo` com lock (`FOR UPDATE`).
     - `novo_estoque = insumo.estoque_atual - item.quantidade`.
     - `estoque_repository.update_estoque_e_custo(db, insumo.id, novo_estoque, insumo.custo_medio)` — custo médio mantido.
     - Registrar `MovimentoEstoque` com `tipo=ESTORNO_COMPRA`, `quantidade=-item.quantidade`, `saldo_apos=novo_estoque`, `compra_id=compra.id`.
  4. Marcar `compra.status = "cancelada"`.
  5. `db.commit()`.

- Adicionar `TipoMovimento.ESTORNO_COMPRA` ao enum `TipoMovimento` se não existir.

**Frontend:**
- Em `ComprasPage` (listagem): botão "Cancelar Nota" por linha, apenas para compras com `status === "ativa"`.
- Modal de confirmação:
  > "Tem certeza que deseja cancelar esta nota? As quantidades serão retiradas do estoque. O custo médio dos insumos não será revertido — se necessário, registre uma nova compra com os valores corretos."
- Após confirmação bem-sucedida: toast amarelo "Nota cancelada. Verifique o custo médio dos insumos afetados."
- Compras canceladas exibidas com linha em `text-gray-400` e badge "Cancelada" na coluna Status.

### CP2 — Edição de campos não-estoque

**Backend:**
- Novo endpoint: `PUT /api/compras/{compra_id}` (ou `PATCH`) — aceitar `fornecedor_id`, `data_compra`, `numero_nota`.
- Guard: se `compra.status == "cancelada"` → 422 (não editar compra cancelada).
- Não aceitar `itens` no payload.

**Frontend:**
- Botão "Editar" por linha na listagem (apenas para `status === "ativa"`).
- Modal de edição pré-preenchido com os 3 campos editáveis.
- Salvar via PATCH. Invalidar query de compras após sucesso.

### CP3 — Identificador interno

**Frontend:**
- Em toda referência à compra (listagem, modal de detalhe, toast): prefixar com:
  ```ts
  `#${String(compra.id).padStart(4, "0")}`
  ```
- Zero mudança no backend.

## Testing Decisions

- **CP1:** Registrar compra com 2 insumos → verificar estoque aumentou → cancelar → verificar estoque reverteu e movimentos `ESTORNO_COMPRA` criados. Tentar cancelar mesma compra novamente → 409.
- **CP1 custo médio:** verificar que `custo_medio` do insumo não mudou após o cancelamento.
- **CP2:** PATCH de compra ativa com novo fornecedor → verificar persistência. PATCH de compra cancelada → 422.
- **CP3:** Verificar que compra com `id=42` exibe "#0042" na UI.

## Out of Scope

- Edição de itens ou quantidades da compra (requer estorno + nova entrada).
- Reversão do custo médio após cancelamento.
- Histórico de edições da compra.
- Importação de notas via XML de NFe.

## Further Notes

O custo médio ponderado é calculado na entrada e não armazenado em versões históricas. Após um cancelamento/estorno, o custo médio reflete a média das entradas restantes sem a entrada cancelada — mas como o cálculo é acumulativo, haverá imprecisão residual. O toast de aviso ao cancelar é suficiente para comunicar essa limitação no MVP.

---

## Sequência de Implementação Recomendada

```
Bloco A (bugs, sem dependências):   BG1, BG2
Bloco B (backend enum):             U1
Bloco C (UI independentes):         U2, C2, C3, C4, P1, D1, S1, CP3
Bloco D (feature comanda):          C1, Z1
Bloco E (cadastros):                F1, F2, MP1
Bloco F (compras):                  CP1, CP2
```

BG1 e BG2 primeiro — são bugs ativos que afetam operação. U1 antes de U2 (U2 depende dos novos valores do enum para teste consistente). CP1 antes de CP2 (compartilham o model `Compra` com campo `status`).
