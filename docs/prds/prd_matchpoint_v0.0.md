# PRD — Sistema Matchpoint (MVP)

**Versão:** 1.0
**Data:** 2026-05-06
**Status:** Aprovado para desenvolvimento
**Documento base:** `docs/matchpoint_documentacao.md`

---

## Problem Statement

Sócios da Estação Matchpoint operam o bar com controle manual em papel/planilha. Em dias de jogo, o caixa trava: comandas se acumulam, divisão de conta vira disputa, perdas de estoque não são rastreadas, e fechamento do dia leva horas para ser conferido. Não há visibilidade de margem por produto (CMV), nem controle de cortesias, descontos e baixas sem venda. Soluções de mercado (PDVs tradicionais) são caras, complexas para "gente mais velha" operar e não cabem no orçamento do estabelecimento (~R$100/mês).

Os sócios precisam de um sistema simples, rápido, operável por qualquer pessoa do balcão, que cubra o fluxo completo: abrir comanda, lançar item, fechar com pagamento misto e divisão, baixar estoque automaticamente, e gerar relatórios financeiros básicos (DRE, CMV, fechamento de caixa).

## Solution

Sistema web Matchpoint — um SaaS interno multi-módulo acessado via navegador no PC do bar, com login único do estabelecimento. Frontend React rodando local (entregue via Vercel quando integração de hospedagem for ativada) e backend FastAPI + PostgreSQL com arquitetura Deep Models (Controllers → Services → Repositories → Models).

O MVP entrega o núcleo operacional (Comandas + Estoque + Compras) e o núcleo gerencial (Dashboard + Relatórios + Cadastros), com UI deliberadamente simples: botões grandes, atalhos visuais para os 6 produtos mais vendidos, confirmação modal em ações destrutivas, toasts de feedback. Suporta resolução mínima 1280×720 (HD).

A entrega é seguida de um mês de teste gratuito (12/05 → 12/06/2026) com rodadas semanais de ajuste às terças 16h00. Hospedagem em Railway (backend + DB) + Vercel (frontend) **será configurada como etapa de deploy — ainda não há integração ativa**. Custo total estimado pós-deploy: ~R$35-40/mês.

---

## User Stories

### Autenticação

1. Como sócio, quero entrar no sistema com uma senha única do estabelecimento, para que eu não precise gerenciar usuários no MVP.
2. Como operador, quero que minha sessão expire em 12 horas, para que esquecer de deslogar não vire risco de segurança.
3. Como operador, quero ser redirecionado automaticamente para a tela de login quando minha sessão expirar, para que eu saiba que preciso autenticar de novo.
4. Como sócio, quero abrir o sistema em mais de um PC simultaneamente com a mesma senha, para que caixa e balcão operem em paralelo.

### Dashboard

5. Como sócio, quero ver o faturamento, ticket médio, número de comandas e lucro estimado do dia, para que eu tenha leitura imediata da operação.
6. Como sócio, quero ver gráfico de faturamento por hora do dia, para que eu identifique horários de pico.
7. Como sócio, quero ver os top 10 produtos mais vendidos, para que eu priorize estoque e atalhos.
8. Como sócio, quero ver o faturamento dos últimos 30 dias e um heatmap mensal, para que eu compare desempenho ao longo do tempo.
9. Como sócio, quero ver a lista de comandas abertas no dashboard com atalho para abrir cada uma, para que eu acesse o operacional em 1 clique.

### Comandas — Operação Núcleo

