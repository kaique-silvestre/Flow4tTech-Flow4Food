# PRD — Melhorias Pós-MVP: Sistema Matchpoint

> Documento unificado com todas as fases de melhoria planejadas após entrega do MVP (12/05/2026).
> Cada fase agrupa features relacionadas. Fases devem ser implementadas na ordem listada respeitando dependências.

---

## Sequência de Implementação

```
Fase 1 (UX triviais — independente):  M003 ✓, M004 ✓, M015 ✓
Fase 2 (Base arquitetural):           M000 ✓
Fase 3 (Dependem de M000):            M001 ✓, M002 ✓
Fase 4 (Comanda UX):                  M005 ✓, M006 ✓, M007 ✓
Fase 5 (Navbar):                      M008 ✓, M009, M011 ✓
Fase 6 (Dashboard/Relatórios):        M010, M013, M014, M016
Fase 7 (Dados avançados):             M012, M017
```

---

# Fase 1 — UX Triviais (M003, M004, M015)

## Problem Statement

Três falhas de usabilidade independentes afetam operadores diariamente:

1. Na tela de comanda aberta (`/comandas/:id`) não existe forma de voltar para a listagem sem acionar o fechamento — o operador fica preso.
2. Quantidades inteiras de itens lançados aparecem com casas decimais desnecessárias (ex: "3.000" em vez de "3"), poluindo a leitura.
3. O menu lateral destaca múltiplas abas simultaneamente ao navegar para certas rotas (ex: acessar "Histórico" também destaca "Estoque"), confundindo o operador sobre onde está.

## Solution

1. **M003** — Adicionar botão "← Voltar" no cabeçalho de `ComandaAbertaPage`, navegando para `/comandas` sem alterar o estado da comanda.
2. **M004** — Adicionar helper de formatação de quantidade em `lib/format.ts`: inteiros exibem sem decimais; fracionários exibem com precisão adequada.
3. **M015** — Garantir prop `end` em cada `NavLink` do `Sidebar.tsx` para correspondência exata de rota, eliminando destaque múltiplo.

## User Stories

1. Como operador de caixa, quero um botão "← Voltar" na tela de comanda aberta, para retornar à lista de comandas sem fechar ou alterar a comanda.
2. Como operador, quero que o botão de voltar não apareça na tela de fechamento (`FechamentoPage`), para não confundir os fluxos.
3. Como operador, quero que a comanda permaneça com status `aberta` após eu clicar em voltar, para não perder os itens lançados.
4. Como operador, quero ver a quantidade "3" em vez de "3.000" na listagem de itens da comanda, para leitura mais rápida em horário de pico.
5. Como operador, quero que quantidades fracionárias (ex: 0.250) continuem sendo exibidas com precisão, para não perder informação de peso.
6. Como operador, quero que apenas a aba correspondente à rota atual fique destacada no menu lateral, para saber sempre onde estou no sistema.
7. Como operador, quero que ao navegar para "Histórico" apenas a aba "Histórico" fique destacada (não "Estoque" ou qualquer outra), para navegação sem confusão.

## Implementation Decisions

### M003 — Botão Voltar

- Modificar `ComandaAbertaPage.tsx`: adicionar botão/link "← Voltar" no cabeçalho usando `navigate('/comandas')` do React Router.
- O botão NÃO deve aparecer em `FechamentoPage.tsx`.
- Nenhuma chamada de API — puramente navegação frontend.
- Nenhuma mudança no estado da comanda (não chama endpoint de fechamento/cancelamento).

### M004 — Formatação de Quantidade

- Criar função `formatQuantidade(value: number): string` em `lib/format.ts`.
- Lógica: `value % 1 === 0` → retorna `String(value)` (sem decimais); caso contrário → retorna com casas decimais adequadas (máximo 3).
- Aplicar onde quantidades de `ItemComanda` são exibidas em `ComandaAbertaPage.tsx`.
- Zero impacto no backend — dado não muda, apenas renderização.

### M015 — NavLink Ativo Correto

- Modificar `Sidebar.tsx`: adicionar prop `end` em cada `<NavLink>` da lista `NAV_ITEMS`.
- A prop `end` força correspondência exata da rota, evitando que rota pai destaque ao acessar sub-rota.
- Nenhuma mudança de lógica de negócio — só configuração de roteamento.

## Testing Decisions

Bom teste verifica comportamento externo visível pelo usuário, não implementação interna.

- **M003:** Navegar para `/comandas/:id` → clicar "← Voltar" → verificar que URL muda para `/comandas` e que a comanda ainda está `aberta` via GET.
- **M004:** Renderizar componente de item com `quantidade=3` → verificar texto "3"; com `quantidade=0.25` → verificar "0.250" ou similar sem arredondamento.
- **M015:** Navegar para sub-rota → verificar que apenas um `NavLink` tem classe de estado ativo.

Prior art: testes de formatação seguem padrão de `lib/format.ts` — testar função pura com entrada/saída esperada.

## Out of Scope

- Edição inline de garçom/identificação na comanda (M005).
- Qualquer mudança no backend.
- Reordenação ou redesign do menu lateral além da correção de estado ativo.

## Further Notes

As três melhorias são completamente independentes entre si e de qualquer outra fase. Podem ser implementadas e entregues em qualquer ordem dentro da Fase 1.

---

# Fase 2 — Reforma Arquitetural: Insumo e Produto (M000)

## Problem Statement

O sistema atual usa uma entidade única `Item` com flag `vendavel` para representar tanto insumos (ingredientes comprados) quanto produtos (itens vendidos nas comandas). Essa modelagem gera contradições semânticas: um mesmo modelo tenta ser "pão de hambúrguer comprado por quilo" e "X-Burguer vendido a R$28". O resultado é:

- Relatórios de CMV confusos — custo de venda calculado de forma indireta.
- Estoque mistura insumos físicos com produtos compostos.
- Ficha técnica (`FichaTecnica` + `ComponenteFicha`) acoplada ao mesmo modelo `Item`, tornando difícil distinguir o que é insumo e o que é produto.
- Sem suporte claro para produtos sem ficha técnica (serviços, couverts) que vendem sem baixar estoque.

