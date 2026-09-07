# 03: Toggle de ordenação com rótulo de estado

**What to build:** O botão de ordenação do Cardápio troca de texto conforme o estado atual — "A→Z" quando a lista está na ordem de cadastro (convite pra ativar), "Z→A" quando está ordenada alfabeticamente (mostra a ação que desfaz, clicar volta à ordem de cadastro) — em vez de só mudar cor de fundo, que hoje é ambíguo sobre qual estado está ativo.

**Blocked by:** None (can start immediately)

**Touches:** `frontend/src/features/cardapio/CardapioPage.tsx`

**Nature:** objective

**Status:** ready-for-agent

- [x] Estado inicial (ordem de cadastro, `ordenacao === "original"`) mostra o texto "A→Z"
- [x] Após clicar (ordem alfabética, `ordenacao === "az"`) o texto muda para "Z→A"
- [x] Clicar novamente volta ao texto "A→Z" e à ordem de cadastro
- [x] Sem ícone adicional — só o texto muda
- [x] Comportamento de ordenação em si (os dois estados existentes) não muda, só a legenda do botão
