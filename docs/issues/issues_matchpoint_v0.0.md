# Issues — Sistema Matchpoint MVP

**Parent PRD:** `docs/prd_matchpoint_mvp.md`
**Documento mestre:** `docs/matchpoint_documentacao.md`
**Gerado em:** 2026-05-06

Cada issue abaixo é uma fatia vertical (schema → API → UI → testes). Quando `gh` CLI estiver disponível, criar nesta ordem para que números de bloqueio resolvam corretamente. Substituir `#PRD` pelo número da issue do PRD.

---

## Visão geral — grafo de dependências

```
1 Foundation
 ├─► 2 Auth/Login ──┐
 │                  ├─► 3 Cadastros base ──► 4 Itens + ficha técnica
 │                  │                          │
 │                  └─► 14 Config + backup     ▼
 │                                            5 Estoque & Compras
 │                                              │
 │                                              ▼
 │                                            6 Comandas (abrir + lançar + cancelar)
 │                                              │
 │                                              ▼
 │                                            7 Fechamento + divisão + pagamento misto
 │                                              │
 │                       ┌──────────────────────┼──────────────────────┐
 │                       ▼                      ▼                      ▼
 │              8 Comprovante + impressão  9 Reabertura     10 Relatórios operacionais
 │                                              ▼                      ▼
 │                                       11 Relatórios financeiros   12 Dashboard
 │
 └─► 13 UX sweep (crosscutting — finaliza após demais)
```

---

## Issue 1 — Foundation: skeleton repo + observabilidade + boot

**Type:** HITL (decisões arquiteturais iniciais)
**Blocked by:** None — pode começar imediatamente.

### What to build

Esqueleto inicial dos dois apps (frontend + backend) seguindo a arquitetura definida no PRD §Implementation Decisions. Backend FastAPI com Deep Models vazio mas funcional, frontend Vite/React com providers globais configurados, ambos rodando localmente. Sem feature de domínio — só plumbing.

### Acceptance criteria

- [ ] Backend roda local com `uvicorn` e responde `GET /health` retornando `{status, db, version}`.
- [ ] Estrutura de pastas Deep Models criada (`api/routes`, `services`, `repositories`, `models`, `schemas`, `core`).
- [ ] Pydantic `Settings` valida env vars no boot e falha cedo se algo faltar.
- [ ] Alembic inicializado, primeira migration vazia versionada.
- [ ] `CORSMiddleware` configurado com allowlist via env var.
- [ ] Exception handler global retorna formato padrão `{"error":{"code","message","field"}}`.
- [ ] `structlog` em JSON no stdout, com middleware de request_id por request.
- [ ] Sentry SDK inicializado (DSN via env, opcional em dev).
- [ ] Frontend roda local com `vite dev`, exibe tela placeholder.
- [ ] Estrutura `src/{pages,features,components,hooks,stores,schemas,lib}` criada.
- [ ] TanStack Query, Zustand, React Router, Axios (com interceptors), RHF+Zod, shadcn/ui (Button, Dialog, Input, Toast via sonner) instalados e configurados como providers globais.
- [ ] Helpers `lib/format.ts` com `formatCurrency` e `formatDate` ptBR.
- [ ] `.env.example` versionado nos dois apps.
- [ ] README curto com comandos de dev.

### User stories addressed

Foundation — não cobre stories diretamente, viabiliza todas as demais.

---

## Issue 2 — Auth: login único + JWT + sessão

**Type:** AFK
**Blocked by:** #1

### What to build

Fluxo completo de autenticação por senha única do estabelecimento. Backend gera JWT (12h), frontend persiste em localStorage e protege rotas. Tela de login conforme §8.1 do documento mestre.

### Acceptance criteria