## Solution

Separar `Item` em dois modelos distintos:

- **Insumo** — representa estoque físico (pão, carne, Coca-Cola lata). Entra via Compras. Aparece no Estoque.
- **Produto** — representa o que é vendido nas Comandas (X-Burguer, Coca-Cola, Balde 6 LongNeck). Aparece no Cardápio.
- **FichaTecnica** — tabela de relação `Produto → [Insumo + quantidade]`. Define quais insumos descontar ao fechar comanda. Opcional por produto.

Migração via Alembic (hard cutover, granular, sem dual-write).

## User Stories

1. Como operador de compras, quero selecionar apenas insumos ao registrar uma compra, para não misturar produtos vendáveis com itens de estoque.
2. Como operador de estoque, quero ver apenas insumos na tela de Estoque, para ter visão clara do que existe fisicamente no estabelecimento.
3. Como gerente, quero cadastrar produtos no Cardápio com uma ficha técnica opcional, para que o sistema saiba quais insumos descontar ao fechar uma comanda.
4. Como operador de caixa, quero lançar produtos (não insumos) nas comandas, para que o fluxo de venda reflita o que o cliente consumiu.
5. Como gerente, quero que ao fechar uma comanda com X-Burguer, o sistema desconte automaticamente pão + carne + queijo do estoque, para manter o saldo de insumos correto.
6. Como gerente, quero que produtos sem ficha técnica (ex: couvert, serviço) fechem normalmente sem baixar estoque, para suportar itens não rastreados por insumo.
7. Como gerente, quero ver o CMV de cada produto calculado a partir do custo médio dos seus insumos, para ter margem real por produto.
8. Como desenvolvedor, quero que a migração preserve todo o histórico de comandas e compras, para que relatórios anteriores ao MVP continuem funcionando.
9. Como desenvolvedor, quero migrations Alembic granulares (uma por passo), para poder reverter passo a passo em caso de erro durante a migração.
10. Como gerente, quero que insumos nunca apareçam nas comandas diretamente, para evitar lançamento acidental de ingredientes brutos.

## Implementation Decisions

### Novas tabelas

**`insumos`**
| Campo | Tipo | Notas |
|-------|------|-------|
| `id` | UUID/int PK | |
| `nome` | string | |
| `categoria_id` | FK → categorias | |
| `unidade_base` | enum `un`/`g` | |
| `quantidade_caixa` | int nullable | Para itens em caixa |
| `custo_medio` | decimal | Média ponderada, calculada nas compras |
| `estoque_atual` | decimal | Saldo atualizado por movimentos |
| `ativo` | bool | Soft delete |

**`produtos`**
| Campo | Tipo | Notas |
|-------|------|-------|
| `id` | UUID/int PK | |
| `nome` | string | |
| `categoria_id` | FK → categorias | |
| `preco_venda` | decimal | |
| `ativo` | bool | Soft delete — nunca hard delete se tiver histórico em comanda |

**`ficha_tecnica`** (substitui `fichas_tecnicas` + `componentes_ficha`)
| Campo | Tipo | Notas |
|-------|------|-------|
| `produto_id` | FK → produtos | |
| `insumo_id` | FK → insumos | |
| `quantidade` | decimal | Quantidade do insumo por unidade do produto |

Unidade NÃO existe na ficha técnica — herdada de `insumo.unidade_base`.

### Sequência de migrations Alembic

1. Criar tabela `insumos`.
2. Criar tabela `produtos`.
3. Criar tabela `ficha_tecnica`.
4. Migrar dados de `itens`: `vendavel=false` → `insumos`; `vendavel=true` → `produtos`.
5. Migrar `componentes_ficha` → `ficha_tecnica` (mapear `item_composto_id` → `produto_id`, `insumo_id` permanece).
6. Atualizar FK em `compras`/`itens_compra`: `item_id` → `insumo_id`.
7. Atualizar FK em `itens_comanda`: `item_id` → `produto_id`.
8. Atualizar FK em `movimentos_estoque`: `item_id` → `insumo_id`.
9. Deprecar tabelas `itens`, `fichas_tecnicas`, `componentes_ficha` (DROP após validação).

### Mudanças nos serviços

- `compras_service`: registrar entrada em `insumos` (não `itens`). Custo médio ponderado já implementado corretamente — apenas migrar FK.
- `estoque_service`: operar sobre `insumos` em vez de `itens`.
- `comanda_service.fechar_comanda`: ao fechar, iterar `itens_comanda` → para cada produto, buscar `ficha_tecnica` → descontar `insumos`. Se produto sem ficha: fechar sem baixa.
- `relatorio_service`: atualizar queries para apontar para `produtos` e `insumos`.
- `itens_service`: deprecar (ou transformar em fachada sobre `insumos_service` + `produtos_service`).

### API

- `GET /api/insumos` — lista insumos ativos (usado por Compras, Estoque, Ficha Técnica).
- `GET /api/produtos` — lista produtos ativos (usado por Comandas, Cardápio).
- `POST/PUT/DELETE /api/insumos` — CRUD de insumos.
- `POST/PUT/DELETE /api/produtos` — CRUD de produtos (inclui `ficha_tecnica` embutida no payload).
- Endpoints antigos `GET /api/itens` retornam 404 ou são redirecionados internamente durante período de transição.

### Frontend

- Compras (`NovaCompraPage`): seletor busca `GET /api/insumos`, não `GET /api/itens`.
- Estoque (`EstoquePage`): lista de `insumos`, não `itens`.
- Comandas (`ComandaAbertaPage`): seletor busca `GET /api/produtos`.
- Cadastros: remover seção "Itens" — substituída por Cardápio (M001) e Compras/Estoque para insumos.
- `Sidebar.tsx`: remover link para Itens do menu Cadastros.

## Testing Decisions

