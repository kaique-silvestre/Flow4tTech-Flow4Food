# 04: Padronizar MetodosPagamentoPage (tabela, busca, badge, paginação, explicar bloqueio de padrão)

**What to build:** `/cadastros/metodos-pagamento` usa `components/ui/table.tsx`, ganha busca normalizada por nome, badge de status, paginação (única das quatro telas de Cadastros sem ela hoje), e os itens "Desativar"/"Remover" ficam desabilitados com explicação (em vez de ausentes) quando o método é `padrao`.

**Blocked by:** Ticket 01 da spec `.scratch/cardapio-restructure/` (Componente Table)

**Touches:** `frontend/src/features/cadastros/metodos_pagamento/MetodosPagamentoPage.tsx`

**Nature:** objective

**Status:** ready-for-agent

- [x] Tabela usa `Table`/`TableHeader`/`TableBody`/`TableRow`/`TableHead`/`TableCell` de `components/ui/table.tsx`
- [x] Campo de busca por nome, normalizado (NFD + lowercase) — funciona junto com o filtro Ativos/Inativos/Todos
- [x] Status usa `<Badge variant="outline" ...>` em vez do `<span>` inline
- [x] Paginação adicionada (`components/ui/pagination.tsx` + `paginar`, mesmo padrão das outras três telas de Cadastros)
- [x] Digitar na busca reseta a página para 1
- [x] Quando `metodo.padrao === true`: botão/item "Desativar" fica `disabled` (não ausente) com texto de apoio "Método padrão não pode ser desativado"
- [x] Quando `metodo.padrao === true`: botão/item "Remover" fica `disabled` (não ausente) com texto de apoio "Método padrão não pode ser removido"
- [x] Linha inativa mantém `line-through` no nome (sem `opacity` extra)
- [x] Nenhuma mudança de backend — `metodos_pagamento_service.py` não é alterado