- [ ] Schema: tabela com hash da senha única (bcrypt).
- [ ] Endpoint `POST /api/auth/login` recebe senha, retorna JWT ou 401 com código `SENHA_INCORRETA`.
- [ ] JWT expira em 12h, segredo via `JWT_SECRET`.
- [ ] Frontend: tela `/login` com RHF+Zod, toast vermelho em senha incorreta.
- [ ] `<RequireAuth>` wrapper redireciona para `/login` se sem token.
- [ ] Interceptor axios injeta `Authorization: Bearer` em toda request e trata 401 limpando storage + redirect.
- [ ] Layout pai (Topbar + Sidebar) envolve rotas autenticadas (sidebar apenas com placeholders por enquanto).
- [ ] Múltiplas sessões simultâneas funcionam (mesma senha, JWTs independentes).
- [ ] Testes: login OK, senha errada, token expirado rejeitado, rota protegida bloqueia sem token.

### User stories addressed

Stories 1, 2, 3, 4 do PRD.

---

## Issue 3 — Cadastros base (Categorias, Fornecedores, Garçons, Métodos de Pagamento)

**Type:** AFK
**Blocked by:** #2

### What to build

Quatro CRUDs simples para entidades secundárias usadas pelos demais módulos. Telas conforme §8.6.3–8.6.6. Inclui seed idempotente de métodos de pagamento e categoria default.

### Acceptance criteria

- [ ] Schemas: `categorias`, `fornecedores`, `garcons`, `metodos_pagamento`.
- [ ] Endpoints REST CRUD para cada entidade.
- [ ] Soft delete onde fizer sentido (garçom inativo, método desativado) — flag `ativo`.
- [ ] Telas frontend: lista + modal de cadastro/edição para cada entidade.
- [ ] Garçom: cadastro inclui flag `ativo`. Lista mostra inativos riscados ou agrupados.
- [ ] Seed: PIX, Crédito, Débito, Dinheiro pré-cadastrados; categoria "Geral" default. Idempotente.
- [ ] Garçom inativado não some de comandas existentes (preserva nome) — testar contrato (sem comanda ainda, mas API expõe `ativo`).
- [ ] Testes: CRUD básico, seed idempotente.

### User stories addressed

Stories 33, 42 do PRD.

---

## Issue 4 — Itens: simples, composto, ficha técnica, soft delete

**Type:** HITL (modelo central, validações de domínio)
**Blocked by:** #3

### What to build

Cadastro completo de itens conforme §6.2 e §8.6.1–8.6.2. Suporta tipo simples e composto, ficha técnica com cálculo de custo e CMV em tempo real, validações de domínio, soft delete.

### Acceptance criteria

- [ ] Schemas: `itens` (com `ativo`), `ficha_tecnica`, `componente_ficha`.
- [ ] `Item` tem `tipo` (simples/composto), `vendavel`, `unidade_base` (un/g), `quantidade_caixa`, `custo_medio`, `preco_venda`, `estoque_atual`.
- [ ] Endpoints: CRUD item, GET com filtros (categoria, tipo, vendável), endpoint para montar/editar ficha técnica.
- [ ] Validação: composto exige ≥1 insumo na ficha (código `FICHA_VAZIA`).
- [ ] Validação: item não-vendável não pode ter `preco_venda` (código `PRECO_EM_NAO_VENDAVEL`).
- [ ] Validação: ficha de composto não pode incluir outro composto (código `FICHA_ANINHADA_NAO_SUPORTADA`).
- [ ] Soft delete: item referenciado em ficha técnica não pode ser hard-deletado, vira `ativo=false`. Inativo some de buscas/atalhos.
- [ ] Cálculo do custo do composto: soma de (quantidade × custo_medio do insumo).
- [ ] FE: lista de itens com filtros (radio simples/composto, dropdown categoria, vendável); tela cadastro/edição com seção ficha técnica condicional, mostrando custo calculado e CMV percentual em tempo real.
- [ ] Testes: validações, cálculo de custo composto, soft delete preservando histórico.

### User stories addressed

Stories 39, 40, 41, 43 do PRD.

---

## Issue 5 — Estoque & Compras: saldo, baixa sem venda, histórico, custo médio ponderado

**Type:** AFK
**Blocked by:** #4

### What to build

Módulos de estoque e compras unificados nesta fatia (compartilham `movimento_estoque`). Telas conforme §8.4 e §8.5. Custo médio ponderado com regra de reset quando estoque ≤ 0.

### Acceptance criteria

