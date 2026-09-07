# 04: Aba ativa (Usuários/Perfis) via query param

**What to build:** A aba ativa de `/configuracoes/usuarios` passa a ser um query param (`?tab=usuarios` | `?tab=perfis`) em vez de `useState` local — endereçável, compartilhável, e o botão voltar do navegador desfaz a troca de aba.

**Blocked by:** None (can start immediately)

**Touches:** `frontend/src/features/configuracoes/usuarios/GestaoUsuariosPage.tsx`

**Nature:** objective

**Status:** ready-for-agent

- [x] Aba ativa lida de `useSearchParams` (`?tab=usuarios` default, `?tab=perfis`)
- [x] Trocar de aba chama `setSearchParams`
- [x] Abrir `/configuracoes/usuarios?tab=perfis` diretamente já carrega na aba Perfis
- [x] Botão voltar do navegador desfaz a troca de aba
- [x] Breadcrumb "Configurações > Usuários" continua funcionando sem alteração (item estático em `NAV_ITEMS`, não muda)
- [x] Filtros internos de cada aba (busca, filtro de perfil, mostrar inativos) continuam como estado local — não entram na URL
