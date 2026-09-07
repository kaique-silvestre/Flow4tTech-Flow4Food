# 06: Rodapé fixo (Configurações + Sair) com teste de permissão

**What to build:** "Configurações" e "Sair" saem da lista rolável de navegação e ficam fixos num bloco não-rolável no final da sidebar, separados visualmente do resto do menu. "Configurações" continua respeitando a permissão do usuário (tela some se não tiver acesso) e, ao clicar, expande seus filhos (Configurações Gerais, Usuários) usando o mesmo mecanismo de accordion inline da ticket 04 — não um padrão de interação separado. "Sair" dispara o mesmo fluxo de logout que já existe no dropdown do avatar do topbar.

**Blocked by:** 02, 04

**Touches:** `frontend/src/components/layout/Sidebar.tsx`, `frontend/src/components/layout/Topbar.tsx`, `frontend/src/components/layout/Sidebar.test.tsx` (novo)

**Nature:** mixed

- [ ] "Configurações" (com filhos Configurações Gerais, Usuários) e "Sair" renderizados num bloco fixo fora do `<nav>` rolável.
- [ ] Visibilidade de "Configurações" e de cada filho segue a mesma lógica de permissão já existente (`visibleChildren`/`usePermissions()`), só reposicionada.
- [ ] Clicar em "Configurações" no rodapé expande/colapsa os filhos inline, reusando o mecanismo de accordion da ticket 04 (mesmo componente/lógica, não uma implementação paralela).
- [ ] Lógica de logout extraída pra uma função/hook compartilhado, usado tanto pelo "Sair" do rodapé da sidebar quanto pelo item "Sair" do dropdown do avatar no `Topbar.tsx` — sem duplicar `clearToken`+`navigate`+`toast`.
- [ ] Teste RTL novo (`Sidebar.test.tsx`), seedando `useAuthStore` diretamente (sem mock de hook):
  - [ ] Usuário com permissão `"configuracoes"` ou `"gestao_usuarios"`: "Configurações" aparece no rodapé.
  - [ ] Usuário sem nenhuma das duas: "Configurações" não aparece; "Sair" continua aparecendo (não depende de permissão de tela).
  - [ ] Usuário só com `"gestao_usuarios"`: "Configurações" aparece, expandir mostra só "Usuários" (não "Configurações Gerais").
  - [ ] "Sair" sempre presente e dispara a função de logout compartilhada ao clicar.
