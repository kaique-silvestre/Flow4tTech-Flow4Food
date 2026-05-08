# Melhorias Pós-MVP — Sistema Matchpoint

> Documento para registrar ideias e mudanças planejadas após a entrega do MVP (12/05/2026).
> Cada melhoria é numerada sequencialmente.

---

## Sequência de implementação

```
Fase 1 (UX triviais — independente):  M003, M004, M015
Fase 2 (Base arquitetural):           M000
Fase 3 (Dependem de M000):            M001, M002
Fase 4 (Comanda UX):                  M005, M006, M007
Fase 5 (Navbar):                      M008, M009, M011
Fase 6 (Dashboard/Relatórios):        M010, M013, M014, M016
Fase 7 (Dados avançados):             M012, M017
```

---

## M000 — Reformulação arquitetural: eliminação de `Item` unificado → separação em `Insumo` e `Produto`

**Status:** Planejado — prioridade máxima, base para M001 e M002
**Estratégia de migração:** Hard cutover — migration Alembic por passo (granular), sem dual-write.

### Nova lógica do sistema

```
COMPRAS (registro de entrada)
    ↓
  INSUMO (estoque físico: pão, carne, queijo, Coca-Cola)
    ↓
  ESTOQUE (view do saldo atual de cada insumo)

CARDÁPIO (cadastro de produtos vendáveis)
    └── PRODUTO (ex: X-Burguer, Coca-Cola)
            └── FICHA TÉCNICA → define quais insumos e quantidades descontar
                    ex: X-Burguer = 1 pão + 200g carne + 50g queijo
                    ex: Coca-Cola = 1 Coca-Cola (insumo)

COMANDA → lança Produtos → ao fechar, explode ficha técnica → baixa Insumos do Estoque
```

### Entidades resultantes

#### Insumo (substitui `Item` com `vendavel=false`)

| Campo | Descrição |
|-------|-----------|
| `nome` | Ex: "Pão de hambúrguer", "Coca-Cola Lata", "Carne moída" |
| `categoria_id` | FK para categorias |
| `unidade_base` | `un` ou `g` |
| `quantidade_caixa` | Para itens em caixa (ex: 24 un por caixa) |
| `custo_medio` | Calculado por média ponderada nas compras |
| `estoque_atual` | Saldo atualizado pelas movimentações |
| `ativo` | Soft delete |

- Insumos são registrados **exclusivamente via Compras**.
- Insumos aparecem no **Estoque** (view do saldo).
- Insumos **nunca** aparecem em comandas diretamente.

#### Produto (substitui `Item` com `vendavel=true`)

| Campo | Descrição |
|-------|-----------|
| `nome` | Ex: "X-Burguer", "Coca-Cola", "Balde 6 LongNeck" |
| `categoria_id` | FK para categorias |
| `preco_venda` | Preço cobrado ao cliente |
| `ativo` | Soft delete — produto com histórico em comanda nunca é hard deleted |

- Produtos são cadastrados no **Cardápio**.
- Produtos aparecem nas **Comandas** para lançamento.
- Produtos **não têm estoque próprio** — o estoque é dos seus insumos.
- CMV do produto = soma dos custos dos insumos da ficha técnica.
- Produto sem ficha técnica vende sem baixar estoque (ex: couvert, serviço).

#### Ficha Técnica (relação Produto → Insumos)

| Campo | Descrição |
|-------|-----------|
| `produto_id` | FK para produtos |
| `insumo_id` | FK para insumos |
| `quantidade` | Quantidade do insumo a descontar por unidade do produto |

> `unidade` **não** existe na ficha técnica — herdada de `insumo.unidade_base`.

**Exemplos:**

| Produto | Insumo | Qtd |
|---------|--------|-----|
| X-Burguer | Pão de hambúrguer | 1 |
| X-Burguer | Carne moída | 200 |
| X-Burguer | Queijo mussarela | 50 |
| Coca-Cola | Coca-Cola Lata | 1 |
| Balde 6 LongNeck | Heineken Long Neck | 6 |

### Impacto técnico

