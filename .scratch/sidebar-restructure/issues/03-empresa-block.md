# 03: Bloco "Empresa" no topo da sidebar

**What to build:** Usuário logado vê, no topo da sidebar (estado expandido), um quadrado com a letra inicial da empresa, o nome completo da empresa e o status da assinatura como subtítulo (ex: "Ativa", "Trial") — tudo estático, sem indicar que é clicável (sem chevron, sem hover de botão).

**Blocked by:** 01

**Touches:** `frontend/src/stores/authStore.ts`, `frontend/src/components/layout/Sidebar.tsx`, `frontend/src/features/platform/subscriptionStatus.ts`

**Nature:** mixed

- [ ] `AuthUser` (em `authStore.ts`) ganha `tenant_name: string`, populado a partir do decode do JWT (nenhuma chamada de rede nova).
- [ ] Novo bloco no topo da sidebar: quadrado `rounded-md` com a primeira letra de `tenant_name`, nome completo truncado se longo, subtítulo com label amigável do `subscription_status` (reaproveitar `SUBSCRIPTION_STATUS_LABELS` de `subscriptionStatus.ts`, sem duplicar o mapa).
- [ ] Bloco não tem `cursor-pointer`, não tem hover de botão, não tem chevron/seta.
- [ ] Sem `tenant_name`/`subscription_status` no token (ex: usuário com token antigo, edge case improvável mas defensivo), bloco não quebra o layout — mostra o que tiver disponível de forma graciosa.
