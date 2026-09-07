# 08: Widget "Estoque — Atenção" (críticos + menor estoque)

**What to build:** Novo card no Dashboard usando `DashboardCard`, com duas seções: (a) insumos críticos, reusando os mesmos itens de `insumos_criticos` que já alimentam o banner de alerta — extrair subcomponente `InsumoCriticoRow` reusável entre banner e card, não duplicar UI de lista; (b) "Menor estoque" (exatamente 5 itens vindos prontos do backend, já excluindo críticos), lista simples nome + `estoque_disponivel` + `unidade_base`, sem badge de cor/rótulo de severidade.

**Blocked by:** 02 (campo `insumos_menor_estoque` no backend), 03 (`DashboardCard`)

**Touches:** `frontend/src/features/dashboard/DashboardPage.tsx`, `frontend/src/features/dashboard/components/InsumoCriticoRow.tsx` (novo, extraído do banner de alerta existente)

**Nature:** mixed

**Status:** ready-for-agent

- [ ] Card "Estoque — Atenção" posicionado após "Cortesias/Perdas do Mês" e antes de "Ontem/Esta Semana/Este Mês" (ordem da spec: item 11 de 16)
- [ ] Usa `DashboardCard` (título, "?", skeleton)
- [ ] `helpText`: explica que a seção "Críticos" mostra insumos abaixo do nível configurado e "Menor estoque" é um ranking cru (sem threshold) dos insumos com menos saldo disponível
- [ ] Subcomponente `InsumoCriticoRow` extraído do banner de alerta existente (que já lista `insumos_criticos`) e reusado tanto no banner quanto neste card — não duplicar markup
- [ ] Seção "Menor estoque": exatamente os itens de `insumos_menor_estoque` (backend já garante 5 e exclusão de críticos), lista simples nome + `estoque_disponivel` + `unidade_base`, **sem** badge de cor/rótulo "baixo"/"alto" (decisão explícita: ranking cru, sem threshold inventado)
- [ ] Loading state usa skeleton do `DashboardCard`
- [ ] Ambas as listas vazias (nenhum crítico, nenhum insumo cadastrado) mostram estado vazio razoável, sem quebrar
- [ ] Banner de alerta existente continua funcionando sem regressão após a extração de `InsumoCriticoRow`