- [ ] Schemas: `compras`, `itens_compra`, `movimento_estoque` (entrada/saida_venda/saida_perda com motivo, observação, custo_unitario, timestamp).
- [ ] Endpoint `POST /api/compras` cria compra: insere itens, gera movimento de entrada, recalcula `custo_medio` por média ponderada. Se `estoque_anterior <= 0`, custo médio é redefinido para o custo unitário da compra.
- [ ] Endpoint `GET /api/compras` com filtros de período e fornecedor.
- [ ] Cadastro inline de fornecedor a partir do form de compra.
- [ ] Endpoint `GET /api/estoque/saldo` com filtros (categoria, tipo, busca).
- [ ] Endpoint `POST /api/estoque/baixa-sem-venda` (motivo enum: consumo_interno/perda/quebra/cortesia/outro, observação livre, gera movimento `saida_perda`).
- [ ] Endpoint `GET /api/estoque/movimentos` paginado com filtros (período, item, tipo).
- [ ] FE: telas Lista de Compras, Nova Compra, Saldo Atual, Baixa Sem Venda (modal), Histórico de Movimentações.
- [ ] Saldo negativo permitido. Toast amarelo informa quando ocorre em baixa.
- [ ] Testes: custo médio em N compras sequenciais, reset com estoque ≤ 0, baixa sem venda gera movimento e atualiza saldo, histórico ordenado por timestamp desc.

### User stories addressed

Stories 31, 32, 33, 34, 35, 36, 37 do PRD.

---

## Issue 6 — Comandas: abrir, lançar, editar, cancelar item (núcleo operacional)

**Type:** HITL (núcleo do sistema, concorrência, auditoria)
**Blocked by:** #4

### What to build

Tela mais usada do sistema. Cobre §8.3.1 a §8.3.5 (sem fechamento ainda). Inclui controle otimista via coluna `version` e tabela de auditoria de eventos.

### Acceptance criteria

- [ ] Schemas: `comandas` (com coluna `version` int default 1 NOT NULL), `itens_comanda`, `eventos_comanda`.
- [ ] Endpoints: `POST /api/comandas` (abrir, valida garçom ativo + identificação), `GET /api/comandas?status=aberta`, `GET /api/comandas/{id}`, `POST /api/comandas/{id}/itens` (lançar com qtd, pessoa_associada, observação, cortesia → preço 0), `PATCH /api/comandas/{id}/itens/{item_id}` (editar qtd/pessoa/obs), `POST /api/comandas/{id}/itens/{item_id}/cancelar` (motivo enum + flag estornar_estoque).
- [ ] Endpoint `GET /api/itens/top?dias=7&limit=6` retorna itens vendáveis mais vendidos no período.
- [ ] UPDATE de comanda valida `WHERE id=? AND version=?`, incrementa version. Mismatch retorna 409 com código `COMANDA_DESATUALIZADA`.
- [ ] Cada mudança de estado grava registro em `eventos_comanda` (tipo, payload jsonb, garcom_id, timestamp).
- [ ] Snapshot de preço gravado em `itens_comanda.preco_unitario` no momento do lançamento.
- [ ] Cortesia → `cortesia=true` e `preco_unitario=0`.
- [ ] FE: lista de comandas abertas (busca por nome/mesa, card com identificação/garçom/qtd/total/tempo), modal Nova Comanda, tela Comanda Aberta (split com busca + atalhos top 7d + form de lançamento + painel de itens lançados), modal Cancelar Item (motivo + checkbox "Estornar ao estoque").
- [ ] Edição em comanda aberta não baixa estoque (baixa só no fechamento).
- [ ] Edição de pessoas em comanda aberta sempre permitida; não retroage em itens já associados.
- [ ] Frontend trata 409: toast vermelho "Comanda alterada por outro usuário, recarregue" + refetch automático.
- [ ] Atalhos visuais em grid 3×2 (suporte a 1280×720).
- [ ] Toda ação destrutiva (cancelar item) tem confirmação modal.
- [ ] Testes: snapshot de preço, cortesia, version conflict retorna 409, eventos gravados.

### User stories addressed

