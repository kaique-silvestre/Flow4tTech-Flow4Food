# Auditoria Matchpoint — Handoff pra continuação

> Documento de transferência de contexto para outra LLM/agente continuar o trabalho de correção dos achados da auditoria de segurança/arquitetura do repositório. Escrito em 2026-09-02 pelo Claude (Sonnet 5) após 5 "lotes" de correções já commitados e enviados.

## 1. Contexto — o que é isso

Em 2026-08-25 foi feita uma auditoria completa do monorepo Matchpoint (Flow4Food): 11 módulos × 6 eixos (multi-tenancy/RLS, segurança/auth, sistema de erros, arquitetura, observabilidade, performance/resiliência), via subagentes especializados. O relatório completo está publicado como Artifact privado do usuário: **"Auditoria Matchpoint"**, título exato, buscável via `Artifact({action:"list"})` — não peça a URL ao usuário, ela muda; liste os artifacts e ache pelo título. Se não tiver acesso à tool `Artifact`, peça ao usuário pra colar o conteúdo ou re-gerar a lista de achados restantes (seção 4 deste documento já tem tudo o que falta, então na prática você não precisa reabrir o artifact pra continuar).

O relatório encontrou ~57 achados CRÍTICO+ALTO e dezenas de MÉDIO/BAIXO, distribuídos assim (ranking por Crítico+Alto):

| Módulo | Crítico | Alto |
|---|---|---|
| core/database + RLS + multi-tenant | 2 | 6 |
| relatórios financeiros / CMV + dashboard | 1 | 6 |
| platform_admin | 2 | 5 |
| caixa | 0 | 5 |
| nfe + compras | 0 | 5 |
| frontend platform + auth guards | 0 | 5 |
| estoque + insumos + ficha técnica | 1 | 3 |
| comandas | 2 | 2 |
| comissões de garçom | 0 | 4 |
| core/ restante (middleware, scheduler, sentry, errors) | 1 | 3 |
| frontend operacional (comandas/estoque/caixa/cardápio) | 2 | 2 |

## 2. O que já foi feito (5 lotes, 17 fixes, tudo commitado e pusheado)

Branch: `development`. Todos os commits abaixo já estão no remoto (`git push origin development` já executado, HEAD em `1ab0e5f` no momento da escrita deste doc — confira `git log --oneline -10` pra ver se algo mais foi commitado depois).

```
1ab0e5f fix(garcons,compras,db): audita comissão de garçom e compras, corrige unique constraint per-tenant, corrige migration 0085
2c8e3ad fix(admin,rate-limit,frontend): endurece SUPERADMIN_TOKEN, adiciona rate limit em rotas críticas, corrige frontend de comandas/caixa
8529af6 fix(comandas,relatorios,nfe): lock otimista + N+1 em comandas/CMV/match NFe
3df8eb6 fix(core,estoque,caixa): corrige vazamento de contexto entre tenants, audita baixa de estoque, trava fechamento de caixa concorrente
4ddaf0d fix(errors,nfe,db): preserva payload estruturado de erro, bloqueia billion laughs, adiciona índices de relatório
```

Detalhe do que cada commit resolveu (todos com testes passando, mypy limpo, suíte completa validada antes de cada commit):