10. Como garçom, quero abrir uma comanda identificada por nome do cliente ou número de mesa, para que eu cubra o fluxo de bar (mesa) e o de festa (nome).
11. Como garçom, quero vincular um garçom responsável obrigatório à comanda na abertura, para que o relatório de vendas por garçom funcione.
12. Como garçom, quero adicionar nomes de pessoas que vão consumir na mesma comanda, para que eu associe itens individuais e divida a conta depois.
13. Como garçom, quero buscar produtos por nome com autocomplete, para que eu encontre item rápido em cardápio grande.
14. Como garçom, quero atalhos visuais para os 6 produtos mais vendidos dos últimos 7 dias, para que lançamentos comuns sejam imediatos.
15. Como garçom, quero lançar item com quantidade, pessoa associada (opcional), observação (texto livre) e flag de cortesia, para que o lançamento cubra os casos reais do bar.
16. Como garçom, quero editar um item já lançado em comanda aberta, para que eu corrija erro sem precisar cancelar e relançar.
17. Como garçom, quero cancelar um item da comanda informando motivo (cliente desistiu, erro, indisponível, outro), para que o relatório de cancelamentos seja útil.
18. Como garçom, ao cancelar item, quero escolher se o item volta ao estoque (não foi preparado) ou não, para que perda real seja diferenciada de erro de lançamento.
19. Como sócio, quero aplicar desconto na comanda (em % ou valor fixo), para que eu fidelize cliente em casos pontuais.
20. Como sócio, quero aplicar cortesia em item específico (preço zero), para que cortesia individual fique registrada no relatório sem afetar a comanda toda.
21. Como caixa, quero fechar a comanda calculando subtotal, desconto e total, para que o pagamento seja preciso.
22. Como caixa, quero dividir a conta em 4 modos: sem divisão / igual entre N / valor diferente por pessoa / pagamento parcial, para que eu cubra todos os cenários comuns do bar.
23. Como caixa, quero registrar pagamento misto (PIX + Crédito + Dinheiro na mesma comanda), para que cliente pague como preferir.
24. Como caixa, quero que o sistema bloqueie o fechamento se a soma dos pagamentos não bater com o total, para que erro de digitação não passe.
25. Como caixa, em pagamento parcial, quero que a comanda volte ao estado "aberta" com saldo restante, para que o cliente continue consumindo e pague o resto depois.
26. Como caixa, quero gerar comprovante não-fiscal após o fechamento, para que o cliente leve registro do consumo.
27. Como caixa, quero imprimir o comprovante via diálogo do navegador, para que eu use a impressora térmica configurada no SO.
28. Como sócio, quero reabrir uma comanda fechada por engano, com estorno automático do estoque, para que correção pós-fechamento não desconfigure o saldo.
29. Como sócio, quero ser avisado por toast amarelo se o estoque ficar negativo no fechamento, para que eu saiba que preciso ajustar manualmente.
30. Como caixa, quero que se outro operador alterar a mesma comanda enquanto eu estou nela, o sistema me avise para recarregar antes de salvar, para que alterações simultâneas não se sobrescrevam silenciosamente.

### Compras

31. Como sócio, quero registrar uma compra manual selecionando fornecedor, data, número da nota (opcional) e itens com quantidade e custo, para que o estoque entre e o custo médio seja recalculado.
32. Como sócio, quero ver o histórico de compras filtrado por período e fornecedor, para que eu controle gasto com insumos.
33. Como sócio, quero cadastrar fornecedor novo direto no formulário de compra, para que eu não precise sair do fluxo.

### Estoque

34. Como sócio, quero ver o saldo atual de cada item com categoria, quantidade e custo médio, para que eu acompanhe estoque a qualquer momento.
35. Como sócio, quero filtrar estoque por categoria e tipo (simples/composto) e buscar por nome, para que eu encontre item rápido.
36. Como sócio, quero registrar baixa sem venda informando item, quantidade, motivo (consumo interno, perda, quebra, cortesia, outro) e observação, para que perdas fiquem rastreadas.
37. Como sócio, quero ver o histórico completo de movimentações de estoque (entradas, saídas de venda, baixas sem venda), para que eu audite qualquer divergência.
38. Como sistema, ao fechar comanda, quero dar baixa automática no estoque explodindo a ficha técnica de itens compostos, para que vender 1 X-Burguer baixe pão + carne + queijo proporcionalmente.

### Cadastros

39. Como sócio, quero cadastrar item com nome, categoria, tipo (simples/composto), flag vendável, unidade base (un/g) e quantidade por caixa, para que o catálogo cubra insumos puros e produtos vendáveis.
40. Como sócio, quero montar a ficha técnica de um item composto adicionando insumos com quantidade e unidade, para que o custo seja calculado e o estoque baixe corretamente.
41. Como sócio, quero ver o custo calculado e o CMV percentual do item composto em tempo real ao montar a ficha, para que eu precifique com base na margem.
42. Como sócio, quero CRUD de categorias, fornecedores, garçons e métodos de pagamento, para que o sistema reflita meu negócio.
43. Como sistema, quero impedir exclusão hard de item referenciado em ficha técnica ou histórico de comanda, e usar soft delete (campo `ativo=false`), para que histórico não quebre.

### Relatórios