**Backend — migrations Alembic (uma por passo):**
1. Criar tabela `insumos` (campos acima).
2. Criar tabela `produtos` (campos acima).
3. Criar tabela `ficha_tecnica` (`produto_id`, `insumo_id`, `quantidade`).
4. Migrar dados de `itens`: `vendavel=false` → `insumos`; `vendavel=true` → `produtos`.
5. Migrar `componentes_ficha` → `ficha_tecnica` (mapear `item_composto_id` → `produto_id`, `insumo_id` permanece).
6. Atualizar `compras` e `itens_compra`: `item_id` → `insumo_id`.
7. Atualizar `itens_comanda`: `item_id` → `produto_id`.
8. Atualizar `movimentos_estoque`: `item_id` → `insumo_id` (FK migrada, histórico preservado).
9. Deprecar tabelas `itens`, `fichas_tecnicas`, `componentes_ficha`.

**Backend — mudanças nos serviços:**
- `compras_service`: registrar entrada em `insumos`, não em `itens`.
- `estoque_service`: operar sobre `insumos`.
- `comanda_service`: ao fechar, explodir ficha técnica de `produtos` → baixar `insumos` (pular se produto sem ficha).
- `relatorio_service`: atualizar queries para novas tabelas.

**Frontend:**
- Remover referências a `Item` unificado com flag `vendavel`.
- Compras: seletor de insumos.
- Estoque: view de insumos.
- Cardápio: CRUD de produtos com ficha técnica.
- Comandas: lançamento de produtos.

### Critérios de aceite

- Compras registra somente insumos; insumos aparecem no Estoque.
- Cardápio permite criar/editar produtos com ficha técnica de insumos.
- Ao fechar comanda com X-Burguer, desconta pão + carne + queijo do estoque de insumos.
- Produto sem ficha fecha normalmente sem baixar estoque.
- CMV de produto calculado a partir do custo médio dos insumos da ficha técnica.
- Histórico de comandas e relatórios preservados após migração.

---

## M001 — Tela de Cardápio: CRUD de Produtos com Ficha Técnica

**Status:** Planejado — depende de M000
**Origem:** Com a nova arquitetura (M000), Cardápio é uma seção própria para gerenciar Produtos vendáveis.

### Solução

Nova tela **Cardápio** no menu lateral:

```
Menu lateral:
│ 📊 Dashboard    │
│ 🍺 Comandas     │
│ 🍽️ Cardápio     │  ← CRUD de Produtos
│ 📦 Estoque      │
│ 🛒 Compras      │
│ 📋 Cadastros    │
│ 📈 Relatórios   │
│ ⚙️ Config.      │
```

**Listagem de Produtos:**

| Coluna | Descrição |
|--------|-----------|
| Nome | Nome do produto |
| Categoria | Categoria do produto |
| Preço de venda | `preco_venda` |
| Custo (ficha) | Soma dos custos dos insumos da ficha técnica |
| CMV % | `(custo / preco) × 100` |
| Lucro bruto | `preco_venda - custo_ficha` |

CMV com coloração: verde (< 30%), amarelo (30–50%), vermelho (> 50%).

**Formulário de cadastro de Produto:**

```
Nome:        [_______________________________]
Categoria:   [Selecione...              ▼]
Preço:       [R$ ______]

FICHA TÉCNICA (insumos que este produto consome):
┌────────────────────────────────────────────────┐
│ Insumo              Quantidade                  │
│ [Pão hambúrg.  ▼]   [1]             [✕]        │
│ [Carne moída   ▼]   [200]           [✕]        │
│ [Queijo        ▼]   [50]            [✕]        │
│ [+ Adicionar insumo]                           │
└────────────────────────────────────────────────┘

Custo calculado: R$ 11,30
CMV: 40,4% | Lucro bruto: R$ 16,70
```

> Coluna "Unidade" removida do formulário — exibida inline ao lado da quantidade (ex: "200 g") usando `insumo.unidade_base`.

### Impacto técnico

- Frontend: nova página `CardapioPage.tsx` + `ProdutoModal.tsx`, rota `/cardapio`.
- Backend: endpoints CRUD para `produtos` e `ficha_tecnica`.
- Seletor de insumos na ficha técnica busca em `GET /api/insumos`.

### Critérios de aceite

- CRUD completo de produtos (criar, editar, desativar via `ativo=false`).
- Ficha técnica opcional — produto sem ficha é válido.
- CMV e lucro bruto calculados em tempo real ao montar a ficha.
- Produtos sem ficha ou com insumos sem custo exibem "—" no CMV.