Bom teste: verifica contrato externo (API response, state após operação), não implementação interna.

- **`comanda_service.fechar_comanda`**: fechar comanda com produto que tem ficha técnica → verificar que `estoque_atual` de cada insumo diminuiu corretamente. Fechar com produto sem ficha → verificar que nenhum insumo é alterado.
- **`compras_service`**: registrar compra com insumo → verificar `custo_medio` de `insumo` atualizado via média ponderada.
- **Migrations**: executar sequência completa em DB com dados de fixture → verificar que dados de `itens` aparecem corretamente em `insumos` e `produtos` após migração.

Prior art: services testados via integração com DB (não mocks). Ver `compras_service.py` para referência de cálculo de custo médio.

## Out of Scope

- Tela de Cardápio com UI (M001) — Fase 3.
- Modal de cadastro rápido de insumo em Nova Compra (M002) — Fase 3.
- Subcategorias (M012) — Fase 7.
- Qualquer feature de UI além da remoção de "Itens" do menu.

## Further Notes

Esta fase é bloqueante para M001, M002, M009 e qualquer feature que distinga insumos de produtos. Deve ser concluída antes de iniciar a Fase 3.

O custo médio ponderado já está implementado corretamente em `compras_service.py` — a fórmula migra para `insumos` sem alteração.

Hard cutover (sem dual-write) é a estratégia correta: dados de ambiente single-tenant, sem usuários simultâneos que dependam das tabelas antigas durante a migração.

---

# Fase 3 — Cardápio e Cadastro Rápido de Insumo (M001, M002)

## Problem Statement

Após a reforma arquitetural da Fase 2, dois fluxos ficam sem UI adequada:

1. **M001** — Não existe tela para gerenciar Produtos (cadastrar, editar, desativar, ver CMV). O Cardápio precisa de uma seção própria no sistema.
2. **M002** — Ao registrar uma compra com um insumo novo, o operador precisa abandonar o formulário de Nova Compra, ir até outro lugar para cadastrar o insumo e depois voltar. Não há atalho inline.

## Solution

1. **M001** — Nova seção "Cardápio" no menu lateral com CRUD completo de Produtos e suas fichas técnicas. Listagem com CMV calculado em tempo real.
2. **M002** — Link "[ + Cadastrar novo insumo ]" abaixo do seletor de insumos em Nova Compra. Abre modal mínimo. Ao salvar, insumo aparece pré-selecionado na linha sem perder os dados já preenchidos.

## User Stories

### M001 — Cardápio

1. Como gerente, quero uma seção "Cardápio" no menu lateral, para gerenciar produtos vendáveis separadamente dos insumos.
2. Como gerente, quero ver uma listagem de produtos com nome, categoria, preço de venda, custo da ficha técnica, CMV% e lucro bruto, para avaliar a rentabilidade de cada item.
3. Como gerente, quero que o CMV seja colorido (verde < 30%, amarelo 30–50%, vermelho > 50%), para identificar rapidamente produtos com margem problemática.
4. Como gerente, quero criar um novo produto informando nome, categoria e preço de venda, para adicionar itens ao cardápio.
5. Como gerente, quero montar a ficha técnica de um produto selecionando insumos e quantidades, para que o sistema saiba o que descontar do estoque ao vender.
6. Como gerente, quero ver a unidade do insumo exibida ao lado da quantidade na ficha técnica (ex: "200 g"), para não precisar memorizar as unidades.
7. Como gerente, quero que o custo total da ficha técnica e o CMV sejam calculados em tempo real conforme monto a ficha, para tomar decisões de precificação sem sair do formulário.
8. Como gerente, quero criar produtos sem ficha técnica (ex: couvert artístico), para suportar itens não rastreados por insumo.
9. Como gerente, quero editar um produto existente (nome, categoria, preço, ficha técnica), para corrigir erros ou atualizar o cardápio.
10. Como gerente, quero desativar um produto sem excluí-lo, para preservar histórico de comandas que o utilizaram.
11. Como gerente, quero que produtos inativos não apareçam no seletor de itens de comandas, para evitar lançamento acidental.
12. Como gerente, quero que produtos sem ficha técnica ou com insumos sem custo médio exibam "—" no CMV, para não mostrar valores enganosos.

### M002 — Cadastro Rápido de Insumo

13. Como operador de compras, quero ver um link "[ + Cadastrar novo insumo ]" abaixo do seletor de insumos em Nova Compra, para saber que posso cadastrar um insumo sem sair do formulário.
14. Como operador de compras, quero que ao clicar no link um modal abra com campos mínimos (nome, categoria, unidade), para cadastrar o insumo rapidamente.
15. Como operador de compras, quero que ao salvar o insumo no modal, ele apareça automaticamente pré-selecionado na linha da compra, para continuar o preenchimento sem interrupção.
16. Como operador de compras, quero que todos os dados já preenchidos no formulário de Nova Compra sejam preservados quando o modal abre e fecha, para não perder o trabalho feito.
17. Como operador de compras, quero que após salvar o insumo, ele apareça disponível para seleção em futuras compras, para não precisar cadastrá-lo novamente.

## Implementation Decisions

### M001 — Cardápio

**Frontend:**
- Nova rota `/cardapio` com `CardapioPage.tsx` — listagem de produtos.
- `ProdutoModal.tsx` — formulário de criação/edição com ficha técnica dinâmica.
- Adicionar "Cardápio" ao `NAV_ITEMS` de `Sidebar.tsx` (entre Comandas e Estoque).
- Ficha técnica: lista de linhas com seletor de insumo + campo de quantidade. Botão "[ + Adicionar insumo ]". Botão "✕" para remover linha.
- Unidade exibida inline: buscar `insumo.unidade_base` do insumo selecionado e renderizar ao lado do campo de quantidade.
- Custo e CMV calculados no frontend a partir de `insumo.custo_medio * quantidade` para cada linha.
- Coluna CMV colorida via classe condicional (green/yellow/red).