44. Como sócio, quero ver vendas do dia detalhadas por comanda fechada, para que eu confira o operacional.
45. Como sócio, quero ver histórico de comandas com filtro de período (semana, mês, custom) e busca por nome/garçom/mesa, para que eu audite qualquer venda.
46. Como sócio, quero ver fechamento de caixa com total bruto, descontos, cortesias, líquido e quebra por método de pagamento, para que eu confira o caixa do dia.
47. Como sócio, quero ver DRE simplificado mensal com receita, custos, lucro bruto e margem, para que eu tenha leitura financeira do mês.
48. Como sócio, quero ser avisado no DRE se houver produtos sem custo cadastrado, para que eu saiba que o CMV pode estar subestimado.
49. Como sócio, quero ver CMV por produto com classificação verde/amarelo/vermelho, para que eu identifique produtos com margem ruim.
50. Como sócio, quero ver perdas e cortesias agrupadas por motivo, para que eu identifique padrões.
51. Como sócio, quero ver vendas por garçom (faturamento, comandas, ticket médio), para que eu avalie performance.
52. Como sócio, quero exportar fechamento de caixa em PDF, para que eu arquive ou envie para contador.

### Configurações

53. Como sócio, quero cadastrar dados do estabelecimento (nome, CNPJ, endereço, telefone), para que apareçam no comprovante.
54. Como sócio, quero alterar a senha única do sistema, para que eu rotacione segurança.
55. Como sócio, quero exportar todos os dados em JSON e Excel, para que eu tenha backup manual sob demanda.

### Qualidade Geral

56. Como operador, quero confirmação modal em toda ação destrutiva (cancelar item, reabrir comanda, excluir cadastro, aplicar cortesia/desconto), para que eu não cometa erro irreversível por engano.
57. Como operador, quero feedback toast (verde/vermelho/amarelo) consistente em todas as operações, para que eu saiba se ação deu certo.
58. Como operador, quero que o sistema funcione fluído em resolução 1280×720, para que eu use em PCs antigos do bar.
59. Como sócio, quero que erros não-tratados sejam reportados automaticamente para o time dev (Sentry), para que bugs em produção sejam corrigidos sem eu precisar abrir chamado.

---

## Implementation Decisions

### Arquitetura Geral

- **Padrão Deep Models** no backend: Controllers (rotas FastAPI) → Services (lógica de negócio) → Repositories (acesso a dados) → Models (SQLAlchemy) + DTOs (Pydantic).
- **Stack backend:** Python 3.11+, FastAPI, SQLAlchemy 2.0, Pydantic v2, Alembic, Uvicorn.
- **Stack frontend:** React 18 + Vite 5 + TailwindCSS 3 + React Router v6 + Axios + **TanStack Query** (server state/cache) + **Zustand** (estado UI global) + **React Hook Form + Zod** (forms + validação espelhando schemas Pydantic) + **shadcn/ui** (componentes copy-paste sobre Tailwind) + **sonner** (toasts).
- **Banco:** PostgreSQL 15 com transações ACID.
- **Hospedagem:** Vercel (frontend) + Railway (backend + DB) — **sem integração ativa no momento**, será configurada na etapa de deploy. Desenvolvimento e testes locais até então.

### Frontend — Estrutura e Padrões

- Estrutura por feature: `src/{pages, features/{comandas, estoque, compras, ...}, components, lib, hooks, stores, schemas}`.
- Componentes UI base via shadcn/ui: Button, Modal/Dialog, Input, Select, Combobox, Table, Card, Skeleton.
- Toast: sonner, com 3 variantes (sucesso 2-3s verde, erro permanente vermelho, aviso 4-5s amarelo) conforme doc.
- Roteamento: wrapper `<RequireAuth>` checa JWT em localStorage; layout pai (Topbar + Sidebar) envolve rotas autenticadas.
- Formatação: `Intl.NumberFormat('pt-BR', {currency:'BRL'})` e `date-fns` com locale `ptBR`. Helpers centralizados em `lib/format.ts`.
- Empty states e Skeleton em toda tabela/lista carregada de API.
- Resolução alvo: design base mobile-friendly via Tailwind `md:` (768px+), split de painéis ativa em `lg:` (1024px+). **Mínimo suportado: 1280×720**. Densidade reduzida (padding `p-3`, botões `h-10` mínimo 40px). Atalhos de produtos em grid 3×2 em vez de 6×1. Não suportar viewport <1280px no MVP.

