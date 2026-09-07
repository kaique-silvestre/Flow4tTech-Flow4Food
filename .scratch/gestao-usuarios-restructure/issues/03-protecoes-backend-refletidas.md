# 03: Três proteções do backend refletidas no front (perfil, permissões, editar Proprietário)

**What to build:** As três regras que `users_service.py` já aplica (não pode alterar o próprio perfil, não pode alterar as próprias permissões, um Proprietário só pode ser editado por si mesmo) deixam de aparecer só como erro 409 depois de salvar — os controles correspondentes ficam desabilitados no front, com explicação, antes de tentar.

**Blocked by:** 02 (Ações em dropdown) — o item "Editar" desabilitado vive dentro do dropdown

**Touches:** `frontend/src/features/configuracoes/usuarios/UserModal.tsx`, `frontend/src/features/configuracoes/usuarios/GestaoUsuariosPage.tsx`

**Nature:** objective

**Status:** ready-for-agent

- [x] `UserModal.tsx`: campo de Perfil (`select` de `profile_id`) fica `disabled` quando `editing` é o usuário logado (`currentUser?.user_id === editing.id`)
- [x] Texto de apoio junto ao campo desabilitado: "Você não pode alterar seu próprio perfil"
- [x] `UserModal.tsx`: grade de checkboxes de `screens` fica com todos os inputs `disabled` quando editando a si mesmo (mesma condição acima), independente de ser ou não Proprietário
- [x] Texto de apoio junto à grade desabilitada: "Você não pode alterar suas próprias permissões"
- [x] `GestaoUsuariosPage.tsx`: item "Editar" do dropdown fica `disabled` quando `user.is_owner && !isSelf`
- [x] Texto de apoio (tooltip ou texto no próprio item): "Usuário proprietário só pode ser editado por si mesmo"
- [x] Quando o próprio Proprietário edita a si mesmo, "Editar" continua liberado (nome/email/username editáveis; só perfil e permissões próprias ficam bloqueados, cobertos pelos itens acima)
- [x] Nenhuma mudança de backend — `users_service.py` não é alterado, as três regras já existem e só são espelhadas