**Backend:**
- `GET /api/produtos` — lista com `custo_ficha` e `cmv` calculados no response (ou calculados no frontend a partir de insumos).
- `POST /api/produtos` — cria produto + ficha técnica em transação única.
- `PUT /api/produtos/:id` — atualiza produto + substitui ficha técnica (delete all + insert).
- `DELETE /api/produtos/:id` — soft delete (`ativo=false`), bloqueado se tiver `itens_comanda` referenciando.

### M002 — Cadastro Rápido de Insumo

**Frontend:**
- Modificar `NovaCompraPage.tsx`: adicionar link "[ + Cadastrar novo insumo ]" abaixo do `Select` de insumo em cada linha de item da compra.
- `InsumoModal.tsx` — campos: nome (required), categoria_id (required), unidade_base (required). Campos opcionais: quantidade_caixa.
- Ao fechar modal com sucesso: chamar `invalidateQueries(['insumos'])` e pré-selecionar o ID do insumo criado na linha que disparou o modal.
- Estado do formulário de compra (fornecedor, data, nota, outras linhas) não é afetado pela abertura/fechamento do modal.

**Backend:**
- `POST /api/insumos` — já existe via M000.

## Testing Decisions

Bom teste: verifica comportamento visível ao usuário — dados salvos, seleção pré-preenchida, custo calculado corretamente.

- **`CardapioPage` + `ProdutoModal`**: criar produto com ficha técnica → verificar que produto aparece na listagem com CMV correto. Criar produto sem ficha → verificar "—" no CMV.
- **CMV calculation**: função pura que calcula custo e CMV a partir de lista de `{insumo, quantidade}` — testar com valores conhecidos.
- **`NovaCompraPage` + `InsumoModal`**: abrir modal → criar insumo → verificar que insumo aparece pré-selecionado na linha e dados da compra preservados.

Prior art: `ItemModal.tsx` em `features/cadastros/itens/` — referência para formulário de produto com ficha técnica.

## Out of Scope

- Subcategorias de insumos/produtos (M012).
- Edição de preço em massa.
- Importação de cardápio via planilha.
- Histórico de alterações de preço.
- Imagens de produtos.

## Further Notes

M001 e M002 dependem de M000 estar completo. São independentes entre si — podem ser implementados em paralelo após M000.

O seletor de insumos em `NovaCompraPage` e em `ProdutoModal` compartilham a mesma query `GET /api/insumos` — considerar hook compartilhado `useInsumos`.

---

# Fase 4 — Comanda UX (M005, M006, M007)

## Problem Statement

Três fricções no fluxo de comanda degradam a experiência do operador:

1. **M005** — Erros de digitação no garçom ou na identificação da comanda (nome/mesa) não têm correção: o operador é forçado a fechar e reabrir a comanda.
2. **M006** — A tela de fechamento abre sem nenhuma opção pré-selecionada e sem o valor preenchido, obrigando o operador a selecionar "Sem divisão" e digitar o total manualmente — mesmo sendo o caso mais comum.
3. **M007** — Na opção "Dividir entre N pessoas", o operador precisa calcular manualmente o valor por pessoa, sujeito a erros de cálculo em horário de pico.

## Solution

1. **M005** — Adicionar botão `[✏]` ao lado do garçom e da identificação no cabeçalho de `ComandaAbertaPage`. Edição inline, sem modal de confirmação. Salva via `PATCH /api/comandas/:id`.
2. **M006** — Ao carregar `FechamentoPage`, pré-selecionar "Sem divisão" e preencher o campo de valor com o total da comanda automaticamente.
3. **M007** — No modo "Dividir entre N pessoas", calcular e exibir valor por pessoa em tempo real conforme o operador digita N. Garantir que a soma não perca centavos.

## User Stories

### M005 — Edição de Garçom e Identificação

1. Como operador, quero ver um botão `[✏]` ao lado do nome/identificação da comanda no cabeçalho, para corrigir erros de cadastro sem fechar a comanda.
2. Como operador, quero ver um botão `[✏]` ao lado do nome do garçom no cabeçalho, para trocar o garçom sem fechar a comanda.
3. Como operador, quero que ao clicar em `[✏]` o campo vire editável inline (sem abrir modal), para editar rapidamente.
4. Como operador, quero confirmar a edição com Enter ou clicando fora do campo, para fluxo rápido sem clique extra.
5. Como operador, quero que a edição só esteja disponível em comandas com status `aberta`, para não alterar comandas já fechadas.
6. Como gerente, quero que a troca de garçom reflita nos relatórios de vendas por garçom, para manter dados consistentes.
7. Como operador, quero que a edição não exija confirmação via modal, para não interromper o ritmo de atendimento.

### M006 — Fechamento Pré-preenchido

8. Como operador, quero que a tela de fechamento abra com "Sem divisão" já selecionado, para não precisar escolher a opção mais comum manualmente.
9. Como operador, quero que o campo de valor já venha preenchido com o total da comanda ao abrir a tela de fechamento, para não precisar digitar o valor.
10. Como operador, quero que ao trocar o modo de divisão (ex: para "Dividir igualmente") o campo de valor seja resetado adequadamente, para não gerar confusão com o valor pré-preenchido.

### M007 — Divisão Automática por Pessoa

11. Como operador, quero que ao selecionar "Dividir entre N pessoas" e digitar o número de pessoas, o valor por pessoa seja calculado automaticamente, para não fazer cálculo mental em horário de pico.
12. Como operador, quero ver o valor por pessoa atualizado em tempo real (onChange), para ajustar N e ver o resultado imediatamente.
13. Como operador, quero que a soma dos valores por pessoa bata com o total da comanda sem perda de centavos, para não criar divergência no fechamento.

## Implementation Decisions

### M005 — Edição Inline

**Frontend:**
- `ComandaAbertaPage.tsx`: substituir texto estático de identificação e garçom por componentes de edição inline (input oculto que aparece ao clicar em `[✏]`).
- Estado local: `editingField: 'identificacao' | 'garcom' | null`.
- `onBlur` e `onKeyDown Enter` → disparar mutação.
- Apenas para `status === 'aberta'` — botão `[✏]` não renderizado para outros status.

