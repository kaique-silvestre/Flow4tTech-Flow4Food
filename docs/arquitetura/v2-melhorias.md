# V2 — Melhorias e Evolução (Flow4Food)

> Documento de arquitetura. Escopo: **melhorias planejadas para a V2**, a serem iniciadas só depois da V1 estável.
> Baseline e pendências da V1 vivem em [`v1-pendencias.md`](./v1-pendencias.md). Esta versão pressupõe que multi-tenancy, billing e auditoria de caixa da V1 já estão em produção.

---

## 1. Permissões dinâmicas: de telas fixas para ações ALLOW/DENY + templates

**Hoje (V1):** perfis fixos hardcoded (Admin/Gerente/Caixa) e permissão por tela, sem DENY explícito (ver §1.5 de `v1-pendencias.md`).

**V2:** catálogo dinâmico de **ações do sistema**, cada perfil definindo ALLOW/DENY por ação via checkbox, e **templates** que aplicam um conjunto de ações de uma vez.

```sql
-- Catálogo de ações (semeado pela plataforma, não pelo cliente)
CREATE TABLE acoes (
    id          BIGSERIAL   PRIMARY KEY,
    codigo      VARCHAR(60) NOT NULL UNIQUE,   -- 'comanda:cancelar_item', 'caixa:fechar'
    grupo       VARCHAR(40) NOT NULL,          -- 'Comandas', 'Caixa', 'Estoque' (agrupa na UI)
    descricao   VARCHAR(200) NOT NULL
);

-- ALLOW/DENY explícito por perfil x ação
CREATE TABLE profile_acoes (
    id          BIGSERIAL   PRIMARY KEY,
    tenant_id   BIGINT      NOT NULL REFERENCES tenants(id),
    profile_id  BIGINT      NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
    acao_id     BIGINT      NOT NULL REFERENCES acoes(id),
    efeito      VARCHAR(5)  NOT NULL CHECK (efeito IN ('allow','deny')),
    UNIQUE (profile_id, acao_id)
);

-- Templates ("Configurações Padrão": Garçom, Gerente, Caixa)
CREATE TABLE permission_templates (
    id          BIGSERIAL   PRIMARY KEY,
    nome        VARCHAR(60) NOT NULL,          -- 'Garçom'
    descricao   VARCHAR(200),
    is_system   BOOLEAN     NOT NULL DEFAULT FALSE  -- templates da plataforma vs. do cliente
);

CREATE TABLE template_acoes (
    template_id BIGINT      NOT NULL REFERENCES permission_templates(id) ON DELETE CASCADE,
    acao_id     BIGINT      NOT NULL REFERENCES acoes(id),
    efeito      VARCHAR(5)  NOT NULL CHECK (efeito IN ('allow','deny')),
    PRIMARY KEY (template_id, acao_id)
);
```

### 1.1 DENY por padrão (deny-by-default)

Estado inicial de qualquer permissão é **negado**. Um perfil ou usuário recém-criado **nasce sem nenhuma ação permitida** — só enxerga o que for explicitamente marcado `allow`. A ausência de registro em `profile_acoes`/`user_acoes` ⇒ negado.

**Resolução de permissão (DENY vence):** ao montar o JWT, resolver as ações aplicáveis — `deny` explícito tem precedência sobre `allow`, e a falta de `allow` também é negação. A lista final de ações permitidas substitui o array `permissions` de telas da V1.

### 1.2 Perfis criados do zero

Novos perfis podem ser criados **totalmente do zero** (não só clonando os padrões). O perfil nasce vazio (tudo negado) e o operador marca as ações `allow` desejadas via checkbox, agrupadas por `acoes.grupo`.

### 1.3 Dois modos de criar usuário

