
# Issues — Matchpoint Melhorias de UX, Correções e Reserva de Estoque v0.4

> Gerado a partir de `docs/prds/prd_matchpoint_v0.4.md`.
> Ordem de criação respeita dependências (blockers primeiro).

---

## Issue 1 — Inverter mesa/nome na nova comanda ✅

**Tipo:** AFK
**Bloqueado por:** Nenhum — pode iniciar imediatamente
**Status:** ✅ Concluído (commit `62ffd5f`)

### O que construir

Trocar o padrão de identificação da nova comanda de "Número da mesa" para "Nome do responsável". Duas mudanças no mesmo componente: o valor padrão selecionado ao abrir o modal deve ser "nome", e a ordem de exibição dos radio buttons deve colocar "Nome do responsável" antes de "Número da mesa".

Nenhuma alteração de backend ou schema necessária.

### Critérios de aceite

- [x] Abrir modal de nova comanda → radio "Nome do responsável" já está selecionado
- [x] "Nome do responsável" aparece antes de "Número da mesa" na lista
- [x] Input de identificação abre como campo de texto (não numérico)
- [x] Trocar para "Número da mesa" continua funcionando normalmente
- [x] Criar comanda por nome → backend recebe `tipo_identificacao: "nome"`
- [x] Criar comanda por mesa → backend recebe `tipo_identificacao: "mesa"` com número inteiro

### User stories endereçadas

- US1: Como garçom, quero que o modal de nova comanda abra já com "Nome do responsável" selecionado, para não precisar trocar manualmente em cada atendimento.
- US2: Como garçom, quero que o campo "Nome do responsável" apareça primeiro na lista de opções, para encontrá-lo mais rapidamente.

---

## Issue 2 — Filtrar produtos ativos na busca da comanda ✅

**Tipo:** AFK
**Bloqueado por:** Nenhum — pode iniciar imediatamente
**Status:** ✅ Concluído (commit `ce53555`)

### O que construir

Garantir que a busca de produtos dentro de uma comanda aberta retorne apenas produtos ativos. O hook de busca de produtos precisa aceitar um parâmetro opcional de filtro de status. A página de comanda aberta deve passar esse filtro como `ativo=true`. A rota de listagem de produtos no backend deve aceitar e repassar esse parâmetro ao repositório.

A página de cardápio (gestão) continua funcionando sem alteração — ela não passa o filtro, portanto recebe todos os produtos (comportamento atual via toggle próprio).

### Critérios de aceite

- [x] Desativar produto X → abrir comanda → buscar produto X → não aparece nos resultados
- [x] Produto X reativado → busca na comanda → aparece normalmente
- [x] `CardapioPage` continua exibindo produtos inativos no filtro "Inativos"
- [x] `GET /api/produtos?ativo=true` retorna apenas produtos com `ativo=true`
- [x] `GET /api/produtos` sem parâmetro continua retornando todos (sem quebra de comportamento existente)

### User stories endereçadas

- US3: Como garçom, quero que a busca de itens na comanda aberta mostre apenas produtos ativos, para não adicionar por engano um produto que foi desativado.
- US4: Como gerente, quero que produtos desativados continuem visíveis na tela de cardápio (com toggle de filtro), para gerenciar o histórico completo.

---

## Issue 3 — Toast de erro com duração automática ✅

**Tipo:** AFK
**Bloqueado por:** Nenhum — pode iniciar imediatamente
**Status:** ✅ Concluído (commit `82782c5`)

### O que construir

Alterar a configuração de duração do toast de erro no módulo centralizado de toasts. A duração atual é `Infinity` (fica para sempre). Deve passar para 8 segundos — tempo suficiente para ler mensagens longas sem bloquear a interface indefinidamente. O usuário ainda pode fechar clicando (comportamento padrão do sonner).

Durações finais: sucesso = 2500ms, erro = 8000ms, aviso = 4500ms.

Nenhuma alteração de backend necessária.

### Critérios de aceite

