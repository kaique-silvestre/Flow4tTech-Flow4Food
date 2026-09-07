# 07: Breadcrumb "Empresa / Página" no topbar

**What to build:** O título estático "Flow4Food" no topbar é substituído por um breadcrumb "NomeDaEmpresa / PáginaAtual", sempre com exatamente 2 níveis — inclusive em rotas raiz como Dashboard, que hoje não mostram breadcrumb nenhum. Rota que não bate com nenhum item do menu mostra só o nome da empresa (1 nível), nunca um label inventado.

**Blocked by:** 01

**Touches:** `frontend/src/components/layout/Topbar.tsx`, `frontend/src/components/layout/Breadcrumb.tsx`, `frontend/src/components/layout/AppLayout.tsx`

**Nature:** mixed

- [ ] `<span>Flow4Food</span>` estático removido do `Topbar.tsx`.
- [ ] Renderização do breadcrumb movida de dentro de `<main>` (`AppLayout.tsx`) pra dentro do `Topbar.tsx`.
- [ ] `buildCrumbs(pathname)` exportada de `Breadcrumb.tsx` (hoje não-exportada).
- [ ] `buildCrumbs` sempre retorna 2 segmentos pra rota reconhecida: `[tenant_name, label da página atual]` — inclusive pra itens de topo sem filho (Dashboard, Cardápio), que hoje retornam `[]`.
- [ ] Pra subitem de grupo (ex: Estoque > Movimentos), mantém exatamente 2 segmentos: `[tenant_name, label do filho]`, nunca 3 (sem o grupo pai).
- [ ] Pra rota não reconhecida por nenhum item/filho de `NAV_ITEMS`, retorna 1 segmento: `[tenant_name]`, sem inventar label.
- [ ] Testes unitários (Vitest puro, sem DOM) para `buildCrumbs`: rota raiz, rota de subitem de grupo, rota não reconhecida.
