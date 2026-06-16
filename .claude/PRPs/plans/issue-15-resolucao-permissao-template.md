# PRP — Issue #15: Resolução de permissão via template
**GitHub Issue:** #15 | **Type:** AFK | **Depende de:** #11

## Contexto
`_build_token_response` e `rotate_refresh_token` em `auth_service.py` leem permissões
diretamente de `user.profile.permissions` (ProfilePermission). Perfis com `template_id`
devem usar `template.permissions` (TemplatePermission) em vez disso — sem copiar para
`profile_permissions`.

Problema adicional: `_with_profile` em `users_repository.py` só faz joinedload de
`Profile.permissions`, não de `Profile.template` + `PermissionTemplate.permissions`.
Precisa carregar ambos eager.

## Tarefas
- [ ] A1. `users_repository.py` — `_with_profile` adicionar joinedload de `Profile.template` e `PermissionTemplate.permissions`
- [ ] A2. `auth_service.py` — criar helper `resolve_permissions(user) → list[str]`:
           SE `user.profile.template_id IS NOT NULL` → `[p.screen for p in user.profile.template.permissions if p.can_access]`
           SE `user.profile.template_id IS NULL` → `[p.screen for p in user.profile.permissions if p.can_access]`
           SE `user.profile_id IS NULL` → `[]` (placeholder para #18)
- [ ] A3. `_build_token_response`: substituir `[p.screen for p in user.profile.permissions if p.can_access]` por `resolve_permissions(user)`
- [ ] A4. `rotate_refresh_token`: mesma substituição na linha 105
- [ ] B1. Teste: login com perfil `template_id` SET → JWT contém telas do template
- [ ] B2. Teste: login com perfil `template_id` NULL → JWT contém telas de `profile_permissions`
- [ ] B3. Teste: `rotate_refresh_token` com perfil template → emite telas do template

## Arquivos-chave
- `backend/src/services/auth_service.py` — linhas 56 e 105
- `backend/src/repositories/users_repository.py` — `_with_profile` linha 10
- `backend/src/models/profiles.py` — Profile.template, PermissionTemplate.permissions
- `backend/tests/test_auth.py` — adicionar B1–B3

## Validações
```bash
cd backend && python -m pytest
```