---

## M002 — Atalho rápido para cadastrar insumo em Nova Compra

**Status:** Planejado — depende de M000
**Origem:** Ao registrar uma compra com insumo novo, operador precisa sair do fluxo para cadastrá-lo separadamente.

### Problema

A tela `/compras/nova` já tem atalho `[+ Cadastrar novo fornecedor]` inline. O campo de insumos não tem equivalente — se o insumo não existe, o operador abandona o formulário.

### Solução

Adicionar link `[+ Cadastrar novo insumo]` abaixo do campo de busca:

```
INSUMOS COMPRADOS:
┌─────────────────────────────────────────────────────────────┐
│ Insumo                Qtd    Unitário    Total               │
│ [Selecione...     ▼]  [___]  [R$ ___]   [R$ ___]  [✕]       │
│ [+ Cadastrar novo insumo]                                    │
└─────────────────────────────────────────────────────────────┘
```

Modal de cadastro de insumo (campos mínimos: nome, categoria, unidade). Ao salvar, insumo aparece selecionado na linha.

### Impacto técnico

- Frontend: modal `InsumoModal.tsx` disparado inline na tela de Nova Compra.
- Ao fechar com sucesso, invalidar cache de insumos e pré-selecionar o criado.
- Zero mudança em backend além dos endpoints de M000.

### Critérios de aceite

- Link `[+ Cadastrar novo insumo]` visível abaixo do seletor em Nova Compra.
- Modal abre sem sair da tela.
- Insumo criado aparece selecionado na linha.
- Dados já preenchidos no formulário de compra são preservados.

---

## M003 — Botão de voltar na tela de comanda aberta

**Status:** Planejado
**Origem:** Usabilidade — operador sem forma de retornar à lista de comandas sem fechar a comanda atual.

### Problema

Na rota `/comandas/:id`, não há forma de voltar para `/comandas` sem acionar o fechamento.

### Solução

```
┌──────────────────────────────────────────────────────────────────┐
│  ← Voltar   COMANDA #003 — MARIA (Mesa 2)                        │
```

- Navega para `/comandas`. Não fecha, não altera a comanda.

### Impacto técnico

- Apenas frontend — `navigate('/comandas')` no header.

### Critérios de aceite

- Botão "← Voltar" visível no topo da tela `/comandas/:id`.
- Comanda permanece `aberta` após navegação.
- Não aparece na tela de fechamento.

---

## M004 — Remover casas decimais desnecessárias em quantidade de itens lançados

**Status:** Planejado
**Origem:** Itens aparecem como "3.000" em vez de "3" na listagem da comanda.

### Solução

- `quantidade % 1 === 0` → exibir sem decimais (ex: `3`)
- Quantidade fracionária → exibir com precisão adequada (ex: `0.250`)

### Impacto técnico

- Apenas frontend — helper de formatação em `lib/format.ts`.

### Critérios de aceite

- Quantidade `3` exibe `3`, não `3.000`.
- Quantidade fracionária exibe corretamente.

---

## M005 — Edição de garçom e identificação em comanda aberta

**Status:** Planejado
**Origem:** Erro de cadastro na abertura não tem correção sem fechar e reabrir.

### Solução

Botão `[✏]` ao lado do garçom e da identificação no cabeçalho:

```
│  ← Voltar   COMANDA #003 — MARIA [✏]   Garçom: João [✏]         │
```

Salva via `PATCH /api/comandas/:id`. Sem modal de confirmação — edição inline direta.

### Impacto técnico

- Frontend: inline edit sem modal de confirmação.
- Backend: `PATCH /api/comandas/:id` aceita `identificacao` e `garcom_id` para status `aberta`.

### Critérios de aceite

- Edição disponível apenas em comandas `aberta`.
- Alterar garçom reflete nos relatórios.
- Sem modal de confirmação.

---

## M006 — Fechamento: "Sem divisão" pré-selecionado + valor preenchido automaticamente

**Status:** Planejado
**Origem:** Operador precisa selecionar opção e digitar valor manualmente no fluxo mais comum.

### Solução

- Ao carregar tela de fechamento: pré-selecionar "Sem divisão".
- Campo de valor preenchido com o total da comanda.

### Impacto técnico

- Apenas frontend — estado inicial do formulário.

### Critérios de aceite

