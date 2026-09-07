# 04: DropdownMenu em Métodos de Pagamento (ações por linha, com item desabilitado)

**What to build:** `MetodosPagamentoPage.tsx` troca os botões soltos ("Editar" + "Desativar"/"Ativar", com "Desativar"/"Remover" desabilitados quando `metodo.padrao === true`) por um único `DropdownMenu`, mesmo padrão de Insumos/Fornecedores (ticket 03) e Garçons/Gestão de Usuários.

**Blocked by:** None (can start immediately) — mas ler o ticket 03 primeiro pelo padrão base

**Touches:** `frontend/src/features/cadastros/metodos_pagamento/MetodosPagamentoPage.tsx`

**Nature:** objective

**Status:** ready-for-agent

**Atenção — bug já encontrado e corrigido em Gestão de Usuários (commit `10e1851`)**: o `disabled` do Radix `DropdownMenuItem` NÃO bloqueia sozinho o `onClick` passado — ele só impede a seleção interna do Radix e adiciona `aria-disabled`/`data-disabled`. Todo item desabilitado deste ticket precisa de um guard explícito (`if (metodo.padrao) return;`) dentro do próprio handler do `onClick`, não confiar só na prop `disabled`.

- [ ] Linha de Método de Pagamento tem um único `DropdownMenu` com itens "Editar", "Desativar"/"Ativar" e (se existir separado) "Remover"
- [ ] Item "Desativar" fica `disabled` (com guard explícito no handler, não só a prop) quando `metodo.padrao === true`, com texto de apoio "Método padrão não pode ser desativado" (tooltip ou texto no item)
- [ ] Item "Remover" (se existir) fica `disabled` (com guard explícito) quando `metodo.padrao === true`, com texto de apoio "Método padrão não pode ser removido"
- [ ] Teste de regressão: clicar no item desabilitado NÃO dispara a mutation (replicar o teste que provou o bug em `GestaoUsuariosPage.test.tsx`)
- [ ] Badge de status, busca normalizada e paginação (já existentes) continuam funcionando sem regressão
- [ ] Nenhuma mudança de backend