- [x] Toast de erro aparece e desaparece automaticamente após ~8 segundos
- [x] Toast de sucesso desaparece após ~2,5 segundos (sem regressão)
- [x] Toast de aviso desaparece após ~4,5 segundos (sem regressão)
- [x] Clicar em qualquer toast fecha imediatamente (comportamento padrão mantido)
- [x] Nenhum toast fica preso na tela indefinidamente

### User stories endereçadas

- US13: Como operador, quero que toasts de erro somam automaticamente após 8 segundos, para que não bloqueiem a interface indefinidamente.
- US14: Como operador, quero poder fechar um toast clicando nele a qualquer momento, independentemente da duração configurada.
- US15: Como operador, quero que toasts de sucesso somam em 2,5 segundos e toasts de aviso em 4,5 segundos, pois são informações menos críticas que erros.

---

## Issue 4 — Hierarquia de categorias no cardápio ✅

**Tipo:** AFK
**Bloqueado por:** Nenhum — pode iniciar imediatamente
**Status:** ✅ Concluído (commit `f721e1f`)

### O que construir

Substituir a exibição simples do nome de categoria na tabela do cardápio por um caminho hierárquico no formato `"Categoria > Subcategoria"`. O backend já retorna a árvore de categorias com `children[]` — basta construir os caminhos recursivamente no frontend a partir dessa estrutura.

Produto sem subcategoria exibe apenas o nome da categoria raiz. Produto sem categoria exibe "—". Nenhuma nova coluna na tabela. Nenhuma alteração de backend.

### Critérios de aceite

- [x] Produto na subcategoria "Sucos" (filha de "Bebidas") → coluna exibe "Bebidas > Sucos"
- [x] Produto na categoria raiz "Sobremesas" → coluna exibe "Sobremesas"
- [x] Produto sem categoria → coluna exibe "—"
- [x] Filtro de categoria na barra superior continua funcionando corretamente
- [x] Layout da tabela não quebra com nomes longos de hierarquia

### User stories endereçadas

- US16: Como gerente, quero ver o caminho completo da categoria de cada produto no cardápio (ex: "Bebidas > Sucos"), para identificar a hierarquia sem precisar abrir cada produto.
- US17: Como gerente, quero que produtos sem subcategoria mostrem apenas o nome da categoria principal, sem quebrar o layout.

---

## Issue 5 — Máscara monetária nos campos de valor ✅

**Tipo:** AFK
**Bloqueado por:** Nenhum — pode iniciar imediatamente
**Status:** ✅ Concluído (commit `7253919`)

### O que construir

Criar componente `MoneyInput` reutilizável usando `react-number-format` (`NumericFormat`) com prefixo `"R$ "`, separador decimal vírgula, separador de milhar ponto e duas casas decimais fixas. Comportamento: entrada da esquerda para direita — digitar `10` exibe `R$ 10,00`.

Instalar dependência `react-number-format` e aplicar o componente em:
- Campo de preço de venda no modal de produto (cardápio)
- Campos de custo total e custo unitário na tela de nova compra

### Critérios de aceite

- [x] `npm install react-number-format` registrado em `package.json`
- [x] Digitar `1050` no campo de preço → exibe `R$ 1.050,00`
- [x] Digitar `10` → exibe `R$ 10,00` (duas casas fixas)
- [x] Digitar `0,50` → exibe `R$ 0,50`
- [x] Valor submetido ao backend é número sem máscara (não inclui "R$ ")
- [x] Campo de preço de venda no `ProdutoModal` usa `MoneyInput`
- [x] Campos de custo total e custo unitário em `NovaCompraPage` usam `MoneyInput`
- [x] Cálculo de total da compra continua correto após troca do input

### User stories endereçadas

- US18: Como gerente, quero que o campo de preço de venda no cadastro de produtos exiba o prefixo "R$" e formate automaticamente os centavos enquanto digito, para reduzir erros de valor.
- US19: Como gerente, quero que os campos de custo total e custo unitário na tela de compras tenham a mesma formatação monetária, para consistência visual.
- US20: Como gerente, quero digitar "1050" e ver "R$ 10,50" formatado automaticamente, com vírgula decimal e ponto separador de milhar no padrão brasileiro.

