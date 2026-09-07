# 04: Accordion inline (expandida) + flyout mantido (colapsada)

**What to build:** Com a sidebar expandida, clicar num grupo com filhos (Vendas, Estoque, Financeiro, Relatórios, Cadastros) expande os subitens inline, embaixo do próprio grupo, com animação de altura (sem flyout flutuante). Com a sidebar colapsada (rail de ícones), o comportamento de hoje é mantido: clicar no grupo abre o flyout via portal ao lado do ícone.

**Blocked by:** 02

**Touches:** `frontend/src/components/layout/Sidebar.tsx`

**Nature:** mixed

- [ ] Sidebar expandida: clicar num grupo com filhos expande/colapsa os filhos inline, abaixo do grupo, com transição de altura animada (técnica CSS grid `grid-rows-[0fr]`→`grid-rows-[1fr]`, sem `overflow` cortando o conteúdo durante a transição).
- [ ] Sidebar colapsada: grupo com filhos continua abrindo o flyout via portal existente (`renderFlyout`), sem regressão.
- [ ] Estado de "grupo aberto" (`openGroup`) é compartilhado entre os dois modos — só muda o que é renderizado (inline vs portal) conforme `collapsed`.
- [ ] Badges dinâmicos (Vendas/Estoque/Financeiro) continuam aparecendo corretamente tanto no header do grupo (accordion fechado) quanto nos dois modos de exibição dos filhos.
- [ ] Trocar de rota fecha o grupo aberto (accordion ou flyout), mesmo comportamento de hoje.
- [ ] Clique fora / Escape fecha o flyout no modo colapsado (comportamento de hoje preservado); no modo accordion inline, clicar em outro grupo fecha o anterior (só um aberto por vez, mesmo padrão de hoje).