- **`4ddaf0d`**: `core/errors.py` preserva payload estruturado de `HTTPException` dict (`SUBSCRIPTION_BLOCKED` não vira mais `str()` cru), mapeia 403/409 pra `ErrorCode` correto, adiciona `sentry_sdk.capture_exception` explícito no handler 500, adiciona handler pra `RequestValidationError` (422) com envelope padrão. `nfe_parser.py` troca `xml.etree.ElementTree` por `defusedxml` (billion laughs DoS). Migration 0089: índices compostos `(tenant_id, col)` em comandas/pagamentos/movimentos_estoque/insumos/compras/itens_compra.
- **`3df8eb6`**: `_tenant_ctx` (contexto de tenant) trocado de `threading.local()` pra `contextvars.ContextVar` — o achado mais crítico da auditoria inteira, risco real de leitura/escrita cruzada entre tenants confirmado com teste de concorrência (reproduzido 3/3 antes do fix, corrigido 5/5 depois). `get_tenant_db` virou `async def` (necessário — generator síncrono não propaga `ContextVar` entre as chamadas do threadpool do anyio). `MovimentoEstoque` ganhou `user_id` (migration 0090) + auditoria em baixa manual/CRUD de insumos. Fechamento de caixa ganhou lock via `UPDATE` condicional atômico (`WHERE status='aberta'`), `ErrorCode.CAIXA_JA_FECHADO` (409).
- **`8529af6`**: `fechar_comanda`/`reabrir_comanda`/`patch_comanda` ganharam optimistic locking (`version` obrigatório — **breaking change de contrato de API**, corrigido no frontend no lote seguinte). N+1 na listagem de comandas (~300→7 queries). Auditoria em fechar/cancelar comanda. N+1 em `calcular_custo_produto`/CMV (41→2 queries), código morto removido. N+1 no match de NFe (100→1 query), truncamento em 2000 insumos removido.
- **`2c8e3ad`**: Frontend atualizado pro novo contrato de `version` (desconto/fechar/reabrir/patch de comanda) + tratamento de `isError` explícito em 6 páginas (CaixaPage era o mais crítico — falha de rede era tratada como "caixa fechado", risco de reabertura indevida). `admin.py` (SUPERADMIN_TOKEN legado): `hmac.compare_digest`, auditoria com `X-Admin-Identifier` obrigatório, rate limit 3/15min. Rate limiting adicionado em: login platform admin (5/15min), mutações admin (10/min), caixa (30-60/min), toggle/delete comissão (30/min), upload NFe (10/min), relatórios/dashboard (60/min).
- **`1ab0e5f`**: Auditoria em `toggle_pago_comissao`/`delete_comissao` (com snapshot do valor removido antes de apagar), bound checking (`ge=0`) em `ComissaoUpdateRequest.valor`, `CheckConstraint` no banco pra `percentual` (0-100). `garcons.nome` migrado pra unique constraint per-tenant (migration 0091, mesmo padrão da 0082). Auditoria em `criar_compra`/`confirmar_recebimento`/`cancelar_compra`, warning explícito (`compra_item_insumo_ausente`) no descarte silencioso de item sem insumo. Bug pré-existente na migration 0085 corrigido (tentava recriar índice que a 0044 já cria, quebrava `alembic upgrade head` em banco vazio).

### Decisões humanas pendentes (não foram implementadas de propósito — risco/ambiguidade real)

1. **`admin.py` roda sob `get_db` (RLS `ENABLE`, não `FORCE`)**, bypassando RLS por completo pro superadmin. Investigado no lote 4: migrar pra `get_platform_db` ou pra `FORCE ROW LEVEL SECURITY` nas tabelas `tenants`/`assinaturas` arrisca quebrar `tenant_service.criar_tenant` (que clona perfis-seed cross-tenant relying no bypass de RLS via role de owner do banco). **Não mexer sem decisão humana explícita** — ver `admin.py` e `tenant_repository.clone_profiles_from_seed`.
2. **Redis pro rate limiter**: hoje usa `MemoryStorage` (SlowAPI). Confirmado que o deploy (Railway) é single-instance (`railway.toml`/`railway.staging.toml` sem config de réplica) — não é prioridade migrar. Se o deploy virar multi-instância no futuro, revisitar `core/limiter.py`.
3. **Proxy headers (`X-Forwarded-For`)**: rate limit hoje usa `get_remote_address` sem configurar proxy confiável — atrás do Railway, pode colapsar rate limit de todos tenants numa única chave (ou permitir spoofing se configurado errado). Não resolvido — precisa confirmar a config de rede do Railway antes de mexer.
4. **`scheduler.py` não popula `_tenant_ctx`** (só faz `SET ROLE` direto). Hoje seguro porque nenhum job comita no meio do loop por tenant — risco late nte se isso mudar no futuro. Não mexido, só documentado.

### Onda 6 concluída em 2026-09-02

Commit local: `51cf84a fix(platform): unifica provisioning e audita mutações JWT` (não enviado ao remoto).

- Unifica a criação JWT de tenant com `tenant_service.criar_tenant`, incluindo perfis clonados, usuário administrador owner e assinatura trial; o formulário da plataforma agora coleta as credenciais iniciais do administrador.
- Adiciona auditoria às mutações JWT de plataforma e à criação de announcements, sem registrar senha crua.
- Adiciona processor estruturado para redigir CPF, senhas, tokens e outras credenciais antes da renderização dos logs.
- Validação integrada: `365 passed, 4 skipped`; type-check, lint e build do frontend passaram. Mypy mantém três erros preexistentes de incompatibilidade de middleware em `src/main.py` com as versões resolvidas neste ambiente.

