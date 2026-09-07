# 03: Componente DashboardCard (wrapper com "?" popover, skeleton, motion)

**What to build:** Novo componente `DashboardCard` em `frontend/src/features/dashboard/components/` que padroniza: título, botão "?" no canto superior direito (abre `Popover` com `helpText`), skeleton de loading, e slot de conteúdo. Usar `Popover`/`PopoverTrigger`/`PopoverContent` já existentes em `@/components/ui/popover.tsx`. Aplicar motion com restraint (spring criticamente amortecido sem bounce, cross-fade loading→conteúdo, respeita `prefers-reduced-motion`).

**Blocked by:** None (can start immediately) — mas é fundacional para os tickets 04-08, que consomem este componente.

**Touches:** `frontend/src/features/dashboard/components/DashboardCard.tsx` (novo), `frontend/src/features/dashboard/DashboardPage.test.tsx` (novo — primeiro teste RTL do dashboard)

**Nature:** mixed

**Status:** ready-for-agent

- [ ] `DashboardCard` aceita props: `title`, `helpText`, `loading` (boolean), `onClick`/`href` opcional (navegação, ex. comissões→garçons), `children`
- [ ] Botão "?" abre `Popover` ancorado nele (não centralizado na tela), conteúdo = `helpText` (texto curto, 1-2 frases, linguagem simples sem jargão)
- [ ] Escopo local em `frontend/src/features/dashboard/components/` — NÃO promover para `components/ui/` nesta spec (YAGNI, decisão do grill)
- [ ] Loading→conteúdo: cross-fade (opacity), nunca slide
- [ ] Transição do popover: spring criticamente amortecido (`damping: 1.0`, sem bounce) — informacional, sem gesto de arrasto
- [ ] `prefers-reduced-motion: reduce` respeitado: cross-fade vira transição de opacidade curta sem spring, popover sem spring
- [ ] `transform-origin` do popover ancorado no botão "?" que o disparou (comportamento padrão do Radix Popover — garantir que nenhum CSS custom sobrescreva)
- [ ] Nenhuma dependência nova instalada (Popover Radix já instalado, Tailwind 3.4, shadcn já configurado)
- [ ] Primeiro teste RTL do dashboard criado (`DashboardPage.test.tsx`), mockando `useDashboard` (padrão de `usePlatformApi.test.tsx` como prior art de mock/wrapper) — estabelece o padrão de teste de UI para as próximas tickets do dashboard usarem. Casos mínimos aqui: card renderiza título/helpText, clicar em "?" abre popover com o texto esperado, loading mostra skeleton
- [ ] Não portar `hero-195`/`BorderBeam` — fora de escopo, decidido