**Backend:**
- `PATCH /api/comandas/:id` — aceitar `identificacao` (string) e `garcom_id` (int) individualmente, apenas para comanda com `status='aberta'`.
- Registrar `EventoComanda` do tipo `COMANDA_EDITADA` com payload das mudanças.
- `relatorio_service`: queries de vendas por garçom já usam `garcom_id` da comanda — a troca reflete automaticamente.

### M006 — Estado Inicial do Fechamento

**Frontend:**
- `FechamentoPage.tsx` (ou `useFechamento.ts`): inicializar estado do formulário com `modo_divisao: 'sem_divisao'` e `valor: comanda.total` ao montar o componente.
- Quando `modo_divisao` mudar: resetar `valor` para `comanda.total` se `sem_divisao`, ou limpar para input manual nos outros modos.
- Zero mudança no backend.

### M007 — Cálculo de Divisão

**Frontend:**
- `FechamentoPage.tsx`: no modo "Dividir entre N pessoas", adicionar campo `n_pessoas` e exibir campo calculado `valor_por_pessoa = total / n_pessoas`.
- Cálculo em `onChange` de `n_pessoas`.
- Tratar divisão por zero (N=0 ou vazio → não exibir).
- Distribuição de centavos: `valor_por_pessoa = Math.floor(total * 100 / n) / 100` para N-1 pessoas; última pessoa recebe o restante (`total - valor_por_pessoa * (n-1)`).
- Zero mudança no backend.

## Testing Decisions

- **`PATCH /api/comandas/:id`**: atualizar `identificacao` e `garcom_id` de comanda aberta → verificar persistência. Tentar editar comanda fechada → verificar 422/400.
- **Cálculo de divisão** (função pura): `dividirTotal(total, n)` → verificar que soma das partes == total (sem perda de centavos). Testar com valores não divisíveis (ex: R$10,00 / 3 pessoas).
- **Estado inicial de fechamento**: renderizar `FechamentoPage` com `total=100` → verificar que campo de valor inicia com "100" e modo "sem divisão" marcado.

Prior art: mutações de comanda: `useComandas.ts` — padrão `useMutation` + `invalidateQueries`.

## Out of Scope

- Divisão desigual (cada pessoa paga valor diferente).
- Múltiplos métodos de pagamento por pessoa no modo dividido.
- Histórico de edições de garçom/identificação visível na UI.
- Edição de itens já lançados (quantidade, preço) — fluxo existente de `editar_item`.

## Further Notes

M005, M006 e M007 são independentes entre si. M005 requer mudança de backend; M006 e M007 são puramente frontend.

A edição inline de M005 deve usar debounce ou aguardar `onBlur`/Enter para não disparar PATCH a cada keystroke.

---

# Fase 5 — Navbar (M008, M009, M011)

## Problem Statement

O menu lateral tem três problemas de usabilidade:

1. **M008** — Menu colapsado remove completamente os ícones, eliminando referência visual para o operador. Sem ícones, o menu colapsado é inútil.
2. **M009** — A seção "Cadastros" leva o operador a uma única página com abas, em vez de permitir navegação direta para cada subseção (Categorias, Fornecedores, Garçons, Pagamentos). O submenu via dropdown melhora a navegação.
3. **M011** — Não há botão padronizado para colapsar/expandir o menu. O mecanismo atual é inconsistente.

## Solution

1. **M008** — Menu colapsado mantém ícones visíveis; expandido mostra ícone + texto. Tooltip ao hover no estado colapsado. Estado padrão: expandido. Estado persiste em `localStorage`.
2. **M009** — "Cadastros" vira dropdown/submenu com links diretos: Categorias, Fornecedores, Garçons, Pagamentos. "Itens" removido (não existe mais após M000).
3. **M011** — Ícone `☰` fixo no topo do `Sidebar`, alternando colapsado/expandido. Compartilha key `localStorage` com M008.

## User Stories

1. Como operador, quero ver os ícones do menu mesmo quando está colapsado, para ter referência visual de onde clicar sem precisar expandir.
2. Como operador, quero ver um tooltip com o nome da seção ao passar o mouse sobre um ícone no menu colapsado, para confirmar o destino antes de clicar.
3. Como operador, quero que o menu inicie expandido por padrão, para ter acesso imediato aos nomes das seções.
4. Como operador, quero que minha preferência de colapso/expansão do menu seja lembrada entre sessões, para não precisar reconfigurar a cada login.
5. Como operador, quero um ícone `☰` fixo no topo do menu para alternar entre colapsado e expandido, para ter controle claro e padronizado do menu.
6. Como operador, quero que ao clicar em "Cadastros" no menu, um submenu se expanda mostrando: Categorias, Fornecedores, Garçons, Pagamentos, para navegar diretamente para a subseção desejada.
7. Como operador, quero que a subseção ativa de Cadastros seja destacada visualmente, para saber exatamente onde estou dentro do menu.
8. Como operador, quero que ao passar o mouse sobre o ícone de Cadastros no menu colapsado, um submenu flutuante apareça com as opções, para acessar subseções sem precisar expandir o menu.
9. Como operador, quero que "Itens" não apareça mais no submenu de Cadastros, para não ver uma seção inexistente após a reforma arquitetural.

## Implementation Decisions

### Estado de Colapso (M008 + M011)

- `localStorage` key: `sidebar_collapsed` (boolean).
- Leitura no mount do componente `Sidebar.tsx`; escrita a cada toggle.
- Valor padrão: `false` (expandido).
- Estado gerenciado em `Sidebar.tsx` com `useState` inicializado a partir de `localStorage`.

### Ícones no Estado Colapsado (M008)