```sql
-- ALLOW/DENY direto no usuário (modo "usuário livre")
CREATE TABLE user_acoes (
    id          BIGSERIAL   PRIMARY KEY,
    tenant_id   BIGINT      NOT NULL REFERENCES tenants(id),
    user_id     BIGINT      NOT NULL REFERENCES system_users(id) ON DELETE CASCADE,
    acao_id     BIGINT      NOT NULL REFERENCES acoes(id),
    efeito      VARCHAR(5)  NOT NULL CHECK (efeito IN ('allow','deny')),
    UNIQUE (user_id, acao_id)
);
```

- **(a) Usuário associado a um perfil:** herda as ações do perfil (Admin, Caixa, etc.). Caminho comum.
- **(b) Usuário livre:** sem perfil (ou sobrepondo o perfil), com ações `allow`/`deny` mapeadas **diretamente nele** via `user_acoes`. Para casos pontuais que não cabem num perfil. Também nasce deny-by-default.

### 1.4 Templates travam edição manual

Quando um perfil **adota um Template**, o template **força um padrão fixo de checkboxes** naquele perfil. Enquanto o template estiver ativo:

- As permissões do perfil ficam **bloqueadas para edição manual** (checkboxes read-only na UI).
- Mudam **apenas** se o template global for atualizado pela plataforma — a alteração propaga para todos os perfis que usam aquele template.
- Para editar manualmente, é preciso **desvincular** o template do perfil (vira perfil custom, aí os checkboxes liberam).

Modela-se com um vínculo no perfil:

```sql
ALTER TABLE profiles ADD COLUMN template_id BIGINT REFERENCES permission_templates(id);
-- template_id NOT NULL ⇒ perfil travado no template; NULL ⇒ perfil custom editável
```

**Aplicar template:** "usar template Garçom no perfil X" = setar `profiles.template_id` e materializar `template_acoes` → `profile_acoes`. UI: tela de checkboxes agrupados por `acoes.grupo`, com seletor "Padrão → [Garçom|Gerente|Caixa|Custom]".

### 1.5 Nova ação entra como DENY global

Se a plataforma criar uma **nova ação** no futuro, ela entra globalmente com estado inicial **DENY** (bloqueada) para **todas as empresas e usuários** — inclusive perfis e templates existentes — até ser **explicitamente liberada**. Garante que um deploy que adiciona funcionalidade nunca conceda acesso retroativo sem decisão consciente (fail-closed).

### 1.6 Migração V1→V2

Mapear cada tela atual para o conjunto de ações equivalente (ex: tela `comandas` → `comanda:lancar_item` + `comanda:editar_item` + ...). Os perfis fixos viram templates de sistema. `require_permission(screen)` é trocado por `require_action(codigo)`.

> Substitui a string mágica `profile.name == "Admin"` (§1.5 de `v1-pendencias.md`) por uma ação não-removível (ex: `sistema:admin_total`) marcada no template Admin.

---

## 2. Painel do Administrador Global (core da V2)

Painel exclusivo dos **donos do SaaS** (não dos clientes): visão de todas as empresas, usuários de cada uma e métricas de uso. Exige um nível de identidade **acima** do tenant.

**Identidade — admin da plataforma é separado de `system_users`** (que é sempre tenant-scoped):

```sql
CREATE TABLE platform_admins (
    id            BIGSERIAL    PRIMARY KEY,
    email         VARCHAR(254) NOT NULL UNIQUE,
    name          VARCHAR(200) NOT NULL,
    password_hash VARCHAR(200) NOT NULL,
    is_active     BOOLEAN      NOT NULL DEFAULT TRUE,
    created_at    TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);
```

> O JWT do platform admin carrega claim `platform_admin: true` e **não** tem `tenant_id`.

### 2.1 Conexão separada com Superuser (BypassRLS)

O painel da Flow4Tech precisa ver dados **consolidados de todas as empresas** — o oposto do isolamento por RLS que protege o app dos clientes. Em vez de tentar contornar as policies de RLS (frágil, fácil de vazar dados do tenant errado), a API do painel usa uma **conexão de banco totalmente separada**, com um role PostgreSQL **Superuser / `BYPASSRLS`**.