### Autenticação

- Senha única do estabelecimento, validada via endpoint de login. Backend gera JWT.
- JWT armazenado em `localStorage`, expiração 12h, sem refresh token no MVP.
- 401 do backend → frontend limpa storage, redireciona para `/login`, mostra toast.
- Múltiplas sessões simultâneas permitidas (caixa + balcão), sem revogação.

### Concorrência

- Coluna `version` (int, default 1) em `comandas`. Cada UPDATE incrementa.
- UPDATE valida `WHERE id=? AND version=?`. Mismatch → backend retorna 409 com código `COMANDA_DESATUALIZADA`.
- Frontend exibe toast vermelho "Comanda alterada por outro usuário, recarregue" e refaz o GET.

### Timezone

- Storage em UTC. Conversão para `America/Sao_Paulo` na borda da aplicação.
- Variável de ambiente `TZ=America/Sao_Paulo`.
- Relatórios "do dia" usam range em horário local convertido para UTC na query.

### Erros — Padrão de API

- Exception handler global FastAPI retorna JSON consistente:
  ```json
  {"error": {"code": "COMANDA_FECHADA", "message": "Comanda já fechada", "field": null}}
  ```
- Códigos enumerados no backend (constantes). Frontend faz match para mensagem amigável e destacar campo do form (se `field` preenchido).

### Migrations e Seeds

- Alembic para versionamento de schema. Cada mudança gera revision.
- Comando `alembic upgrade head` rodado como etapa pré-deploy (será configurado quando integração com Railway for ativada). Em desenvolvimento, dev roda manual.
- Script `src/seeds.py` idempotente popula dados iniciais obrigatórios: métodos de pagamento (PIX, Crédito, Débito, Dinheiro) e categoria default. Roda 1x ao subir ambiente.

### Logging e Observabilidade

- `structlog` no backend, logs em JSON com campos estruturados (event, request_id, latência, IDs de domínio).
- Logs de operações críticas: abertura/fechamento de comanda, baixa de estoque, exceptions com stacktrace.
- **Sentry** (free tier) configurado em frontend (`@sentry/react`) e backend (`sentry-sdk[fastapi]`). DSN via env var. Captura automática de exceptions com contexto (browser, request, user).

### Variáveis de Ambiente

- `.env.example` versionado.
- Vars: `DATABASE_URL`, `JWT_SECRET`, `JWT_EXPIRES_HOURS=12`, `TZ=America/Sao_Paulo`, `CORS_ORIGINS`, `ENV` (`dev`/`prod`), `SENTRY_DSN_BACKEND`, `SENTRY_DSN_FRONTEND`.
- Pydantic `Settings` valida no boot — falha cedo se var faltar.

### CORS

- `CORSMiddleware` FastAPI com allowlist (URL produção do frontend + `http://localhost:5173`). Sem `*`.

### Health Check

- `GET /health` retorna `{status:"ok", db:"ok", version:"x.y.z"}` testando conexão DB.

### Backup e Exportação

- Endpoint `GET /api/backup` autenticado, gera on-demand:
  - JSON dump completo de todas as tabelas.
  - Excel (.xlsx) com 3 planilhas: comandas, itens, movimento_estoque.
- Operação manual sob demanda no MVP.

### Lógica de Negócio — Decisões Pontuais