- `Sidebar.tsx`: quando `collapsed=true`, renderizar apenas o ícone de cada item (sem texto).
- Adicionar `<Tooltip>` (shadcn/ui) ao redor de cada ícone no estado colapsado, com `content={item.label}`.
- Quando `collapsed=false`: renderizar ícone + texto lado a lado.
- Largura do sidebar: `collapsed ? 'w-16' : 'w-56'` (ou similar via Tailwind).

### Botão de Toggle (M011)

- Ícone `☰` (ou equivalente shadcn/ui `Menu`) no topo de `Sidebar.tsx`, sempre visível.
- `onClick={() => setCollapsed(!collapsed)}` + persist em `localStorage`.

### Submenu de Cadastros (M009)

- `NAV_ITEMS` em `Sidebar.tsx`: transformar item "Cadastros" em grupo com filhos:
  ```
  { label: 'Cadastros', icon: ClipboardList, children: [
    { label: 'Categorias', href: '/cadastros/categorias' },
    { label: 'Fornecedores', href: '/cadastros/fornecedores' },
    { label: 'Garçons', href: '/cadastros/garcons' },
    { label: 'Pagamentos', href: '/cadastros/metodos-pagamento' },
  ]}
  ```
- "Itens" (`/cadastros/itens`) removido da lista.
- Estado local: `cadastrosOpen: bool` para controlar expansão do dropdown no sidebar expandido.
- Menu colapsado: `onMouseEnter` no ícone de Cadastros abre submenu flutuante posicionado com CSS (absolute/fixed).
- Rotas existentes não mudam.
- Remover rota `/cadastros/itens` do `App.tsx` após M000 estar completo.

## Testing Decisions

- **Persistência**: montar `Sidebar` com `localStorage` vazio → estado expandido. Clicar `☰` → collapsed. Remontar → estado collapsed preservado.
- **Submenu**: clicar em "Cadastros" → verificar que links de subseções aparecem. Clicar em "Categorias" → verificar navegação para `/cadastros/categorias`.
- **Destaque ativo**: navegar para `/cadastros/fornecedores` → verificar que link "Fornecedores" tem classe ativa (e somente ele).

Prior art: `Sidebar.tsx` existente — padrão de `NavLink` com classe ativa. M015 (Fase 1) corrige o `end` prop que é base para o destaque correto.

## Out of Scope

- Reordenar itens do menu.
- Atalhos de teclado para navegação.
- Menu responsivo/mobile (sidebar tipo drawer).
- Qualquer mudança nas páginas de destino.

## Further Notes

M008 e M011 são fortemente acoplados (mesma key `localStorage`) — implementar juntos no mesmo PR.

M009 depende de M000 estar concluído para remover "Itens" com segurança. M008 e M011 são independentes de M000.

M015 (Fase 1) deve estar concluído antes de M009 para que o destaque de subitem funcione corretamente.

---

# Fase 6 — Dashboard e Relatórios (M010, M013, M014, M016)

## Problem Statement

Quatro problemas afetam a visibilidade operacional e financeira do sistema:

1. **M010** — A rota `/relatorios` exibe um placeholder vazio. Os sub-relatórios existem mas são inacessíveis pela interface — não há página índice que os liste.
2. **M013** — A tela de Comandas só exibe lista. Em dias de pico, cards visuais facilitam leitura rápida do nome/mesa sem percorrer linhas de tabela.
3. **M014** — O histórico dentro de Comandas mistura o dia atual com comandas antigas. Operadores precisam de separação clara: "o que fechei hoje" vs. "histórico geral com filtros".
4. **M016** — O Dashboard exibe dados que não refletem necessidades de acompanhamento financeiro real: "Lucro estimado" é impreciso sem CMV completo, e o calendário atual (heatmap de dias do mês) tem pouco valor gerencial. Faltam visão histórica entrada/saída e calendário anual por mês.

## Solution

1. **M010** — Página índice em `/relatorios` com cards navegáveis para cada sub-relatório disponível.
2. **M013** — Toggle `[≡ Lista] / [⊞ Cards]` na tela de Comandas. Cards exibem 3 por linha (telas largas) ou 2 (menores). Preferência salva em `localStorage`.
3. **M014** — Separar histórico: dentro de Comandas → "Histórico do dia" (só `fechada` com `data_fechamento` hoje). Nova aba no menu `📜 Histórico` → `/historico` → todas as fechadas com filtros de período.
4. **M016** — Remover "Lucro estimado" e calendário de dias. Adicionar: tab "Histórico" com entrada/saída por dia (filtro de período) + calendário anual (12 meses com faturamento e gasto por mês).

## User Stories

### M010 — Índice de Relatórios

1. Como gerente, quero acessar `/relatorios` e ver um índice com todos os relatórios disponíveis, para não precisar lembrar as rotas ou navegar por tentativa e erro.
2. Como gerente, quero que cada relatório seja representado por um card com nome e breve descrição, para entender o que cada um mostra antes de abrir.
3. Como gerente, quero clicar no card e ser levado diretamente para o relatório, para navegação em um clique.

### M013 — Lista vs. Cards em Comandas

4. Como operador, quero alternar a visualização da lista de comandas entre tabela e cards, para escolher o formato mais adequado ao ritmo de trabalho.
5. Como operador, quero que os cards exibam claramente nome/mesa, garçom, horário de abertura e valor total acumulado, para leitura rápida sem abrir a comanda.
6. Como operador, quero que minha preferência de visualização (lista ou cards) seja salva, para não precisar reconfigurar a cada acesso.
7. Como operador, quero que clicar em um card abra a comanda normalmente, para manter o fluxo de trabalho independente do modo de visualização.

### M014 — Separação de Histórico

8. Como operador, quero ver em Comandas apenas as comandas fechadas no dia atual na seção "Histórico do dia", para encontrar rapidamente o que fechei hoje.
9. Como gerente, quero uma aba "Histórico" no menu lateral com todas as comandas fechadas (qualquer data), para consultar histórico geral.
10. Como gerente, quero filtrar o histórico geral por período (data inicial e final), para analisar períodos específicos.
11. Como gerente, quero que "Histórico do dia" e "Histórico geral" não se sobreponham, para não ver duplicidade de dados.