Próxima prioridade: Onda 7 da seção 5.

## 3. Como o trabalho foi organizado (pra você replicar)

Fluxo usado nos 5 lotes anteriores — **replique este padrão**:

1. **Escolha 2-3 achados independentes** (arquivos que não se sobrepõem entre si) pra rodar em paralelo. **Nunca mais que 3 subagentes simultâneos** — mais que isso aumenta risco de dois agentes editarem o mesmo arquivo ao mesmo tempo (já aconteceu de forma inofensiva, mas é sorte, não garantia) e também estressa o rate-limit da sessão (um lote de 3 tickets grandes já esgotou o limite de sessão uma vez).
2. **Cada ticket vira um prompt rico pra um subagente `implementer`** (ou equivalente `TDD`-capable no seu ambiente), com: contexto do achado (severidade, local exato — arquivo:linha —, descrição, recomendação, todos copiados literalmente do relatório da auditoria ou deste documento), instrução explícita de **TDD** (ler arquivo inteiro antes de editar, escrever teste que falha, implementar, rodar suíte inteira + mypy/type-check, self-review), instrução de **NÃO commitar** e **NÃO editar CHANGELOG.md** (isso fica com você, o orquestrador, no final do lote), e a lista de arquivos que outros agentes do mesmo lote estão tocando (pra evitar conflito).
3. **Depois que os 3 terminam**: rode a suíte completa (`pytest -q` + `mypy src/` no backend; `npm run type-check && npm run lint && npm run build` no frontend) você mesmo, no diretório principal — não confie cegamente no que cada agente reportou isoladamente, porque pode ter havido interação entre os arquivos que cada um só viu depois que o outro terminou.
4. **Se algum agente falhar/ficar incompleto** (aconteceu no lote 5 por rate-limit de sessão): NÃO commite. Verifique `git status`/`git diff` pra ver o que sobrou. Complete manualmente ou relance um ticket mais estreito focado só no que faltou. Rode a suíte antes de decidir.
5. **Escreva as entradas do `CHANGELOG.md`** (seção `## [Unreleased]` → `### Fixed`, formato documentado em `AGENTS.md` — descrição objetiva + autor real via `git config user.name`/`user.email` + data) e **commit** você mesmo, com mensagem cobrindo todos os fixes do lote, terminando com a atribuição de commit que seu ambiente exigir.
6. **Push** pro branch `development` (ou o branch em que você estiver) só quando o usuário pedir explicitamente — nas rodadas anteriores só foi feito push quando pedido.

### Gotchas descobertos (evite redescobrir do zero)

- **Testes em SQLite**: `backend/tests/conftest.py` já faz um patch global no `server_default` de qualquer coluna `tenant_id` (troca `current_setting('app.tenant_id')`, específico de Postgres, por literal `1`) — então não precisa se preocupar com isso em teste novo. MAS colunas com `server_default=sa.text("now()")` (SQL raw Postgres, ex: `ComissaoGarcom.created_at`) **não são patcheadas** e quebram em SQLite (`unknown function: now()`) — se seu teste precisa inserir uma linha nessa tabela diretamente (não via endpoint que já popula o campo em Python), passe `created_at=datetime.now(timezone.utc)` explicitamente no construtor.
- **Numeração de migration**: sempre confira o número mais alto existente em `backend/alembic/versions/` ANTES de nomear uma nova migration — com múltiplos agentes em paralelo, dois podem tentar criar a mesma migration `009X` ao mesmo tempo. No momento da escrita deste doc, a última é `0091`.
- **`get_tenant_db` é `async def`** desde o fix de contextvars (lote 2) — se você (ou um subagente) for tocar em `backend/src/api/dependencies.py` de novo, tenha isso em mente; não reverta pra sync sem entender por quê (está documentado no docstring da função).
- **Rate limit em rotas que usam `Depends`**: no `admin.py`, `require_superadmin`/`get_admin_identifier` foram deliberadamente tirados de `Depends(...)` e viraram chamadas explícitas no corpo da função — porque com `Depends`, FastAPI rejeita token inválido durante a resolução de dependências, ANTES do decorator `@limiter.limit` rodar, então tentativas de força bruta nunca seriam contadas pelo rate limit. Se for adicionar rate limit em outras rotas que dependem de auth via `Depends`, verifique se esse mesmo problema se aplica.
- **`audit_service.log_background`** é a função usada em toda rota que dispara auditoria assíncrona via `BackgroundTasks.add_task(...)`; em teste, precisa de `monkeypatch.setattr(audit_service, "log_background", <versão síncrona>)` porque `BackgroundTasks` do FastAPI/Starlette só executa a task depois da resposta ser enviada — sem isso o teste verifica o banco antes do log existir. Veja o padrão em `backend/tests/test_compras.py::_log_background_sync` e replique.
- **CHANGELOG.md**: autor é sempre o humano (`Kaique Gonzaga Silvestre <kaique.silvestre.22@gmail.com>`, confirmado via `git config` no repo), nunca o nome do agente/LLM. Formato exato em `AGENTS.md`.

