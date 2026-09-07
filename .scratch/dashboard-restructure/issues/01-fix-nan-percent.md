# 01: Corrigir NaN% em CMV Hoje e comparativo mensal

**What to build:** No `DashboardPage.tsx`, o card "CMV Hoje" exibe "—" em vez de "NaN%" quando `faturamento_hoje === 0`. A função utilitária `variacao()` (usada por todos os badges de comparação, ex. "Este mês") retorna `null` corretamente quando `atual === 0 && anterior === 0`, não só quando `anterior === 0`.

**Blocked by:** None (can start immediately)

**Touches:** `frontend/src/features/dashboard/DashboardPage.tsx` (ou onde `variacao()`/cálculo de `cmvPct` estiverem localizados)

**Nature:** objective

**Status:** ready-for-agent

- [x] `cmvPct` só é calculado quando `faturamento_hoje > 0`; caso contrário exibe "—"
- [x] `variacao()` retorna `null` quando `atual === 0 && anterior === 0` (hoje só trata `anterior === 0`)
- [x] Card "Este mês" não mostra mais "↓NaN% vs mês passado" quando ambos os meses estão zerados
- [x] Nenhum outro cálculo de percentual/badge de variação no dashboard quebra com faturamento zerado
- [x] Guard é feito no front — backend continua mandando os valores brutos sem alteração
- [x] Comportamento com dados normais (faturamento > 0) permanece idêntico