- Tela abre com "Sem divisão" marcado e valor preenchido.
- Alterar modo de divisão reseta o campo adequadamente.

---

## M007 — Fechamento: "Dividir entre N pessoas" calcula valor por pessoa automaticamente

**Status:** Planejado
**Origem:** Operador precisa calcular manualmente o valor por pessoa.

### Solução

```
Número de pessoas: [ 3 ]
Valor por pessoa:  R$ 26,70   ← calculado automaticamente
```

### Impacto técnico

- Apenas frontend — cálculo reativo.

### Critérios de aceite

- Valor por pessoa atualiza em tempo real ao digitar N.
- Soma bate com o total (sem perda de centavos).

---

## M008 — Navbar: ícones visíveis com menu colapsado

**Status:** Planejado
**Origem:** Menu colapsado remove ícones, perdendo referência visual.

### Solução

Menu colapsado mantém ícones; expandido mostra ícone + texto. Estado padrão: **expandido**.

### Critérios de aceite

- Ícones visíveis em ambos os estados.
- Tooltip ao hover no estado colapsado.
- Estado padrão: expandido.
- Estado persiste em `localStorage` com key `sidebar_collapsed` (booleano).

---

## M009 — Navbar: Cadastros como dropdown/submenu

**Status:** Concluído ✓ (2026-05-08)
**Origem:** Cadastros agrupa subseções — acesso direto pelo menu melhora navegação.

### Solução

```
│ 📋 Cadastros ▾     │
│    └ Categorias    │
│    └ Fornecedores  │
│    └ Garçons       │
│    └ Pagamentos    │
```

> "Itens" removido do dropdown — não existe mais como seção unificada após M000.
> Insumos são gerenciados via Compras; Produtos via Cardápio.

### Critérios de aceite

- Dropdown exibe: Categorias, Fornecedores, Garçons, Pagamentos.
- Subitem ativo destacado.
- Hover no ícone colapsado abre submenu flutuante.

---

## M010 — Página índice de Relatórios

**Status:** Concluído ✓ (2026-05-08)
**Origem:** Rota `/relatorios` exibe placeholder — sub-relatórios inacessíveis pela interface.

### Solução

Página índice com cards para cada relatório disponível em `/relatorios`.

### Critérios de aceite

- Rota `/relatorios` exibe página índice.
- Cada card navega para a sub-rota correta.
- Placeholder removido.

---

## M011 — Navbar: toggle via ícone burger (☰)

**Status:** Planejado
**Origem:** Botão de colapso do menu deve ser ícone burger padronizado, sempre visível.

### Solução

Ícone `☰` fixo no topo do menu, alternando colapsado/expandido. Combinado com M008.
Key localStorage: `sidebar_collapsed` (compartilhada com M008).

### Critérios de aceite

- Ícone `☰` visível em ambos os estados.
- Estado persiste em `localStorage` com key `sidebar_collapsed`.

---

## M012 — Categorias com subcategorias

**Status:** Planejado — ajustado para refletir M000
**Origem:** Necessidade de organização mais granular (ex: Bebidas → Cervejas, Refrigerantes).

### Problema

Modelo atual de `Categoria` tem apenas `id` e `nome` — sem hierarquia.

### Impacto técnico

**Backend:**
- Adicionar `parent_id` (FK para `categorias.id`, nullable) na tabela `categorias`.
- Máximo 2 níveis (pai + filho) — validação no backend bloqueia subcategoria de subcategoria.
- Migration Alembic necessária.
- API retorna árvore hierárquica.
- Tanto **Insumos** quanto **Produtos** vinculam-se a categorias (podem ser subcategorias).

**Frontend:**
- Cadastros → Categorias: exibir hierarquia em tree/accordion.
- Formulário: campo opcional "Categoria pai".
- Seletores em Insumos (Compras) e Produtos (Cardápio): subcategorias indentadas.

### Critérios de aceite

- Possível criar categorias pai e subcategorias (máximo 2 níveis).
- Backend rejeita criação de subcategoria de subcategoria.
- Subcategorias indentadas nos seletores.
- Excluir categoria pai bloqueia se houver subcategorias ativas.

---

## M013 — Comandas: alternância visual entre lista e cards

**Status:** Planejado
**Origem:** Cards facilitam leitura rápida em dias de pico.