## 4. O que falta — backlog completo, priorizado

### 4.1 CRÍTICO/ALTO ainda não resolvidos (prioridade máxima)

**[CRÍTICO] Duas superfícies admin paralelas com efeitos divergentes** (módulo platform_admin)
Local: `backend/src/api/routes/admin.py` (SUPERADMIN_TOKEN) vs `backend/src/api/routes/platform_auth.py` (JWT). Tenant criado via `/api/platform` fica **sem perfis nem usuário admin clonados** — login quebrado pra tenants criados por esse caminho. `admin.py:46-116`, `platform_auth.py:354-456`, `platform_repository.py:85-130` vs `tenant_service.py:50-100`.
Recomendação da auditoria: unificar os dois caminhos de criação de tenant, ou garantir que ambos cheguem no mesmo `tenant_service.criar_tenant` (que já faz a clonagem correta). **Ticket denso — envolve entender bem os dois fluxos antes de mexer, cuidado com a decisão pendente #1 da seção 2 (RLS de admin.py) que é adjacente a esse código.**

**[ALTO] Diversas ações via JWT (platform_auth) sem auditoria**
Local: `platform_auth.py`, `platform_announcements.py`. Criação/edição de usuário de tenant (inclusive troca de senha), alteração de permissões de perfil, features por tenant, configs globais, criação de announcements — nenhuma dessas rotas chama `audit_service`. Só as rotas de `admin.py` e comissões/compras foram cobertas nos lotes anteriores. Aplique o mesmo padrão `audit_service.log_background` já usado em `garcons.py`/`compras.py`/`caixa.py`.

**[ALTO] N+1 em platform_admin: listagem de tenants e de perfis**
Local: `tenant_service.py:168-174` (query de assinatura por tenant em loop, quando `platform_repository.list_tenants` já faz LEFT JOIN corretamente — parece um bug reintroduzido, vale investigar se o LEFT JOIN não está sendo usado onde deveria). `platform_repository.py:483-504` (2 queries extras por perfil no loop ao listar perfis de um tenant).

**[ALTO] Query de cockpit não sargable, sem paginação**
Local: `platform_repository.py:165-198`. 5 subqueries correlacionadas usando `DATE_TRUNC` no predicado (invalida índice), sem paginação nenhuma.

**[ALTO] Frontend platform — 4 achados**
Local: `frontend/src/features/platform/`.
1. Refresh de token durante impersonation troca contexto silenciosamente pro token do admin da plataforma (`api.ts:37-73`) — requisição sob sessão impersonada com 401 chama refresh via cookie do "dono" da aba e sobrescreve o token ativo.
2. `usePlatformApi.ts:8-17` hard-redireciona em qualquer 401 sem tentar refresh (diferente do client principal `lib/api.ts`, que tenta refresh antes de deslogar).
3. Erros de ações administrativas críticas (alterar assinatura, criar tenant, impersonar) nunca chegam ao Sentry — `platformApi` sem interceptor de 5xx (`usePlatformApi.ts:7-17`).
4. Token de impersonation (JWT) trafega em texto claro na URL antes de ir pro `sessionStorage` — exposto em histórico/logs de proxy. `PlatformTenantDetailPage.tsx:369-381`, `App.tsx:63-79`.
5. Listagem de tenants e cockpit sem paginação — dataset completo carregado de uma vez, sort client-side. `usePlatformApi.ts:125-137,463-475`.