Stories 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 30, 56 do PRD.

---

## Issue 7 — Fechamento de comanda: desconto, divisão, pagamento misto, parcial, baixa de estoque

**Type:** HITL (operação crítica do sistema, atomicidade)
**Blocked by:** #5, #6

### What to build

Operação mais crítica do sistema (§8.3.6 + §10.3). Calcula total, aplica desconto, valida pagamentos mistos, suporta 4 modos de divisão, executa transação atômica de fechamento + baixa de estoque com explosão de ficha técnica para itens compostos.

### Acceptance criteria

- [ ] Schema: `pagamentos` (comanda_id, metodo, valor).
- [ ] Endpoint `POST /api/comandas/{id}/desconto` (percentual ou valor fixo).
- [ ] Endpoint `POST /api/comandas/{id}/fechar` recebe lista de pagamentos, modo de divisão, flag pagamento_parcial.
- [ ] Subtotal ignora itens cancelados e cortesias.
- [ ] Desconto aplicado ao subtotal antes da divisão.
- [ ] Pagamento parcial: validado < total, comanda mantém status `aberta` com saldo deduzido. Desconto fica pendente até fechamento total (parcial calcula sobre subtotal sem desconto).
- [ ] Fechamento total: valida soma de pagamentos = total (margem 0,01), bloqueia com código `PAGAMENTO_NAO_BATE`.
- [ ] Modo "valor diferente por pessoa" bloqueia se comanda tiver < 2 pessoas (código `PESSOAS_INSUFICIENTES`).
- [ ] Transação atômica: registra pagamentos, marca comanda fechada, baixa estoque dos itens não cancelados com explosão de ficha técnica em compostos.
- [ ] Saldo negativo permitido em qualquer item; toast amarelo no FE lista insumos negativos.
- [ ] Cortesia entra no CMV (custo do insumo é registrado) mas não em receita.
- [ ] FE: modal Aplicar Desconto, tela Fechamento (resumo, radio dos 4 modos de divisão, lista de linhas de pagamento com método+valor, validação visual).
- [ ] Confirmação modal antes de cortesia, desconto e fechamento.
- [ ] Testes: cálculo subtotal, aplicação de desconto, soma de pagamentos, parcial mantém aberta, divisão por pessoa, explosão de ficha em composto, atomicidade (falha em meio caminho não persiste nada).

### User stories addressed

Stories 19, 20, 21, 22, 23, 24, 25, 29, 38 do PRD.

---

## Issue 8 — Comprovante + impressão via navegador

**Type:** AFK
**Blocked by:** #7

### What to build

Tela de comprovante pós-fechamento (§8.3.7) com layout otimizado para impressão térmica via diálogo do navegador. Sem integração técnica com a impressora.

### Acceptance criteria

- [ ] Endpoint `GET /api/comandas/{id}/comprovante` retorna payload formatado.
- [ ] Schema mínimo: tabela `estabelecimento` (nome, CNPJ, endereço, telefone) — pode ser vazia, comprovante usa fallbacks.
- [ ] FE: tela `/comprovante/:id` com layout enxuto (largura ~80mm), CSS `@media print` esconde sidebar/topbar.
- [ ] Botão "Imprimir" aciona `window.print()`.
- [ ] Botão "Voltar às comandas" navega para lista.
- [ ] Texto "*** NÃO É CUPOM FISCAL ***" presente.
- [ ] Mostra itens, cortesia, desconto, total e quebra de pagamentos.
- [ ] Teste manual: impressão limpa em formato A4 e térmica 80mm.

### User stories addressed

Stories 26, 27 do PRD.

---

## Issue 9 — Reabertura de comanda + estorno de estoque

**Type:** AFK
**Blocked by:** #7

### What to build

Conforme §9.4 — botão de reabertura na tela de detalhes de comanda fechada (a partir do histórico). Estorna estoque com explosão de ficha, muda status para `reaberta`, registra evento.

### Acceptance criteria

