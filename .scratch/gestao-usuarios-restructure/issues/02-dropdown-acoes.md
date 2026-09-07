# 02: Ações em dropdown (Usuários e Perfis)

**What to build:** As ações por linha (Editar/Desativar/Ativar em Usuários; Editar-ou-Ver/Desativar/Ativar em Perfis) saem dos botões soltos e viram um único menu de ações (`components/ui/dropdown-menu.tsx`) por linha.

**Blocked by:** 01 (Migrar tabela de Usuários/Perfis + avatar + badge)

**Touches:** `frontend/src/features/configuracoes/usuarios/GestaoUsuariosPage.tsx`

**Nature:** objective

**Status:** ready-for-agent

- [x] Linha de Usuário tem um único `DropdownMenu` com itens "Editar" e "Desativar"/"Ativar" (rótulo conforme `is_active`, como hoje)
- [x] Item "Desativar" ausente do menu quando `isSelf || user.is_owner` (mesma lógica atual, agora como item ausente em vez de botão ausente)
- [x] Linha de Perfil tem um único `DropdownMenu` com itens "Editar"/"Ver" (rótulo condicional a `profile.name === "Admin"`, preservado) e "Desativar"/"Ativar" (`disabled` quando `!canToggle` — perfil Admin ou com usuários vinculados)
- [x] Nenhum item novo de menu adicionado (sem "Redefinir senha" ou outras ações que não existem hoje)
- [x] Todas as ações continuam disparando exatamente o mesmo comportamento de antes (mutations, confirm dialogs)