**[ALTO] Módulo relatórios: 3 achados de performance ainda abertos**
1. N+1 de fornecedor no dashboard (compras agendadas) — `dashboard_service.py:60-82`.
2. `historico-comandas` sem paginação nem teto de intervalo — pode carregar todo histórico do tenant numa resposta. `relatorios.py:39-48`, `relatorio_repository.py:103-119`.
3. `AppError`/`ErrorCode` nunca usado no módulo relatórios inteiro — todo erro de validação/negócio vira 500 genérico. Isso inclui `mes`/`ano` malformado em `/relatorios/dre` e `/dashboard/resumo-anual` virando 500 cru (parsing manual com `int()`/`datetime.date()` sem try/except — **não é coberto pelo handler de `RequestValidationError` já adicionado**, porque não é erro de validação Pydantic, é exceção manual dentro do código da rota).

**[ALTO] Sem processor de redação de PII no structlog**
Local: `backend/src/core/logging.py:18-24`. Se algum service passar senha/CPF/token como kwarg de log, vaza em texto puro. Adicionar um processor structlog que redige chaves sensíveis (`senha`, `password`, `cpf`, `token`, etc.) antes de qualquer render.

### 4.2 MÉDIO/BAIXO — backlog por módulo (menos urgente, mas ainda achados reais da auditoria)

Agrupado por módulo. Todos com local exato no relatório original — se precisar do texto completo de algum, o relatório está no Artifact "Auditoria Matchpoint" (seção 1 deste doc).

**core/database + dependencies + scheduler**: SET ROLE sem log nenhum (falha silenciosa de RLS não rastreável); `tenant_id` nunca bindado ao `structlog`; connection pool sem `pool_size`/`max_overflow`/`pool_timeout` explícitos; scheduler compartilha pool com tráfego web; `contextlib.suppress(Exception)` mascara falha de RLS em `tenant_repository.py:45-58`; `increment_version` sem predicado `tenant_id` (defesa em profundidade); `tenant_features` sem RLS; lógica de bloqueio de assinatura devia estar em `services/billing_service.py`, não em `dependencies.py`; `get_assinatura_by_tenant` triplicado; `require_active_subscription` morto; nível de log fixo INFO; Sentry sem `before_send`/breadcrumb; scheduler sem heartbeat/listener `EVENT_JOB_ERROR`; lógica de SET ROLE/RESET triplicada sem helper compartilhado (database.py/dependencies.py/scheduler.py).

**estoque/insumos**: `tenant_id` explícito ausente nas queries (defesa em profundidade); rate limit em baixa-sem-venda; `quantidade_caixa`/`nivel_critico` sem `ge=0`; saldo negativo sem bloqueio/confirmação; datas malformadas em query params viram 500; "estoque insuficiente" sem `ErrorCode` dedicado; `calcular_custo` no repository devia estar no service; `get_historico_produtos` monta query ORM direto na service; fórmula "estoque disponível" duplicada em 5 lugares; ordem de lock não determinística em `ajustar_estoque_ficha_tecnica` (falta `ORDER BY insumo_id`, risco de deadlock).

**caixa**: `structlog` ausente em todo o fluxo; divergência de fechamento não gera alerta/log de warning; audit log via `BackgroundTask` pode se perder silenciosamente (sem retry/dead-letter); `Decimal` sem `max_digits`/`decimal_places` no schema; `contas_pagar_service` acessa `caixa_repository` direto, pulando `caixa_service`.

**comandas**: `structlog` usado só 1x em 700+ linhas do service; `abrir`/`patch`/`lançar`/`editar item` sem `audit_service` (só `fechar`/`cancelar` foram cobertos); `ErrorCode.NOT_FOUND` usado incorretamente pra conflito de estado; parsing de data feito na route em vez do service; taxa de serviço/comissão (10%) hardcoded em 2 lugares sem constante nomeada; `logger.warning` loga `pessoas_json` bruto (pode conter nome de cliente).

**comissões de garçom**: `get_garcom_stats` não valida existência do garçom (retorna 200 com zeros em vez de 404); TOCTOU em `update_comissao` (sem `FOR UPDATE`); query duplicada em `update_comissao`; `tenant_id`/`user_id` não bindados no structlog.

**nfe/compras**: validação de tipo de arquivo só por extensão `.xml` (contornável, sem magic-bytes check); fórmula de custo médio ponderado duplicada dentro do próprio `compras_service.py`; parser síncrono sem timeout/isolamento sob upload concorrente.