- [ ] Endpoint `POST /api/comandas/{id}/reabrir` só aceita comandas com status `fechada`. Outras retornam 400 com código apropriado.
- [ ] Transação atômica: estorna estoque dos itens não-cancelados (explode ficha em compostos, registra movimentos negativos de venda), muda status para `reaberta`, registra evento.
- [ ] FE: botão "Reabrir" em tela de detalhes da comanda fechada com confirmação modal explicando impacto.
- [ ] Após reabrir, comanda volta ao fluxo de lançamento normal e pode ser fechada de novo.
- [ ] Histórico marca como "reaberta" e o evento fica no `eventos_comanda`.
- [ ] Testes: estorno correto em simples e composto, comanda parcial não pode ser reaberta (já está aberta), comanda nunca fechada não pode ser reaberta.

### User stories addressed

Story 28 do PRD.

---

## Issue 10 — Relatórios operacionais: Vendas do dia, Histórico, Fechamento de caixa, export PDF

**Type:** AFK
**Blocked by:** #7

### What to build

Três relatórios operacionais (§8.7.1–8.7.3) com filtros e exportação. Timezone correto via `America/Sao_Paulo`.

### Acceptance criteria

- [ ] Endpoint `GET /api/relatorios/vendas-do-dia` retorna comandas fechadas no dia atual (timezone local).
- [ ] Endpoint `GET /api/relatorios/historico-comandas` com filtros (período, garçom, busca por nome/mesa).
- [ ] Endpoint `GET /api/relatorios/fechamento-caixa?data=` retorna total bruto, descontos, cortesias, líquido e quebra por método de pagamento.
- [ ] FE: 3 telas com filtros no topo + tabela/cards.
- [ ] Botão "Exportar PDF" no Fechamento de Caixa gera PDF (jsPDF ou print CSS).
- [ ] Conversão de timezone correta nas queries (range UTC corresponde ao dia local).
- [ ] Testes: agregação de pagamentos por método, filtros de período, comanda em pagamento parcial não conta como fechada.

### User stories addressed

Stories 44, 45, 46, 52 do PRD.

---

## Issue 11 — Relatórios financeiros: DRE, CMV por produto, Perdas/Cortesias, Vendas por garçom

**Type:** AFK
**Blocked by:** #7

### What to build

Quatro relatórios gerenciais (§8.7.4–8.7.7) com regras de negócio específicas.

### Acceptance criteria

- [ ] Endpoint `GET /api/relatorios/dre?mes=` calcula receita bruta, descontos+cortesias, faturamento líquido, CMV, perdas, lucro bruto, margem%.
- [ ] DRE retorna alerta no payload listando produtos sem custo cadastrado quando houver.
- [ ] Endpoint `GET /api/relatorios/cmv-por-produto` lista vendáveis com preço, custo, margem (R$ e %), classificação (verde >40% margem, amarelo 20–40%, vermelho <20%).
- [ ] Endpoint `GET /api/relatorios/perdas-cortesias?periodo=` agrupa por motivo com totais.
- [ ] Endpoint `GET /api/relatorios/vendas-por-garcom?periodo=` retorna ranking por garçom da abertura, com faturamento, qtd comandas, ticket médio.
- [ ] FE: 4 telas com filtros + tabela/gráfico.
- [ ] DRE renderiza alerta amarelo no topo quando houver produtos sem custo.
- [ ] Cortesia entra no CMV mas não em receita.
- [ ] Testes: DRE com produto sem custo gera alerta, vendas por garçom respeita garçom da abertura, classificação CMV correta nas faixas.

### User stories addressed

Stories 47, 48, 49, 50, 51 do PRD.

---

## Issue 12 — Dashboard: indicadores, gráficos, comandas abertas

**Type:** AFK
**Blocked by:** #7

### What to build

Tela inicial pós-login (§8.2). Cards de indicadores, 4 gráficos e lista de comandas abertas com atalho.

### Acceptance criteria