- **Cortesia e CMV:** cortesia entra no CMV (custo dos insumos consumidos é registrado), mas não em receita. Aparece em "Perdas e Cortesias" e como dedução no DRE.
- **Desconto + pagamento parcial:** desconto fica pendente até o fechamento total. Pagamento parcial é calculado sobre o subtotal sem desconto. Documentar isso no fluxo.
- **Edição de item em comanda aberta:** estoque só é baixado no fechamento. Edição de quantidade/pessoa/observação enquanto comanda aberta é livre, sem efeito no estoque.
- **Item composto sem estoque suficiente:** mesma regra do simples — explode ficha técnica, baixa cada insumo, permite saldo negativo, toast amarelo lista insumos negativos.
- **Custo médio com estoque ≤ 0:** se `estoque_anterior <= 0`, custo médio é redefinido para o custo unitário da nova compra (reseta), em vez de aplicar média ponderada.
- **Divisão "valor diferente por pessoa":** bloqueada se a comanda tiver menos de 2 pessoas cadastradas. Toast orienta cadastro.
- **Numeração de comandas:** MVP exibe `#001` formatando o `id` PK com zero-pad no frontend. Sequencial real fica para pós-MVP.
- **Soft delete de itens:** item referenciado (em ficha técnica ou histórico) só pode ser desativado (`ativo=false`), nunca removido fisicamente. Item inativo some de buscas e atalhos, mas histórico mantém referência.
- **Garçom inativado mid-comanda:** comanda continua válida; relatórios mantêm o nome no snapshot.
- **Item excluído com comanda aberta referenciando:** snapshot do preço já está no `ItemComanda`. Item some das opções de novo lançamento, mas comanda existente permanece intacta.
- **Vendas por garçom:** garçom vinculado na abertura é o responsável para todos os relatórios. Trocar fechador não muda a atribuição.
- **DRE com produto sem custo:** mostra alerta no topo "X produtos sem custo cadastrado, CMV pode estar subestimado. [Ver lista]". Não bloqueia geração.
- **Edição de pessoas em comanda aberta:** sempre editável; não retroage em itens já associados (snapshot mantido em `pessoa_associada`).

### Schema — Adições ao Modelo Atual

- `comandas.version` (int, default 1, NOT NULL) — controle otimista de concorrência.
- `itens.ativo` (boolean, default true) — soft delete.
- `eventos_comanda` (tabela nova) — auditoria: `id, comanda_id, tipo (enum: aberta/item_lancado/item_cancelado/descontada/fechada/reaberta), payload_jsonb, garcom_id, timestamp`.
- Demais entidades conforme já especificado em `matchpoint_documentacao.md` §6.

### API — Contratos Adicionais

- `GET /api/itens/top?dias=7&limit=6` — produtos mais vendidos no período (alimenta atalhos do lançamento).
- `GET /api/health` — health check.
- `GET /api/backup?formato=json|xlsx` — exportação completa.
- `POST /api/comandas/{id}/reabrir` — reabrir comanda fechada (estorna estoque, gera evento).
- Demais rotas conforme `matchpoint_documentacao.md` §10.

---

## Testing Decisions

### Princípios

- Testes cobrem **comportamento externo observável**, não implementação interna. Um teste não deve quebrar quando um detalhe interno do Service é refatorado, desde que o contrato continue o mesmo.
- Cada Service crítico tem cobertura unitária com Repositories mockados.
- Pelo menos um fluxo end-to-end (HTTP → DB real) cobre o caminho mais crítico do sistema.

### Stack de Testes

- **Pytest** + **httpx** (cliente assíncrono) + **pytest-asyncio**.
- Banco de teste isolado (PostgreSQL local ou container), populado/limpo por fixture.
- Mocks via `unittest.mock` apenas em Repositories (em testes de Service unitários).

### Módulos com Cobertura Obrigatória no MVP

1. **`comanda_service`**
   - Abrir comanda — validação de garçom ativo, identificação não vazia.
   - Lançar item — comanda fechada rejeita, item não-vendável rejeita, snapshot de preço, cortesia → preço 0.
   - Fechar comanda — cálculo de subtotal ignorando cortesias/cancelados, aplicação de desconto (% e valor), validação de soma de pagamentos, transação atômica de fechamento + baixa de estoque, pagamento parcial mantém comanda aberta com saldo deduzido.
   - Reabrir comanda — estorna estoque dos itens não-cancelados, status muda para `reaberta`.
   - Concorrência — UPDATE com `version` antiga retorna 409.

2. **`item_service`**
   - Cadastro de item composto exige ao menos 1 insumo na ficha.
   - Item não-vendável não pode ter preço de venda.
   - Item composto não pode ter outro composto na ficha (pré-roadmap).
   - Cálculo de custo do composto via soma da ficha.

3. **`compra_service`**
   - Custo médio ponderado correto após N compras sequenciais.
   - Reset de custo médio quando estoque anterior ≤ 0.
   - Atualização de saldo do item após registro.

4. **`estoque_service`**
   - Baixa sem venda registra movimento e atualiza saldo.
   - Explosão de ficha técnica em item composto durante baixa de venda.
   - Saldo negativo permitido (não bloqueia).

5. **`relatorio_service`**
   - DRE retorna alerta quando há produto sem custo.
   - Vendas por garçom respeita garçom da abertura.
   - Fechamento de caixa quebra correto por método de pagamento.

### Teste E2E