**relatórios/dashboard**: agregações anuais/mensais carregam todas as linhas em Python em vez de `GROUP BY` no SQL; padrão "buscar linhas + agrupar em Python" repetido 5x em `dashboard_repository.py`; sem validação `data_inicio > data_fim` nem teto de amplitude.

**platform_admin**: `IntegrityError` não traduzido em criação de tenant/usuário (CNPJ/email duplicado vira 500); maioria das rotas usa `HTTPException` cru em vez de `AppError`; `_decode_platform_admin_id` engole exceção sem log; `get_db`/`get_platform_db` sem rollback explícito em exceção; `profile_id` não validado contra `tenant_id` ao criar/atualizar usuário via platform admin (risco de vazamento de permissões entre tenants); `announcements.py` (tenant-facing) usa `get_platform_db` sem RLS, isolamento só em Python; `platform_engine` sem `pool_size`/`max_overflow`; timing side-channel de enumeração de e-mail no login (bcrypt só roda se admin existe).

**frontend operacional (comandas/estoque/caixa/cardápio)**: token JWT em `localStorage` (exposto a XSS); cache TanStack Query não limpo no logout/login (vazamento entre usuários em PDV compartilhado); schema Zod de desconto não espelha limite 0-100 do backend; tratamento de erro de API reimplementado inconsistente por hook; taxa de serviço 10% hardcoded em frontend E backend (3 lugares); cálculo de totais/desconto replicado no componente UI sem hook testável; `formatCurrency` duplicado; tick de relógio 1s em `ComandasPage`/`ComandaAbertaPage` força re-render completo sem memoização.

**frontend platform**: decode de JWT duplicado entre `authStore`/`platformAuthStore`; constantes de status de assinatura duplicadas em 3 páginas; lógica de "quando atualizar assinatura junto com tenant" no componente em vez de hook; `RequireAuth`/`RequirePlatformAuth` com estrutura duplicada; `baseURL` do axios configurado mas nunca usado; `authHeaders()` chamado manualmente em vez de interceptor; suspender/reativar assinatura sem `ConfirmDialog`; tabelas grandes sem `React.memo`.

## 5. Como continuar — instruções pro próximo agente

1. Leia este documento inteiro antes de tocar em qualquer código.
2. Rode `cd backend && source .venv/bin/activate && python -m pytest -q && python -m mypy src/` e `cd frontend && npm run type-check && npm run lint` pra confirmar que o estado atual (pós lote 5) está mesmo verde antes de começar — não assuma.
3. Monte "ondas" (lotes) de até **3 tickets em paralelo**, escolhendo achados que não tocam nos mesmos arquivos. Sugestão de ordem pelas próximas ondas, seguindo a seção 4.1 (prioridade CRÍTICO/ALTO primeiro):
   - **Onda 6**: (a) duas superfícies admin — CRÍTICO, ticket denso, considere rodar sozinho sem paralelismo dado o risco; (b) auditoria em `platform_auth.py`/`platform_announcements.py`; (c) processor de redação de PII no structlog (isolado, `core/logging.py`).
   - **Onda 7**: (a) N+1 platform_admin (list tenants/perfis) + cockpit paginação/sargable; (b) N+1 fornecedor dashboard + paginação historico-comandas; (c) `AppError`/`ErrorCode` no módulo relatórios (mes/ano malformado).
   - **Onda 8**: frontend platform — os 5 achados ALTO (impersonation token na URL, refresh silencioso, 401 hard redirect, Sentry interceptor, paginação tenants/cockpit). Pode valer separar em 2-3 tickets já que são vários arquivos do mesmo módulo frontend.
   - **Ondas seguintes**: trabalhar a lista MÉDIO/BAIXO da seção 4.2, agrupando por módulo (cada módulo = ~1 ticket, já que tende a ser o mesmo conjunto de arquivos).
4. Cada ticket: TDD completo (teste que falha → implementa → verde), rodar suíte + type-check antes de reportar como pronto, **não commitar** (você, orquestrador, commita no final da onda depois de validar tudo junto).
5. Escrever `CHANGELOG.md` (formato em `AGENTS.md`) e commitar ao final de cada onda, com mensagem cobrindo os fixes daquela onda.
6. Dar push só quando o usuário pedir.
7. Manter uma lista de "feito"/"restante" igual a este documento e atualizá-la (ou pedir pra registrar como comentário/memória) conforme avança, pra a próxima transferência de contexto ser tão rica quanto esta.