### Solução

Toggle `[≡ Lista] / [⊞ Cards]` no topo da tela. Cards exibem 3 por linha em telas largas, 2 em menores. Apenas visual — zero impacto na lógica de comandas.

### Critérios de aceite

- Toggle visível e funcional.
- Preferência salva em localStorage.
- Clicar em card ou linha abre a comanda normalmente.

---

## M014 — Separação de Histórico: comandas do dia vs. todas as anteriores

**Status:** Planejado
**Origem:** "Histórico" em Comandas deve mostrar somente o dia atual; histórico geral deve ser aba separada.

### Solução

- **Dentro de Comandas:** seção "Histórico do dia" → somente `status=fechada` com `data_fechamento` no dia atual.
- **Nova aba no menu:** `📜 Histórico` → `/historico` → todas as comandas fechadas (qualquer data) com filtros.

### Critérios de aceite

- "Histórico do dia" em Comandas: somente fechadas do dia atual.
- Aba "Histórico" no menu: todas as anteriores com filtros.
- As duas seções não se sobrepõem.

---

## M015 — Navbar: correção do estado ativo (múltiplas abas destacadas)

**Status:** Planejado
**Origem:** Bug — ao acessar "Histórico", a aba "Estoque" também aparece destacada.

### Solução

Garantir prop `end` em cada `NavLink` (React Router) para correspondência exata de rota.

### Impacto técnico

- Apenas frontend — `Sidebar.tsx`.

### Critérios de aceite

- Somente a aba da rota atual fica destacada.

---

## M016 — Dashboard: revisão dos dados exibidos

**Status:** Planejado
**Origem:** Dados atuais não refletem necessidades de acompanhamento financeiro.

### Mudanças

**Remover:** card "Lucro estimado" e calendário atual (heatmap de dias).

**Manter:** faturamento do mês atual, faturamento dos últimos 30 dias, cards operacionais.

**Adicionar:**
1. Tab "Histórico" — entrada (faturamento) e saída (compras) por dia, com filtro de período.
2. Calendário anual — 12 meses do ano corrente com faturamento e gasto por mês.

```
DASHBOARD  [ Resumo ]  [ Histórico ]

Calendário 2026:
       Jan   Fev   Mar   Abr   Mai   Jun  ...
Fat.:  R$0   R$0   R$0   R$0  R$4k   —
Gasto: —     —     —     —   R$1.8k  —
```

### Critérios de aceite

- Card "Lucro estimado" removido.
- Calendário anual com faturamento e gasto mensais.
- Tab "Histórico" com entrada/saída por dia.

---

## M017 — Nova Compra: campo de valor unitário com cálculo bidirecional

**Status:** Planejado
**Origem:** Operador calcula manualmente o total (qtd × unitário).

### Solução

Três campos por linha: Qtd, Custo Unitário, Custo Total — com cálculo automático bidirecional em tempo real.

```
│ Insumo        Qtd    Custo Unit.    Custo Total  │
│ [Coca Lata]  [240]  [R$ 2,00]  →  [R$ 480,00]  │
```

**Lógica de cálculo (último campo editado tem prioridade):**
- Editou Qtd ou Custo Unitário → recalcula Custo Total
- Editou Custo Total → recalcula Custo Unitário (mantém Qtd)

### Impacto técnico

- Apenas frontend — lógica reativa nos campos. Backend já recebe `custo_unitario`.

### Critérios de aceite

- Quaisquer dois campos preenchidos calculam o terceiro automaticamente.
- Último campo editado define o recálculo (Total editado → recalcula Unitário).
- Cálculo em tempo real (onChange).

---

## M018 — Verificação: custo médio ponderado já implementado corretamente

**Status:** Verificado — sem mudança necessária

### Resultado

`compras_service.py` implementa média ponderada correta:

```python
numerador = estoque_atual * custo_medio_atual + quantidade_nova * custo_unitario_novo
denominador = estoque_atual + quantidade_nova
custo_medio = numerador / denominador
```

Exemplo: 10 un a R$50 → venda de 5 → compra de 5 un a R$100 → custo_medio = R$75,00 ✓

Reset quando `estoque_atual <= 0`: custo médio redefinido para o custo da nova compra. Correto.

Após M000, essa lógica migra para `insumos` — sem mudança na fórmula.