---

## Issue 6 — Validação inline de categoria no produto ✅

**Tipo:** AFK
**Bloqueado por:** Nenhum — pode iniciar imediatamente
**Status:** ✅ Concluído (commit `f678076`)

### O que construir

Adicionar validação obrigatória de `categoria_id` no schema Zod do formulário de produto. Atualmente o campo é `nullable().optional()` — sem validação frontend. Ao tentar salvar sem categoria, deve aparecer mensagem de erro diretamente abaixo do select de categoria, no mesmo padrão visual dos outros campos do formulário.

O botão de salvar não deve disparar chamada ao backend quando o campo obrigatório está vazio — a validação Zod bloqueia antes. O backend mantém sua constraint como segunda camada de defesa.

### Critérios de aceite

- [x] Salvar produto sem categoria → erro inline aparece abaixo do select ("Selecione uma categoria")
- [x] Select de categoria fica destacado em vermelho quando inválido
- [x] Nenhuma chamada à API é disparada com categoria vazia
- [x] Selecionar uma categoria → erro some imediatamente
- [x] Editar produto existente com categoria → formulário abre sem erro
- [x] Criar produto com categoria válida → salva normalmente

### User stories endereçadas

- US11: Como gerente, quero ver uma mensagem de erro diretamente abaixo do campo de categoria quando tento salvar um produto sem categoria, para saber exatamente o que corrigir.
- US12: Como gerente, quero que o botão de salvar produto não dispare uma chamada ao servidor quando campos obrigatórios estão vazios, para evitar erros desnecessários.

---

## Issue 7 — Tipo em método de pagamento ✅

**Tipo:** AFK
**Bloqueado por:** Nenhum — pode iniciar imediatamente
**Status:** ✅ Concluído (commit `6b73d80`)

### O que construir

Adicionar coluna `tipo` (enum: `dinheiro`, `credito`, `debito`, `pix`, `outro`) ao model de métodos de pagamento, com `server_default="outro"`. Incluir o campo no schema de response e no modal de criação/edição, para que operadores possam classificar cada método.

Migration additive — não remove nem altera colunas existentes. Métodos existentes recebem `tipo="outro"` automaticamente.

### Critérios de aceite

- [x] Migration aplicada sem erro em banco existente
- [x] Métodos existentes têm `tipo="outro"` após migration
- [x] Modal de criar/editar método exibe select de tipo com as 5 opções
- [x] `GET /api/metodos-pagamento` inclui campo `tipo` no response
- [x] Criar método "Dinheiro" com tipo "dinheiro" → response confirma `tipo: "dinheiro"`
- [x] Editar método existente → campo tipo preenchido com valor atual

### User stories endereçadas

- US10: Como gerente, quero classificar métodos de pagamento por tipo (dinheiro, crédito, débito, pix, outro), para que o sistema identifique corretamente quando exibir o campo de troco.

---

## Issue 8 — Troco no pagamento em dinheiro ✅

**Tipo:** AFK
**Bloqueado por:** Issue 7 (tipo em método de pagamento precisa existir para detecção de "dinheiro")
**Status:** ✅ Concluído (commit `6513eb5`)

### O que construir

Implementar captura de troco end-to-end para pagamentos em dinheiro.

**Backend:** adicionar colunas `valor_nota` (Numeric, nullable) e `troco` (Numeric, nullable) à tabela de pagamentos. Aceitar `valor_nota` opcional no request de fechamento. Quando o método selecionado tem `tipo="dinheiro"` e `valor_nota` é informado, calcular e persistir o troco. Validar que `valor_nota >= valor` quando fornecido.

**Frontend — tela de fechamento:** quando o método selecionado tem `tipo="dinheiro"`, exibir inline abaixo do campo de valor: input "Valor da nota recebida" e campo read-only "Troco a devolver" calculado em tempo real. Se `valor_nota < valor`, exibir aviso em vermelho. O campo é opcional — não preencher não bloqueia o fechamento.

