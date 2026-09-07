# 08: Handle de colapso + tratamento do rail (Empresa/busca/rodapé icon-only)

**What to build:** O botão de colapsar/expandir a sidebar (hoje uma barra ocupando uma linha inteira no topo) vira um handle pequeno e circular grudado na borda direita da sidebar, sempre visível (só em desktop), trocando de ícone/direção conforme o estado. Ao colapsar (rail de ícones), o bloco Empresa encolhe pra só a letra, o campo de busca desaparece (preservando o texto digitado em memória) e o rodapé (Configurações/Sair) vira icon-only, igual ao resto do rail.

**Blocked by:** 03, 05, 06

**Touches:** `frontend/src/components/layout/Sidebar.tsx`

**Nature:** subjective

- [ ] Botão de linha inteira no topo (`hidden ... lg:flex` com ícone `Menu`) removido; novo handle circular na borda direita, posição vertical central, visível só em desktop.
- [ ] Ícone do handle troca de direção conforme `collapsed` (aberto→fecha, fechado→abre).
- [ ] `localStorage` (`sidebar_collapsed`) e prop `onToggle`/`collapsed` de `AppLayout.tsx` inalterados — só muda o elemento que dispara `onToggle()`.
- [ ] Mobile inalterado: hambúrguer do `Topbar.tsx` (`onMenuClick`) continua controlando o overlay deslizante, sem relação com o handle novo.
- [ ] Colapsado: bloco Empresa mostra só o quadrado com a letra (nome/subtítulo escondidos, sem cortar ou quebrar layout).
- [ ] Colapsado: campo de busca desaparece inteiramente; texto digitado antes de colapsar é preservado em memória e reaparece ao expandir de novo (filtro não reseta).
- [ ] Colapsado: "Configurações" e "Sair" no rodapé viram icon-only (mesmo padrão dos demais itens do rail), com `title` de tooltip nativo.
