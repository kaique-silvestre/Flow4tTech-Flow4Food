# PRP — Issue #8: M006 — Fechamento pré-preenchido

**Parent PRD:** `docs/prds/prd_matchpoint_v0.1.md`
**Parent Issue:** `docs/issues/issues_matchpoint_v0.1.md` → Issue 8
**Type:** AFK
**Status:** Em execução
**Criado em:** 2026-05-08
**Depende de:** Nenhum

---

## Objetivo

`FechamentoPage` inicializa com `modo_divisao: 'sem_divisao'` e primeiro pagamento com `valor = baseTotal` ao montar. Trocar modo de divisão reseta o campo adequadamente. Zero mudança no backend.

---

## Estrutura de Arquivos a Modificar

```
frontend/
  src/
    features/
      comandas/
        FechamentoPage.tsx   # (modificar) useEffect para pré-preencher + onChange de modo
```

---

## Tarefas

### Bloco A — FechamentoPage: pré-preencher valor

- [ ] **A1.** Adicionar `useEffect` que dispara quando `comanda` carrega:
  ```tsx
  useEffect(() => {
    if (comanda) {
      const sub = comanda.total_parcial;
      const desc = comanda.desconto_percentual
        ? sub * (comanda.desconto_percentual / 100)
        : (comanda.desconto_valor ?? 0);
      const base = comanda.saldo_pendente ?? (sub - desc);
      setValue("pagamentos.0.valor", Number(base.toFixed(2)));
    }
  }, [comanda?.id]);
  ```
  Usar `comanda?.id` como dep para disparar exatamente uma vez por comanda carregada.

- [ ] **A2.** No onChange de cada opção de modo, ao trocar para `sem_divisao`: preencher `pagamentos.0.valor = baseTotal`. Para qualquer outro modo: limpar `pagamentos.0.valor` para `0`.

  Modificar o loop de `modoOpcoes.map`:
  ```tsx
  onChange={() => {
    setValue("modo_divisao", opt.value);
    if (opt.value === "sem_divisao") {
      setValue("pagamentos.0.valor", Number(baseTotal.toFixed(2)));
    } else {
      setValue("pagamentos.0.valor", 0);
    }
  }}
  ```

---

## Validações

```bash
cd frontend
npm run type-check
npm run lint
npm run build
```

---

## Critérios de Aceite

- [ ] `FechamentoPage` abre com "Sem divisão" já selecionado (já existia)
- [ ] Campo de valor já preenchido com total da comanda ao abrir
- [ ] Trocar modo para outro limpa o campo de valor (seta 0)
- [ ] Trocar de volta para "Sem divisão" preenche novamente com total da comanda
- [ ] type-check PASS, lint PASS, build PASS

---

## Notas

- `baseTotal` calculado fora do useEffect e passado como argumento não funciona pois `comanda` é async. Calcular dentro do effect.
- `pagamentos.0.valor` é o único campo pré-preenchido — se o operador adicionar mais linhas de pagamento, essas linhas iniciam com valor 0.
- O form já inicializa `modo_divisao: "sem_divisao"` — sem alteração necessária nesse ponto.