**Frontend — comprovante:** quando pagamento tem `troco > 0`, exibir linhas "Valor recebido" e "Troco" no comprovante.

### Critérios de aceite

- [x] Migration de `valor_nota` e `troco` aplicada sem erro
- [x] Selecionar método com `tipo="dinheiro"` na tela de fechamento → campos de nota e troco aparecem
- [x] Selecionar método com outro tipo → campos de nota/troco não aparecem
- [x] Digitar valor da nota → troco calculado em tempo real (`nota - valor_pagamento`)
- [x] Nota menor que o total → aviso vermelho "Nota insuficiente"
- [x] Fechar comanda sem preencher valor da nota → fecha normalmente (campo opcional)
- [x] Fechar com nota R$50 para total R$37,50 → `valor_nota=50`, `troco=12.50` persistidos no banco
- [x] Comprovante com troco > 0 exibe "Valor recebido: R$ 50,00" e "Troco: R$ 12,50"
- [x] Comprovante sem troco não exibe essas linhas

### User stories endereçadas

- US5: Como operador de caixa, quero informar o valor da nota recebida ao selecionar "Dinheiro" como método de pagamento, para calcular automaticamente o troco.
- US6: Como operador de caixa, quero ver o troco calculado em tempo real enquanto digito o valor da nota, para confirmar antes de fechar a comanda.
- US7: Como operador de caixa, quero ser avisado quando o valor da nota for inferior ao total a pagar, para corrigir antes de confirmar.
- US8: Como operador de caixa, quero que o valor da nota e o troco sejam registrados no banco de dados, para auditoria e conferência de caixa.
- US9: Como cliente, quero que o comprovante da comanda mostre o valor recebido e o troco, para ter registro completo da transação.

---

## Issue 9 — Reserva de estoque no ciclo da comanda ✅

**Tipo:** HITL
**Bloqueado por:** Nenhum — pode iniciar imediatamente
**Status:** ✅ Concluído (commit `e16c839`)

### O que construir

Implementar reserva de estoque durante o ciclo de vida da comanda, com aviso imediato de insuficiência ao adicionar itens.

**Migration:** adicionar coluna `estoque_reservado` (Numeric 12,4, NOT NULL, default 0) à tabela de insumos.

**Ao adicionar item à comanda:** calcular insumos necessários via ficha técnica e incrementar `estoque_reservado`. Calcular `estoque_disponivel = estoque_atual - estoque_reservado`. Se disponível < 0 para qualquer insumo, incluir o nome na lista `estoque_insuficiente` do response. O item é adicionado normalmente — o aviso não bloqueia.

**Ao cancelar item:** decrementar `estoque_reservado` dos insumos do item, com piso em zero.

**Ao cancelar comanda inteira:** decrementar `estoque_reservado` para todos os itens ativos da comanda.

**Ao fechar comanda (definitivo):** além de debitar `estoque_atual` (comportamento existente), decrementar `estoque_reservado` pela mesma quantidade, com piso em zero.

**Pagamento parcial:** reserva permanece intacta — `estoque_atual` não é debitado nem `estoque_reservado` alterado em pagamentos parciais (comportamento já existente para o débito).

**Frontend:** quando response de "adicionar item" contém `estoque_insuficiente` com um ou mais nomes, exibir toast de aviso para cada insumo: "Estoque insuficiente: [nome do insumo]".

### Critérios de aceite

- [x] Migration aplicada sem erro — todos os insumos existentes com `estoque_reservado=0`
- [x] Adicionar hambúrguer (usa 2 pães) com estoque de pão = 1 → item adicionado + toast "Estoque insuficiente: Pão de hambúrguer"
- [x] Adicionar hambúrguer com estoque de pão = 5 → item adicionado sem toast
- [x] `estoque_reservado` do pão incrementa em 2 após adição do hambúrguer
- [x] Cancelar o item de hambúrguer → `estoque_reservado` do pão decrementa em 2
- [x] `estoque_reservado` nunca fica negativo (piso em zero)
- [x] Cancelar comanda inteira → `estoque_reservado` de todos os insumos retorna ao valor anterior
- [x] Fechar comanda → `estoque_atual` debitado E `estoque_reservado` decrementado (ambos)
- [x] Pagamento parcial → nem `estoque_atual` nem `estoque_reservado` são alterados
- [x] Comanda com produto sem ficha técnica → adição não gera erro, `estoque_insuficiente` vazio

