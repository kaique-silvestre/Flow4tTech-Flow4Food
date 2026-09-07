# 02: Padronizar FornecedoresPage (tabela, busca, badge, linha inativa)

**What to build:** `/cadastros/fornecedores` usa `components/ui/table.tsx`, ganha busca normalizada por nome, badge de status via `components/ui/badge.tsx`, e a linha inativa perde o `opacity-60` extra (fica só com `line-through`, igual às outras telas de Cadastros).

**Blocked by:** Ticket 01 da spec `.scratch/cardapio-restructure/` (Componente Table)

**Touches:** `frontend/src/features/cadastros/fornecedores/FornecedoresPage.tsx`

**Nature:** objective

**Status:** ready-for-agent

- [x] Tabela usa `Table`/`TableHeader`/`TableBody`/`TableRow`/`TableHead`/`TableCell` de `components/ui/table.tsx`
- [x] Campo de busca por nome, normalizado (NFD + lowercase) — funciona junto com o filtro Ativos/Inativos/Todos
- [x] Status usa `<Badge variant="outline" ...>` em vez do `<span>` inline
- [x] Linha inativa perde o `opacity-60` — fica só com `line-through` no nome, igual Insumos/Garçons/Métodos de Pagamento
- [x] Paginação existente continua funcionando sem regressão
- [x] Digitar na busca reseta a página para 1