### M016 — Dashboard Revisado

12. Como gerente, quero que o card "Lucro estimado" seja removido do Dashboard, para não ver dado impreciso.
13. Como gerente, quero ver no Dashboard uma tab "Histórico" com entrada (faturamento) e saída (compras) por dia, para acompanhar fluxo financeiro diário.
14. Como gerente, quero filtrar o histórico do Dashboard por período, para comparar semanas ou meses específicos.
15. Como gerente, quero ver um calendário anual com os 12 meses do ano corrente, mostrando faturamento e gasto por mês, para visão estratégica do ano.
16. Como gerente, quero que meses sem dados apareçam com "—" no calendário anual, para distinguir meses sem movimento de meses com R$0 real.
17. Como gerente, quero que o faturamento e gasto do mês atual no calendário sejam atualizados em tempo real conforme o dia avança, para não ver dados desatualizados.

## Implementation Decisions

### M010 — Índice de Relatórios

**Frontend:**
- Substituir `PlaceholderPage` em `/relatorios` por `RelatoriosIndexPage.tsx`.
- Grid de cards (shadcn/ui `Card`) — um por sub-relatório: Vendas do Dia, Histórico de Comandas, Fechamento de Caixa, DRE, CMV por Produto, Perdas e Cortesias, Vendas por Garçom.
- Cada card: título + descrição de 1 linha + `navigate('/relatorios/...')` no onClick.
- Sem mudança no backend.

### M013 — Lista vs. Cards

**Frontend:**
- `ComandasPage.tsx`: adicionar state `viewMode: 'list' | 'cards'`, inicializado de `localStorage` key `comandas_view_mode`.
- Toggle: dois botões de ícone (`≡` e `⊞`) no canto superior direito da seção.
- `CardsView`: CSS grid `grid-cols-3 lg:grid-cols-3 md:grid-cols-2`. Cada card: `Card` shadcn com nome/mesa (grande), garçom, tempo aberto, total acumulado.
- Clicar em card: `navigate('/comandas/:id')`.
- Apenas visualização — zero mudança em backend ou queries.

### M014 — Separação de Histórico

**Frontend:**
- `ComandasPage.tsx`: filtro de `status=fechada AND data_fechamento >= hoje_00:00` para seção "Histórico do dia".
- Nova rota `/historico` com `HistoricoPage.tsx` — lista de todas as comandas `fechada` com filtros de data.
- `App.tsx`: adicionar rota `/historico`.
- `Sidebar.tsx`: adicionar link `📜 Histórico` → `/historico` no `NAV_ITEMS`.

**Backend:**
- `GET /api/comandas?status=fechada&data_inicio=&data_fim=` — confirmar ou adicionar suporte a filtros de data.

### M016 — Dashboard Revisado

**Frontend:**
- `DashboardPage.tsx`: remover card "Lucro estimado" e componente de heatmap mensal.
- Adicionar tabs: `[Resumo]` (cards operacionais existentes) e `[Histórico]`.
- Tab Histórico: tabela/gráfico de linhas com `data`, `faturamento_dia`, `gasto_dia` — filtro de período com date picker.
- Calendário anual: grid de 12 meses × 2 linhas (Fat. / Gasto).

**Backend:**
- Novo endpoint `GET /api/dashboard/historico?inicio=&fim=` — retorna array de `{data, faturamento, total_compras}` por dia.
- Novo endpoint `GET /api/dashboard/resumo-anual?ano=` — retorna array de `{mes, faturamento, total_compras}` (12 entradas).
- `dashboard_repository.py`: queries agregadas por dia e por mês.

## Testing Decisions

- **M010**: renderizar `RelatoriosIndexPage` → verificar que todos os cards estão presentes e navegam para rotas corretas.
- **M013**: toggle list/cards → verificar que `localStorage` é atualizado e view muda. Clicar em card → verificar navegação.
- **M014**: `GET /api/comandas` com filtro de data do dia → verificar que retorna apenas comandas fechadas hoje. `HistoricoPage` com filtro de período → verificar query correta.
- **M016**: `GET /api/dashboard/historico` → verificar estrutura do response. `GET /api/dashboard/resumo-anual` → verificar 12 entradas, uma por mês.

Prior art: `useDashboard.ts` — padrão de query para dados de dashboard.

## Out of Scope

- Exportação de relatórios para PDF/Excel.
- Gráficos avançados (candlestick, scatter).
- Comparação entre anos no calendário anual.
- Notificações ou alertas baseados em métricas do dashboard.
- Filtro por garçom no histórico geral (coberto por relatório específico).

## Further Notes

M010, M013 são independentes de M000 — podem ser implementados antes da reforma arquitetural.

M016 deve remover o card "Lucro estimado" imediatamente — não aguardar o calendário anual estar pronto para fazer esse cleanup.

---

# Fase 7 — Dados Avançados (M012, M017)

## Problem Statement

Dois gaps de dados limitam organização e eficiência operacional:

1. **M012** — O modelo de `Categoria` é plano (apenas `id` e `nome`). Não é possível agrupar categorias relacionadas (ex: "Bebidas → Cervejas", "Bebidas → Refrigerantes"), forçando nomes longos e redundantes ou categorias genéricas demais.
2. **M017** — Na tela de Nova Compra, o operador precisa calcular manualmente o custo total de cada linha (quantidade × unitário). Sem cálculo automático, erros de digitação são frequentes e o operador precisa de calculadora paralela.

## Solution

1. **M012** — Adicionar campo `parent_id` (nullable FK para `categorias.id`) na tabela `categorias`. Máximo 2 níveis (pai + filho). API retorna árvore hierárquica. UI exibe hierarquia em tree/accordion com subcategorias indentadas em seletores.
2. **M017** — Três campos por linha em Nova Compra: Quantidade, Custo Unitário, Custo Total — com cálculo bidirecional automático em tempo real. Último campo editado define o recálculo.

