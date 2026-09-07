# 01: Migrar tabela de Usuários/Perfis + avatar de iniciais + badge de status

**What to build:** As tabelas de Usuários e Perfis em `/configuracoes/usuarios` usam `components/ui/table.tsx` em vez de `<table>` cru, com alinhamento e hover consistentes com as outras telas já padronizadas. A coluna de usuário ganha um círculo com as iniciais do nome (sem foto). O status Ativo/Inativo usa `components/ui/badge.tsx` em vez do `<span>` inline repetido.

**Blocked by:** Ticket 01 da spec `.scratch/cardapio-restructure/` (Componente Table + migrar tabela do Cardápio) — precisa que `components/ui/table.tsx` exista

**Touches:** `frontend/src/features/configuracoes/usuarios/GestaoUsuariosPage.tsx`, novo `UserAvatarInitials` (ou similar) em `frontend/src/features/configuracoes/usuarios/`

**Nature:** objective

**Status:** ready-for-agent

- [x] Tabelas de Usuários e Perfis usam `Table`/`TableHeader`/`TableBody`/`TableRow`/`TableHead`/`TableCell` de `components/ui/table.tsx`
- [x] Componente de avatar de iniciais: círculo colorido com `getInitials(nome)` (split por espaço, primeira letra de cada parte, uppercase, join), sem `AvatarImage`/upload — nenhuma dependência `@radix-ui/react-avatar` instalada
- [x] Avatar aparece ao lado do nome na tabela de Usuários
- [x] Badge de status (Ativo/Inativo) usa `<Badge variant="outline" ...>` em vez de `<span className="rounded-full ...">`, aplicado em Usuários e Perfis
- [x] Badge "Proprietário" (`is_owner`) continua visível como hoje
- [x] Coluna "Sistema" (perfil `is_system`) continua visível como hoje
- [x] Busca/filtro por perfil/checkbox "Mostrar inativos" continuam funcionando sem regressão
- [x] Nenhuma dependência nova instalada além do que já está no projeto