- Um teste de fluxo completo: login → abrir comanda → lançar 3 itens (1 simples, 1 composto, 1 cortesia) → aplicar desconto → fechar com pagamento misto → verificar comprovante, baixa de estoque (com explosão de ficha) e movimento gravado.

### Testes de Frontend

- **Fora de escopo no MVP** (prazo apertado até 12/05). Validação manual via uso real durante a entrega.
- Pós-MVP: Vitest + React Testing Library cobrindo formulários críticos (Nova Comanda, Fechamento) e lógica de divisão de conta.

### Prior Art

- Não há código prévio neste repositório (greenfield). Convenções serão estabelecidas a partir do primeiro Service implementado (`comanda_service`), que servirá como referência para os demais.

---

## Out of Scope

### Fora do MVP (12/05/2026)

- Atalhos de teclado no caixa.
- Numeração sequencial real de comandas (`#001` é só formatação do `id`).
- Helper desktop para impressão direta na térmica (Obitech WD-80R7).
- Importação de XML de NFe e tela de "de-para" para vincular itens.
- Alertas no dashboard (estoque baixo, comanda antiga, produto sem custo) — DRE tem alerta, mas dashboard não.
- Gestão formal de "comandas perdidas" / abandonadas.
- Configuração técnica direta da impressora.
- Modo offline com sincronização posterior.
- Backup automático em nuvem.
- Multi-usuário com permissões granulares (sócio/caixa/garçom).
- Comandas digitais via palm/tablet do garçom.
- Cupom fiscal (NFCe) — depende de validação com cliente, certificado digital, integração SEFAZ.
- Combos com regras de promoção.
- Ficha técnica aninhada (insumo composto dentro de outro composto).
- Volume como unidade base (ml/L).
- Custo de mão de obra/embalagem na ficha técnica.
- Delivery (iFood, próprio).
- Integração com motoboy.
- Integração com maquininha PagBank.
- Funcionalidades de IA (precificação, predição de demanda).
- App mobile dedicado.
- Multi-loja.
- Testes automatizados de frontend.
- CI/CD via GitHub Actions (deploy manual via Railway CLI no MVP).
- Rate limiting na API.

### Não Considerado em Nenhum Horizonte

- Suporte a viewport < 1280px (mobile responsivo).
- Login social / SSO.

---

## Further Notes

### Premissas de Hospedagem

- Hospedagem em Railway (backend + PostgreSQL) e Vercel (frontend) está **definida como decisão arquitetural**, mas a integração técnica e o setup das contas **ainda não foram realizados** na data deste PRD. Desenvolvimento ocorre localmente até a etapa de deploy.
- Custos estimados (~R$35-40/mês) só passam a incidir quando os serviços forem efetivamente provisionados.
- Backups diários automáticos do Railway, retenção típica de 7 dias no plano Hobby. Restore via dashboard. RPO ~24h, RTO ~10min. Confirmar especificações no momento da contratação.

### Riscos Conhecidos

- **Queda de internet/luz no bar:** risco aceito no MVP. Operação interrompida durante a falha. Versão offline está no roadmap pós-contrato.
- **Concorrência no fechamento de comanda:** mitigada por coluna `version` + 409 + recarga forçada no frontend.
- **Cardápio não enviado a tempo pelo cliente:** follow-up diário; usar cardápio de exemplo se necessário.
- **Prazo apertado (7 dias até 12/05):** priorização rigorosa. Corte de escopo se necessário, sempre preservando o núcleo de comandas + estoque.

### Critérios de Aceite

Documentados em `matchpoint_documentacao.md` §14. Resumo: zero bugs críticos, tempo de resposta <2s por operação, interface operável por "gente mais velha" (testado), todas as ações destrutivas com confirmação, sistema em produção com banco populado pelo cardápio real.

### Cronograma

- **05/05** — Reunião de levantamento (concluído).
- **06/05 → 11/05** — Desenvolvimento (backend + frontend + integração + testes internos).
- **12/05 às 16h00** — Entrega oficial no bar + treinamento (30min) + primeira operação assistida.
- **12/05 → 12/06** — Mês de teste gratuito, ajustes às terças 16h00.
- **12/06** — Definição de plano + assinatura de contrato.

### Documentos Relacionados

- `docs/matchpoint_documentacao.md` — documento mestre (fluxo completo + arquitetura Deep Models + entidades + telas).