## User Stories

### M012 — Subcategorias

1. Como gerente, quero criar categorias pai (ex: "Bebidas") e subcategorias filhas (ex: "Cervejas", "Refrigerantes"), para organizar insumos e produtos de forma mais granular.
2. Como gerente, quero que ao criar uma categoria, possa opcionalmente selecionar uma "categoria pai", para posicioná-la na hierarquia.
3. Como gerente, quero que o sistema bloqueie a criação de subcategoria de subcategoria (máximo 2 níveis), para manter a hierarquia simples e previsível.
4. Como gerente, quero que ao tentar excluir uma categoria pai que tem subcategorias ativas, o sistema bloqueie e informe o motivo, para não deixar subcategorias órfãs.
5. Como gerente, quero ver as categorias exibidas em tree/accordion na tela de Cadastros → Categorias, para visualizar a hierarquia completa.
6. Como operador, quero ver subcategorias indentadas nos seletores de categoria (em Insumos, Produtos, etc.), para identificar rapidamente a hierarquia sem precisar decorar os nomes.
7. Como operador, quero que tanto insumos quanto produtos possam ser vinculados a subcategorias, para organização granular de ambos.

### M017 — Cálculo Bidirecional em Compras

8. Como operador de compras, quero que ao preencher Quantidade e Custo Unitário em uma linha de compra, o Custo Total seja calculado automaticamente, para não fazer multiplicação manual.
9. Como operador de compras, quero que ao preencher o Custo Total diretamente, o Custo Unitário seja calculado automaticamente mantendo a Quantidade, para registrar compras onde só conheço o valor total da nota.
10. Como operador de compras, quero que o cálculo ocorra em tempo real (ao digitar), para ver o resultado imediatamente sem submeter o formulário.
11. Como operador de compras, quero que o último campo editado defina o recálculo (editei Total → recalcula Unitário; editei Unitário → recalcula Total), para controlar qual valor é derivado.
12. Como operador de compras, quero que ao editar Quantidade, o Custo Total seja recalculado mantendo o Custo Unitário, para manter a regra de negócio consistente.

## Implementation Decisions

### M012 — Subcategorias

**Backend:**
- Migration Alembic: adicionar `parent_id INTEGER NULLABLE REFERENCES categorias(id)`.
- Validação no `categorias_service`: ao criar categoria com `parent_id`, verificar que a categoria pai não tem ela própria um `parent_id` (bloquear 3º nível).
- `GET /api/categorias`: retornar árvore hierárquica `[{id, nome, children: [{id, nome}]}]`.
- `DELETE /api/categorias/:id`: verificar se tem subcategorias ativas — retornar erro 409 se sim.
- `categorias_repository.py`: query que carrega categorias com filhos em uma só consulta (CTE ou dois queries com agrupamento em Python).

**Frontend:**
- `CategoriasPage.tsx`: exibir hierarquia em accordion (categoria pai expansível mostrando filhos).
- `CategoriaModal.tsx`: adicionar campo opcional "Categoria pai" (Select com apenas categorias raiz — sem `parent_id`).
- Seletores em `InsumoModal.tsx`, `ProdutoModal.tsx`: subcategorias indentadas com `pl-4` ou similar.
- `useCategorias.ts`: adaptar para receber estrutura hierárquica da API e achatar para seletores quando necessário.

### M017 — Cálculo Bidirecional

**Frontend:**
- `NovaCompraPage.tsx`: cada linha de item terá três campos controlados: `quantidade`, `custo_unitario`, `custo_total`.
- Hook de cálculo bidirecional por linha — state local com `lastEdited: 'unitario' | 'total'`.
- `onChange` de `custo_unitario`: se `quantidade > 0` → `custo_total = quantidade * custo_unitario`. Setar `lastEdited = 'unitario'`.
- `onChange` de `custo_total`: se `quantidade > 0` → `custo_unitario = custo_total / quantidade`. Setar `lastEdited = 'total'`.
- `onChange` de `quantidade`: usar `lastEdited` para decidir o que recalcular.
- Backend já recebe `custo_unitario` no payload — sem mudança de schema.
- Precisão: arredondar resultados a 2 casas decimais para evitar floating point noise.

## Testing Decisions

### M012

- **`categorias_service`**: criar subcategoria de subcategoria → verificar erro 422. Criar subcategoria de categoria raiz → verificar sucesso. Deletar categoria pai com filhos ativos → verificar erro 409.
- **`GET /api/categorias`**: verificar estrutura hierárquica no response (pai com `children` preenchido).
- **Frontend**: seletor de categorias → verificar que subcategorias aparecem indentadas e selecionáveis.

### M017

- **Função de cálculo bidirecional** (função pura): `calculateLine({quantidade: 10, custo_unitario: 2.5, lastEdited: 'unitario'})` → `{custo_total: 25.00}`. `calculateLine({quantidade: 10, custo_total: 25, lastEdited: 'total'})` → `{custo_unitario: 2.50}`.
- Testar divisão com resultado não inteiro: 10 / 3 → `custo_unitario` arredondado a 2 casas.

Prior art: `compraSchemas.ts` — validação Zod da linha de compra existente. `useCompras.ts` — mutação de criação de compra.

## Out of Scope

- Mais de 2 níveis de hierarquia de categorias.
- Mover categoria de um pai para outro (drag and drop).
- Cálculo automático do total geral da compra com desconto (já existe via soma das linhas).
- Importação de compras via planilha.
- Vinculação de categoria a outros objetos além de insumos e produtos.

## Further Notes

M012 depende de M000 concluído para que os seletores de insumos e produtos já existam nas telas de Cardápio e Compras.

M017 é independente de todas as outras fases — pode ser implementado antes da Fase 2 se necessário, pois `NovaCompraPage` tem a mesma estrutura de linha com `itens` ou `insumos`.

O cálculo bidirecional de M017 deve tratar `quantidade = 0` (não dividir por zero ao calcular `custo_unitario = custo_total / quantidade`).