### User stories endereçadas

- US21: Como garçom, quero receber um aviso imediato quando adiciono um produto cujos insumos estão insuficientes em estoque, para informar o cliente na hora.
- US22: Como garçom, quero poder adicionar o produto mesmo com estoque insuficiente (o aviso não bloqueia), para casos em que o gerente já sabe do reabastecimento pendente.
- US23: Como gerente, quero que os insumos sejam "reservados" quando adicionados a uma comanda aberta, para que o estoque disponível reflita apenas o que não está comprometido.
- US24: Como gerente, quero que a reserva de insumos seja liberada automaticamente quando um item é cancelado dentro de uma comanda, para que o estoque disponível seja atualizado em tempo real.
- US25: Como gerente, quero que a reserva seja liberada quando uma comanda inteira é cancelada, sem afetar o estoque definitivo.
- US26: Como gerente, quero que o estoque seja debitado definitivamente apenas quando a comanda é fechada com pagamento confirmado.
- US27: Como gerente, quero que pagamentos parciais não debitam o estoque — o débito ocorre apenas no fechamento total da comanda.

---

## Issue 10 — Visibilidade de estoque reservado ✅

**Tipo:** AFK
**Bloqueado por:** Issue 9 (coluna `estoque_reservado` precisa existir no banco)
**Status:** ✅ Concluído (commit `2a8228d`)

### O que construir

Expor `estoque_reservado` e `estoque_disponivel` (calculado: `estoque_atual - estoque_reservado`) no response de insumos. Adicionar colunas "Reservado" e "Disponível" na tabela da tela de estoque/insumos. A coluna "Disponível" fica destacada em vermelho quando negativa.

### Critérios de aceite

- [x] `GET /api/insumos` inclui `estoque_reservado` e `estoque_disponivel` no response
- [x] Tela de estoque exibe colunas "Estoque atual", "Reservado" e "Disponível"
- [x] Insumo com `estoque_atual=5`, `estoque_reservado=3` → "Disponível" exibe 2
- [x] Insumo com `estoque_atual=1`, `estoque_reservado=3` → "Disponível" exibe -2 em vermelho
- [x] Insumo sem reservas → "Reservado" exibe 0, "Disponível" igual a "Estoque atual"
- [x] Layout da tabela não quebra com as novas colunas

### User stories endereçadas

- US28: Como gerente, quero ver na tela de estoque/insumos três valores separados: "Estoque atual", "Reservado em comandas" e "Disponível", para entender o estado real do estoque.
- US29: Como gerente, quero que o campo "Disponível" fique destacado em vermelho quando for negativo, para identificar imediatamente insumos críticos.

---

## Resumo

| # | Título | Tipo | Bloqueado por | Status |
|---|--------|------|--------------|--------|
| 1 | Inverter mesa/nome na nova comanda | AFK | — | ✅ |
| 2 | Filtrar produtos ativos na busca da comanda | AFK | — | ✅ |
| 3 | Toast de erro com duração automática | AFK | — | ✅ |
| 4 | Hierarquia de categorias no cardápio | AFK | — | ✅ |
| 5 | Máscara monetária nos campos de valor | AFK | — | ✅ |
| 6 | Validação inline de categoria no produto | AFK | — | ✅ |
| 7 | Tipo em método de pagamento | AFK | — | ✅ |
| 8 | Troco no pagamento em dinheiro | AFK | #7 | ✅ |
| 9 | Reserva de estoque no ciclo da comanda | HITL | — | ✅ |
| 10 | Visibilidade de estoque reservado | AFK | #9 | ✅ |

**10/10 issues concluídas. v0.4 completa.**