- App dos clientes (`/api/*`): role comum, **sem** `BYPASSRLS`, com `SET app.tenant_id` por request (V1).
- Painel admin (`/api/platform/*`): engine/pool **dedicado**, role `BYPASSRLS`, enxerga todos os tenants sem barreira de RLS — nenhum `SET app.tenant_id`.

Duas engines distintas no backend (ex: `engine_app` e `engine_platform`), nunca compartilhando o mesmo role. Isso elimina conflito entre as policies de RLS dos tenants e a visão global dos donos do SaaS.

> 🔒 Como o role do painel ignora RLS, **todo** endpoint `/api/platform/*` precisa de auth de platform admin rigorosa (claim `platform_admin: true`). Um vazamento de auth aqui expõe todos os tenants.

### 2.2 Escopo do painel — a definir pelos criadores

As rotas de **gestão** (listar empresas, ver usuários de cada empresa, ativar/suspender assinatura) seguem o modelo de bloqueio da V1 (suspender/ativar = `UPDATE` na assinatura — §3.3 de `v1-pendencias.md`, propaga no próximo refresh sem editar `system_users`).

Já os **dados, relatórios e gráficos** que o painel vai exibir (métricas, KPIs, dashboards) **ainda não estão definidos** — serão especificados pelos criadores da plataforma conforme as necessidades de negócio da Flow4Tech. Não há, nesta versão, contrato fixo de rotas de métricas.

**Recomendação técnica (quando os requisitos fecharem):** para métricas que varrem tabelas grandes, usar uma tabela de **cache/agregação assíncrona** alimentada por job (snapshot periódico), em vez de calcular on-the-fly a cada request. Esboço:

```sql
-- RECOMENDAÇÃO, não especificação fechada — colunas a definir conforme KPIs reais
CREATE TABLE tenant_metrics_daily (
    tenant_id  BIGINT REFERENCES tenants(id),
    dia        DATE,
    -- ... métricas conforme necessidade de negócio
    PRIMARY KEY (tenant_id, dia)
);
```

---

## 3. Outras melhorias (backlog V2+)

- **Módulo de Planos (precificação e pacotes) — estudo de produto + engenharia, a projetar do zero.** Modelo de cobrança e empacotamento **ainda não definido**. Por isso **não há** nesta documentação modelagem estruturada de planos nem regras rígidas (limites por plano, tiers, etc.). Quando o modelo comercial fechar, projetar do zero: catálogo de planos, limites/quotas, vínculo com `assinaturas` e o fluxo de troca de plano no painel admin. Até lá, billing da V1 opera com assinatura por tenant sem diferenciação de plano.
- **Sub-receita (insumo composto de insumo):** a ficha técnica V1 resolve produto → insumos diretos. V2: insumo que é feito de outros insumos (ex: molho que entra no hambúrguer) — explosão recursiva de ficha técnica.
- **Histórico de auditoria visual:** tela para navegar `eventos_comanda` (a V1 mantém só o registro bruto). Filtros por comanda, usuário, tipo de evento, período.
- **Relatórios avançados de CMV / margem por prato** (depende de `custo_medio` consolidado).
- **Roteamento de impressão por setor, KDS, cardápio QR Code, módulo fiscal (NFC-e/SAT):** explicitamente fora da V1 (ver §6 de `v1-pendencias.md`); reavaliar prioridade na V2+.

---

## 4. Ordem sugerida (V2)

1. Permissões dinâmicas ALLOW/DENY + templates (§1) — migra o RBAC por tela para ações.
2. Painel Admin Global (§2) — depende de multi-tenancy e billing da V1 já estáveis.
3. Backlog incremental (§3) conforme demanda de mercado.

> Pré-requisito: V1 (multi-tenancy + billing + auditoria de caixa) em produção e estável.
