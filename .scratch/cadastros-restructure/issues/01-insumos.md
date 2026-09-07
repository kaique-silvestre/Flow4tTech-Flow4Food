# 01: Padronizar InsumosPage (tabela, busca, badge, alinhamento)

**What to build:** `/cadastros/insumos` usa `components/ui/table.tsx`, ganha busca normalizada por nome, badge de status via `components/ui/badge.tsx`, e a coluna "Estoque" passa a alinhar à direita.

**Blocked by:** Ticket 01 da spec `.scratch/cardapio-restructure/` (Componente Table)

**Touches:** `frontend/src/features/cadastros/insumos/InsumosPage.tsx`

**Nature:** objective

**Status:** ready-for-agent

- [x] Tabela usa `Table`/`TableHeader`/`TableBody`/`TableRow`/`TableHead`/`TableCell` de `components/ui/table.tsx`
- [x] Coluna "Estoque" alinhada à direita; "Nome"/"Unidade" continuam à esquerda
- [x] Campo de busca por nome, normalizado (NFD + lowercase, mesmo mecanismo do Cardápio) — "agua" encontra "Água"
- [x] Busca funciona junto com o filtro Ativos/Inativos/Todos existente
- [x] Status (Ativo/Inativo) usa `<Badge variant="outline" ...>` em vez do `<span>` inline
- [x] Linha inativa mantém `line-through` no nome (sem `opacity` extra)
- [x] Paginação existente continua funcionando sem regressão
- [x] Digitar na busca reseta a página para 1
