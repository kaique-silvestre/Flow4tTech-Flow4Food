# 03: Padronizar GarconsPage (tabela, busca, badge, dropdown de ações)

**What to build:** `/cadastros/garcons` usa `components/ui/table.tsx`, ganha busca normalizada por nome, badge de status via `components/ui/badge.tsx`, e as três ações por linha (Ver Comissões, Editar, Desativar/Ativar) viram um único `DropdownMenu`.

**Blocked by:** Ticket 01 da spec `.scratch/cardapio-restructure/` (Componente Table)

**Touches:** `frontend/src/features/cadastros/garcons/GarconsPage.tsx`

**Nature:** objective

**Status:** ready-for-agent

- [x] Tabela usa `Table`/`TableHeader`/`TableBody`/`TableRow`/`TableHead`/`TableCell` de `components/ui/table.tsx`
- [x] Campo de busca por nome, normalizado (NFD + lowercase) — funciona junto com o filtro Ativos/Inativos/Todos
- [x] Status usa `<Badge variant="outline" ...>` em vez do `<span>` inline
- [x] As três ações (Ver Comissões, Editar, Desativar/Ativar) viram um único `DropdownMenu` por linha (`components/ui/dropdown-menu.tsx`)
- [x] Linha inativa mantém `line-through` no nome (sem `opacity` extra)
- [x] Paginação existente continua funcionando sem regressão
- [x] Digitar na busca reseta a página para 1
- [x] `GarcomComissoesModal` (abre a partir de "Ver Comissões" no dropdown) continua abrindo sem regressão