- [ ] Endpoint `GET /api/dashboard` retorna em uma única chamada: faturamento, ticket médio, comandas (abertas/fechadas), lucro estimado, faturamento por hora (24 buckets), top 10 produtos (qtd e R$), 30 dias (linha), heatmap do mês (dia → R$).
- [ ] Lucro estimado = faturamento líquido − CMV (best-effort, ignora produtos sem custo).
- [ ] FE: tela `/` com 4 cards no topo, 4 gráficos via biblioteca de charts (Recharts), lista de comandas abertas com clique → tela de lançamento.
- [ ] Heatmap mostra dias do mês colorindo intensidade de faturamento.
- [ ] Loading com skeleton; refetch automático a cada 60s via TanStack Query.
- [ ] Renderiza limpo em 1280×720 (cards podem quebrar em 2 linhas).
- [ ] Testes: agregações estão corretas, fuso horário não afeta bucket de hora.

### User stories addressed

Stories 5, 6, 7, 8, 9 do PRD.

---

## Issue 13 — Configurações: estabelecimento, senha, backup/exportação

**Type:** AFK
**Blocked by:** #2

### What to build

Telas de configuração (§8.8). Inclui exportação completa de dados em JSON e Excel sob demanda.

### Acceptance criteria

- [ ] Schema: `estabelecimento` com nome, CNPJ, endereço, telefone (linha única).
- [ ] Endpoints `GET /api/config/estabelecimento` e `PATCH /api/config/estabelecimento`.
- [ ] Endpoint `PATCH /api/config/senha` valida senha atual, atualiza hash.
- [ ] Endpoint `GET /api/backup?formato=json|xlsx` autenticado retorna dump:
  - JSON: dump de todas as tabelas.
  - XLSX: 3 planilhas (comandas, itens, movimento_estoque).
- [ ] FE: 3 telas (Dados do Estabelecimento, Senha, Backup com 2 botões de download).
- [ ] Tela Impressora: estática, instruções textuais para configurar a térmica no SO.
- [ ] Testes: alteração de senha invalida JWTs antigos? (No MVP não — sem revogação. Documentar contrato.)

### User stories addressed

Stories 53, 54, 55 do PRD.

---

## Issue 14 — UX sweep: confirmações, toasts, Sentry, QA visual em 1280×720

**Type:** HITL (revisão visual e UX)
**Blocked by:** #1 (mas finaliza após as demais — crosscutting)

### What to build

Fatia transversal aplicada continuamente durante as demais e finalizada como sweep antes da entrega. Garante consistência de feedback, captura automática de erros em produção e QA visual em resolução baixa.

### Acceptance criteria

- [ ] Componente `ConfirmDialog` reutilizável com título, descrição, botão destrutivo, usado em todas as ações destrutivas (cancelar item, reabrir comanda, excluir cadastro, aplicar cortesia, aplicar desconto, baixa sem venda).
- [ ] Sonner configurado globalmente com 3 variantes (verde 2-3s / vermelho persistente / amarelo 4-5s) conforme §5.3.2.
- [ ] Sentry FE captura erros de render, rejeições de promessa e respostas 500. Sentry BE captura exceptions.
- [ ] Smoke test visual em 1280×720 e 1366×768 documentado em checklist (todas as telas principais sem clipping, sem scroll horizontal).
- [ ] Densidade reduzida confirmada: padding `p-3`, botões `h-10`, atalhos 3×2.
- [ ] Sidebar colapsa por padrão em viewport ≤1366px.
- [ ] Toda tabela/lista tem skeleton de loading e empty state.
- [ ] Tempo de resposta <2s por operação confirmado (medir no Sentry/structlog).
- [ ] Manual de operação curto produzido (1 página, fluxo abrir→fechar comanda).

### User stories addressed

Stories 56, 57, 58, 59 do PRD.

---

## Resumo de criação via gh (quando disponível)

Comando-base, repetir para cada issue na ordem (substitua `<PRD_NUM>` pelo número da issue do PRD após criá-la primeiro com `gh issue create --title "PRD: Sistema Matchpoint MVP" --body-file docs/prd_matchpoint_mvp.md`):

```bash
gh issue create \
  --title "Issue N — <título>" \
  --body-file <arquivo recortado deste md> \
  --label "mvp,matchpoint"
```

Editar cada body para substituir `#PRD` pelo número real e `#<N>` pelos números reais retornados pelo gh à medida que forem criados.
